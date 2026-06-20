"""Markdown profile loader for local user profile documents."""

import hashlib
import re
from pathlib import Path

from career_agent.rag.schemas import ProfileDocument


class MarkdownProfileLoader:
    """Load local Markdown user profile files as ProfileDocument objects.

    Supports loading a single file or all .md files under a directory.
    Non-Markdown files are silently skipped when loading a directory.
    """

    # Map filename stems to item_type labels.
    _ITEM_TYPE_MAP: dict[str, str] = {
        "resume": "resume",
        "projects": "project",
        "github_repos": "github_repo",
        "skills": "skill",
        "internship": "internship",
    }

    _DEFAULT_ITEM_TYPE = "document"

    def load_file(self, file_path: str | Path) -> ProfileDocument:
        """Load a single Markdown file and return a ProfileDocument.

        Args:
            file_path: Path to a .md file.

        Returns:
            ProfileDocument with content, title, and metadata populated.
        """
        path = Path(file_path).resolve()
        content = path.read_text(encoding="utf-8")
        title = self._extract_title(content) or path.stem
        item_type = self._infer_item_type(path)
        document_id = self._generate_document_id(str(path))

        return ProfileDocument(
            document_id=document_id,
            source_path=str(path),
            title=title,
            content=content,
            item_type=item_type,
            metadata={
                "filename": path.name,
                "file_stem": path.stem,
                "source_path": str(path),
                "loader": "markdown_profile_loader",
            },
        )

    def load_directory(self, dir_path: str | Path) -> list[ProfileDocument]:
        """Load all .md files under a directory.

        Non-Markdown files and subdirectories are skipped.

        Args:
            dir_path: Path to a directory containing .md files.

        Returns:
            List of ProfileDocument objects, one per .md file found.
            Returns empty list if the directory contains no .md files.
        """
        path = Path(dir_path).resolve()
        if not path.is_dir():
            return []

        documents: list[ProfileDocument] = []
        for md_file in sorted(path.glob("*.md")):
            if md_file.is_file():
                documents.append(self.load_file(md_file))

        return documents

    # -- private helpers --------------------------------------------------------

    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract the first level-1 heading from Markdown content.

        Returns an empty string if no ``# heading`` is found.
        """
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""

    @classmethod
    def _infer_item_type(cls, path: Path) -> str:
        """Infer ``item_type`` from the file stem using a simple lookup table.

        Falls back to ``"document"`` for unknown filenames.
        """
        return cls._ITEM_TYPE_MAP.get(path.stem, cls._DEFAULT_ITEM_TYPE)

    @staticmethod
    def _generate_document_id(source_path: str) -> str:
        """Generate a stable document ID from the absolute file path."""
        return hashlib.sha256(source_path.encode("utf-8")).hexdigest()[:16]
