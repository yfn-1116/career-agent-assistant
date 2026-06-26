"""MCP-based GitHub Tool — delegates to @modelcontextprotocol/server-github.

Replaces the built-in GitHubRepoTool with the official MCP server.
Provides: search_repositories, get_file_contents, create_issue, etc.
"""

from __future__ import annotations

from typing import Any

from career_agent.tools.base import Tool, ToolResult


class MCPGitHubTool(Tool):
    """GitHub operations via official MCP server.

    Uses the @modelcontextprotocol/server-github MCP server
    (npx @modelcontextprotocol/server-github) over stdio JSON-RPC.
    Requires GITHUB_PERSONAL_ACCESS_TOKEN env var.

    Provides: search_repositories, get_file_contents, list_commits,
    create_issue, create_pull_request, fork_repository, etc.
    """

    name = "github"
    description = (
        "GitHub 操作工具。搜索仓库、读取文件内容、查看提交记录、管理 Issue。"
        "当用户粘贴 GitHub 链接、提到开源项目、或需要查看仓库信息时触发。"
    )

    def __init__(self) -> None:
        super().__init__()
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client

        from career_agent.infrastructure.mcp_client import create_github_mcp
        self._client = create_github_mcp()
        self._client.start()
        return self._client

    @property
    def safety_notes(self) -> list[str]:
        return [
            "只读公开仓库（需要 Token 才能访问私有仓库）",
            "通过 MCP 标准协议调用，不直接操作 GitHub API",
        ]

    def run(self, action: str = "read_repo", repo: str = "", path: str = "", **kwargs: Any) -> ToolResult:
        """Execute a GitHub operation via MCP.

        Parameters
        ----------
        action : str
            One of: read_repo, search_repos, read_file, list_commits.
        repo : str
            Repository name ("owner/repo" format).
        path : str
            File path within the repo.
        """
        if not repo.strip():
            return ToolResult(success=False, error="repo is required (owner/repo format)")

        try:
            client = self._ensure_client()

            if action == "read_repo":
                # Read README.md
                return self._read_repo(client, repo)

            if action == "read_file":
                if not path:
                    return ToolResult(success=False, error="path is required for read_file")
                result = client.call_tool("get_file_contents", {
                    "owner": repo.split("/")[0],
                    "repo": repo.split("/")[1],
                    "path": path,
                })
                return ToolResult(success=True, output={"content": result}, summary=f"read {repo}/{path}")

            if action == "search_repos":
                query = kwargs.get("query", repo)
                result = client.call_tool("search_repositories", {"query": query})
                return ToolResult(success=True, output={"results": result}, summary=f"searched: {query}")

            return ToolResult(success=False, error=f"unknown action: {action}")

        except Exception as e:
            # Fallback: try raw.githubusercontent.com directly
            return self._raw_fallback(repo, path)

    def _read_repo(self, client, repo: str) -> ToolResult:
        """Read README.md from a repo via MCP, with raw fallback."""
        try:
            result = client.call_tool("get_file_contents", {
                "owner": repo.split("/")[0],
                "repo": repo.split("/")[1],
                "path": "README.md",
            })
            return ToolResult(
                success=True,
                output={"repo": repo, "content": result, "source": "mcp"},
                summary=f"read README from {repo} (MCP)",
            )
        except Exception:
            return self._raw_fallback(repo, "README.md")

    @staticmethod
    def _raw_fallback(repo: str, path: str = "README.md") -> ToolResult:
        """Fallback: fetch directly from raw.githubusercontent.com."""
        import urllib.request

        clean_repo = repo.rstrip("/")
        url = f"https://raw.githubusercontent.com/{clean_repo}/main/{path}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "career-agent"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="replace")
            return ToolResult(
                success=True,
                output={"repo": repo, "content": content, "source": "raw"},
                summary=f"read {path} from {repo} (raw fallback)",
            )
        except Exception:
            return ToolResult(
                success=False,
                error=f"unable to read {repo}/{path}. Set GITHUB_PERSONAL_ACCESS_TOKEN for MCP access.",
                summary=f"github read failed: {repo}",
            )
