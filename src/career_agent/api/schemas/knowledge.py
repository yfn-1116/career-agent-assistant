"""Knowledge-base API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeUploadRequest(BaseModel):
    filename: str
    content: str
    source_type: str = "text"


class KnowledgeUploadResponse(BaseModel):
    source_name: str
    chunk_count: int
    index_path: str
    saved_path: str | None = None
