"""Core RAG schema models for profile retrieval."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfileItem:
    """A structured user profile item, such as a project or skill."""

    item_id: str
    item_type: str
    title: str
    summary: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    tech_stack: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfileDocument:
    """A source document loaded from local profile materials."""

    document_id: str
    source_path: str
    title: str = ""
    content: str = ""
    item_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """A retrievable text chunk derived from a profile document."""

    chunk_id: str
    document_id: str
    content: str = ""
    chunk_index: int = 0
    source_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedEvidence:
    """A retrieval result that can support downstream generation."""

    evidence_id: str
    chunk_id: str
    title: str = ""
    content: str = ""
    score: float = 0.0
    source_path: str = ""
    matched_keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
