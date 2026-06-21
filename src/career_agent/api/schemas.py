"""Browser API schemas."""

from __future__ import annotations
import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class BrowserPageSnapshot:
    url: str = ""
    title: str = ""
    platform: str = "generic"
    page_type: str = "unknown"  # job_detail / job_list / chat / unknown
    text: str = ""
    html: str = ""
    selected_text: str = ""
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class BrowserAgentResult:
    page_type: str = ""
    job_posting: dict[str, Any] | None = None
    ranked_jobs: list[dict[str, Any]] = field(default_factory=list)
    match_score: float = 0.0
    hiring_intent_score: float = 0.0
    opportunity_score: float = 0.0
    recommended_action: str = ""
    message_draft: dict[str, Any] | None = None
    verification_questions: list[str] = field(default_factory=list)
    resume_paths: list[str] = field(default_factory=list)
    application_record_id: str = ""
    reply_suggestion: dict[str, Any] | None = None
    next_action: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}
