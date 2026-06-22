"""Job API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JobAnalyzeRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    jd_text: str
    source_url: str | None = None
    platform: str | None = None


class JobAnalyzeResponse(BaseModel):
    match_score: float = 0.0
    opportunity_score: float = 0.0
    recommendation: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    approval_required: bool = False
