"""Local GitHub repo Markdown reader — no network, no git commands."""

import hashlib
import re
from pathlib import Path

from career_agent.rag.schemas import ProfileDocument


class LocalGitHubRepoReader:
    """Read local simulated GitHub repos and produce ProfileDocuments.

    Reads README.md and docs/*.md from each repo directory.
    Does NOT access the network, call git, or read source files.
    """

    _ITEM_TYPE = "github_repo"

    def read_repo(self, repo_dir: str | Path) -> list[ProfileDocument]:
        """Read a single repo directory.

        Returns empty list for empty or non-existent directories.
        """
        path = Path(repo_dir).resolve()
        if not path.is_dir():
            return []

        documents: list[ProfileDocument] = []
        repo_name = path.name

        # README.md
        readme = path / "README.md"
        if readme.is_file():
            documents.append(self._load_file(readme, repo_name, "readme"))

        # docs/*.md
        docs_dir = path / "docs"
        if docs_dir.is_dir():
            for md_file in sorted(docs_dir.glob("*.md")):
                documents.append(self._load_file(md_file, repo_name, "docs"))

        return documents

    def read_repos(self, root_dir: str | Path) -> list[ProfileDocument]:
        """Read all repo directories under *root_dir*."""
        path = Path(root_dir).resolve()
        if not path.is_dir():
            return []

        documents: list[ProfileDocument] = []
        for child in sorted(path.iterdir()):
            if child.is_dir():
                documents.extend(self.read_repo(child))
        return documents

    # -- internal -----------------------------------------------------------

    def _load_file(
        self, file_path: Path, repo_name: str, role: str
    ) -> ProfileDocument:
        content = file_path.read_text(encoding="utf-8")
        title = self._extract_title(content) or file_path.stem
        rel_path = str(file_path.relative_to(file_path.parents[1]))
        document_id = hashlib.sha256(
            f"{repo_name}/{rel_path}".encode()
        ).hexdigest()[:16]

        return ProfileDocument(
            document_id=document_id,
            source_path=str(file_path),
            title=title,
            content=content,
            item_type=self._ITEM_TYPE,
            metadata={
                "repo_name": repo_name,
                "relative_path": rel_path,
                "source_path": str(file_path),
                "reader": "local_github_repo_reader",
                "document_role": role,
            },
        )

    @staticmethod
    def _extract_title(content: str) -> str:
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""
