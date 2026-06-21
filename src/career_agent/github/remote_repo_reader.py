"""GitHub remote repo reader — reads README + docs via GitHub API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from career_agent.rag.schemas import ProfileDocument


class GitHubRemoteReader:
    """Read public GitHub repos: README.md, docs/*.md, project structure.

    Uses GitHub API.  Optional ``GITHUB_TOKEN`` env var for higher rate limits.

    Usage::

        reader = GitHubRemoteReader()
        docs = reader.read_repo("yfn-1116/career-agent-assistant")
        for doc in docs:
            pipeline.index([doc])
    """

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self._base = "https://api.github.com"

    def read_repo(self, repo_full_name: str) -> list[ProfileDocument]:
        """Read README.md and docs/*.md from a public repo.

        Args:
            repo_full_name: e.g. ``"langchain-ai/langgraph"``
        """
        owner, repo = repo_full_name.split("/", 1)
        docs: list[ProfileDocument] = []

        # 1. README
        readme = self._get_readme(owner, repo)
        if readme:
            docs.append(readme)

        # 2. docs/ directory listing
        doc_files = self._list_docs(owner, repo)
        for f in doc_files[:5]:  # limit to 5 doc files
            content = self._get_file(owner, repo, f["path"])
            if content:
                docs.append(self._to_document(f["path"], content, repo_full_name))

        # 3. Repo metadata
        meta = self._get_repo_meta(owner, repo)
        if meta:
            docs.append(self._meta_to_document(meta, repo_full_name))

        return docs

    def read_repos(self, repo_names: list[str]) -> list[ProfileDocument]:
        """Read multiple repos."""
        docs: list[ProfileDocument] = []
        for name in repo_names:
            try:
                docs.extend(self.read_repo(name))
            except Exception:
                pass
        return docs

    # -- internals --

    def _api_get(self, path: str) -> dict | list | None:
        url = f"{self._base}{path}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "smart-apply-agent"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _get_readme(self, owner: str, repo: str) -> ProfileDocument | None:
        data = self._api_get(f"/repos/{owner}/{repo}/readme")
        if not data or "content" not in data:
            return None
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return self._to_document("README.md", content, f"{owner}/{repo}")

    def _list_docs(self, owner: str, repo: str) -> list[dict]:
        data = self._api_get(f"/repos/{owner}/{repo}/contents/docs")
        if not isinstance(data, list):
            return []
        return [f for f in data if f["name"].endswith(".md")]

    def _get_file(self, owner: str, repo: str, path: str) -> str | None:
        data = self._api_get(f"/repos/{owner}/{repo}/contents/{path}")
        if not data or "content" not in data:
            return None
        import base64
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")

    def _get_repo_meta(self, owner: str, repo: str) -> dict | None:
        data = self._api_get(f"/repos/{owner}/{repo}")
        return data

    @staticmethod
    def _to_document(path: str, content: str, repo_name: str) -> ProfileDocument:
        import hashlib
        doc_id = hashlib.sha256(f"{repo_name}/{path}".encode()).hexdigest()[:16]
        return ProfileDocument(
            document_id=doc_id,
            source_path=f"github://{repo_name}/{path}",
            title=f"{repo_name}: {Path(path).stem}",
            content=content,
            item_type="github_repo",
            metadata={
                "repo_name": repo_name,
                "relative_path": path,
                "source": "github_remote",
                "reader": "github_remote_reader",
            },
        )

    @staticmethod
    def _meta_to_document(meta: dict, repo_name: str) -> ProfileDocument:
        import hashlib
        doc_id = hashlib.sha256(repo_name.encode()).hexdigest()[:16]
        desc = meta.get("description", "")
        topics = ", ".join(meta.get("topics", []))
        lang = meta.get("language", "")
        stars = meta.get("stargazers_count", 0)
        content = f"# {repo_name}\n\n{desc}\n\n语言: {lang} | Stars: {stars} | Topics: {topics}"
        return ProfileDocument(
            document_id=doc_id,
            source_path=f"github://{repo_name}/meta",
            title=repo_name,
            content=content,
            item_type="github_repo",
            metadata={"repo_name": repo_name, "source": "github_remote", "stars": stars, "language": lang},
        )
