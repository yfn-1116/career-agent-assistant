"""Common API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.3"
    service_name: str = "Internship Copilot API"


class ErrorResponse(BaseModel):
    detail: str
    code: str = "error"


class BrowserPageSnapshot(BaseModel):
    url: str = ""
    title: str = ""
    platform: str = "generic"
    page_type: str = "unknown"
    text: str = ""
    html: str = ""
    selected_text: str = ""
    captured_at: str | None = None


class BrowserAgentResult(BaseModel):
    page_type: str = ""
    job_posting: dict | None = None
    ranked_jobs: list[dict] = Field(default_factory=list)
    match_score: float = 0.0
    hiring_intent_score: float = 0.0
    opportunity_score: float = 0.0
    recommended_action: str = ""
    message_draft: dict | None = None
    verification_questions: list[str] = Field(default_factory=list)
    resume_paths: list[str] = Field(default_factory=list)
    application_record_id: str = ""
    reply_suggestion: dict | None = None
    next_action: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()
