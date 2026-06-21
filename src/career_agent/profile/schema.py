"""Profile knowledge base schema — structured user capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Claim status enum
STATUS_IMPLEMENTED = "implemented"
STATUS_DESIGNED = "designed"
STATUS_PLANNED = "planned"
STATUS_UNCERTAIN = "uncertain"

VALID_STATUSES = {STATUS_IMPLEMENTED, STATUS_DESIGNED, STATUS_PLANNED, STATUS_UNCERTAIN}


@dataclass
class ProfileItem:
    """A structured user profile capability item.

    Every item has a *status* that determines what claims can be made:
    - implemented: can write "built/completed/implemented"
    - designed: can only write "designed/architected/planned interface"
    - planned: can only write "planned to support"
    - uncertain: cannot be used in resume unless user confirms
    """

    item_id: str = ""
    source_path: str = ""
    source_type: str = "document"
    title: str = ""
    project_name: str = ""
    skills: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    status: str = STATUS_UNCERTAIN
    confidence: float = 0.5
    raw_content: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}', must be one of {VALID_STATUSES}")
        if not self.source_path:
            raise ValueError("source_path must not be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id, "source_path": self.source_path,
            "source_type": self.source_type, "title": self.title,
            "project_name": self.project_name, "skills": list(self.skills),
            "claims": list(self.claims), "status": self.status,
            "confidence": self.confidence, "raw_content": self.raw_content,
            "updated_at": self.updated_at, "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProfileItem:
        return cls(
            item_id=str(d.get("item_id", "")), source_path=str(d.get("source_path", "")),
            source_type=str(d.get("source_type", "document")), title=str(d.get("title", "")),
            project_name=str(d.get("project_name", "")), skills=list(d.get("skills", [])),
            claims=list(d.get("claims", [])), status=str(d.get("status", STATUS_UNCERTAIN)),
            confidence=float(d.get("confidence", 0.5)), raw_content=str(d.get("raw_content", "")),
            updated_at=str(d.get("updated_at", "")), metadata=dict(d.get("metadata", {})),
        )
