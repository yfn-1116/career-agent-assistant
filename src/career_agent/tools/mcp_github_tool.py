"""GitHub Tool — direct REST API + raw fallback (no MCP subprocess overhead).

Replaces the MCP-based approach with direct HTTP calls:
- raw.githubusercontent.com for file content (no auth needed for public repos)
- api.github.com for search and metadata
- No npx subprocess, no JSON-RPC, ~1s response instead of 10-30s
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Any

from career_agent.tools.base import Tool, ToolResult


class MCPGitHubTool(Tool):
    """GitHub operations via direct REST API — fast, no MCP overhead.

    Reads public repos via raw.githubusercontent.com.
    Searches via api.github.com.
    """

    name = "github"
    description = (
        "GitHub 工具（直接 HTTP 访问，秒级响应）。操作："
        "read_repo(读取仓库README) "
        "list_user_repos(列出用户的所有公开仓库) "
        "search_repos(搜索仓库) "
        "read_file(读取仓库中的文件)。"
        "参数: action=操作名, repo=仓库(owner/repo格式), username=用户名, path=文件路径"
    )

    def __init__(self) -> None:
        super().__init__()
        self._token: str = ""

    def _get_token(self) -> str:
        if self._token:
            return self._token
        import os
        self._token = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""))
        return self._token

    @property
    def safety_notes(self) -> list[str]:
        return [
            "只读公开仓库",
            "直接 HTTP 访问 GitHub，不启动外部进程",
        ]

    # -- main entry ----------------------------------------------------------

    def run(self, action: str = "read_repo", repo: str = "", path: str = "",
            username: str = "", **kwargs: Any) -> ToolResult:
        try:
            if action == "list_user_repos":
                user = username or kwargs.get("user", repo.split("/")[0] if "/" not in repo else "")
                if not user:
                    return ToolResult(success=False, error="username is required for list_user_repos")
                return self._list_user_repos(user)

            if action == "search_repos":
                query = kwargs.get("query", repo or "")
                if not query:
                    return ToolResult(success=False, error="query is required for search_repos")
                return self._search_repos(query)

            if action == "read_repo":
                repo = repo or kwargs.get("repo", "")
                # If repo is just a username (no slash), list their repos instead
                if repo and "/" not in repo:
                    return self._list_user_repos(repo)
                if not repo:
                    return ToolResult(success=False, error="repo is required (owner/repo format)")
                return self._read_repo(repo)

            if action == "read_file":
                repo = repo or kwargs.get("repo", "")
                path = path or kwargs.get("path", "")
                if not repo or "/" not in repo:
                    return ToolResult(success=False, error="repo is required (owner/repo format)")
                if not path:
                    return ToolResult(success=False, error="path is required for read_file")
                return self._read_raw(repo, path)

            # Unknown action — try read_repo
            if repo and "/" in repo:
                return self._read_repo(repo)
            return ToolResult(success=False, error=f"unknown action: {action}")

        except Exception as e:
            return ToolResult(success=False, error=f"github error: {e}")

    # -- actions -------------------------------------------------------------

    def _list_user_repos(self, username: str) -> ToolResult:
        """List public repos for a user via GitHub API."""
        url = f"https://api.github.com/users/{username}/repos?per_page=30&sort=updated"
        data = self._api_get(url)
        if not data:
            return ToolResult(success=False, error=f"unable to list repos for {username}")

        repos = json.loads(data) if isinstance(data, str) else data
        summary_lines = []
        for r in repos[:15]:
            name = r.get("name", "")
            desc = (r.get("description") or "")[:80]
            lang = r.get("language") or ""
            stars = r.get("stargazers_count", 0)
            summary_lines.append(f"- {name} ({lang}, {stars}⭐): {desc}")

        return ToolResult(
            success=True,
            output={"repo_count": len(repos), "repos": summary_lines},
            summary=f"{username} 有 {len(repos)} 个公开仓库:\n" + "\n".join(summary_lines),
        )

    def _search_repos(self, query: str) -> ToolResult:
        """Search GitHub repositories."""
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&per_page=10"
        data = self._api_get(url)
        if not data:
            return ToolResult(success=False, error=f"search failed for: {query}")

        result = json.loads(data) if isinstance(data, str) else data
        items = result.get("items", [])[:10]
        lines = []
        for r in items:
            lines.append(f"- {r['full_name']} ({r.get('language','')}, {r.get('stargazers_count',0)}⭐): {(r.get('description') or '')[:80]}")
        return ToolResult(
            success=True,
            output={"total": result.get("total_count", 0), "items": lines},
            summary=f"搜索 '{query}' 找到 {result.get('total_count', 0)} 个仓库:\n" + "\n".join(lines),
        )

    def _read_repo(self, repo: str) -> ToolResult:
        """Read README from a repo via raw.githubusercontent.com."""
        # Try main branch first, then master
        for branch in ("main", "master"):
            result = self._read_raw(repo, "README.md", branch)
            if result.success:
                return result
        return ToolResult(success=False, error=f"unable to read README from {repo}")

    def _read_raw(self, repo: str, path: str, branch: str = "main") -> ToolResult:
        """Read a file from raw.githubusercontent.com."""
        clean_repo = repo.rstrip("/")
        url = f"https://raw.githubusercontent.com/{clean_repo}/{branch}/{path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "career-agent"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            return ToolResult(
                success=True,
                output={"repo": repo, "path": path, "content": content, "branch": branch},
                summary=content[:1500],
            )
        except urllib.error.HTTPError as e:
            return ToolResult(success=False, error=f"HTTP {e.code}: {url}")
        except Exception as e:
            return ToolResult(success=False, error=f"read failed: {e}")

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _api_get(url: str) -> str | None:
        """GET request to GitHub API, with optional token."""
        headers = {"User-Agent": "career-agent", "Accept": "application/vnd.github.v3+json"}
        import os
        token = os.getenv("GITHUB_TOKEN", os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", ""))
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None
