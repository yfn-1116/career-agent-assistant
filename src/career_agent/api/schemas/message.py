"""Message API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateMessageRequest(BaseModel):
    job_id: str | None = None
    jd_text: str
    tone: str | None = None
    user_goal: str | None = None


class GenerateMessageResponse(BaseModel):
    message: str = ""
    evidence_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    approval_required: bool = False
