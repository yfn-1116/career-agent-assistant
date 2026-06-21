"""Shared state models for multi-agent job-match workflow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from career_agent.rag.schemas import RetrievedEvidence

if TYPE_CHECKING:
    from career_agent.rag.grading import RetrievalGradeReport


@dataclass
class ParsedJD:
    """Structured representation of a parsed job description."""

    job_title: str = ""
    job_direction: str = ""
    hard_skills: list[str] = field(default_factory=list)
    bonus_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchAnalysisResult:
    """Structured match analysis between a JD and retrieved user evidence."""

    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    recommended_projects: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedOutput:
    """Final grounded output produced by the build agent."""

    resume_bullets: list[str] = field(default_factory=list)
    communication_message: str = ""
    summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTaskState:
    """Top-level state that flows through the job-match workflow.

    Each agent reads from and writes to the subset of fields it owns.
    """

    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_request: str = ""
    job_description: str = ""
    parsed_jd: ParsedJD | None = None
    retrieved_evidence: list[RetrievedEvidence] = field(default_factory=list)
    retrieval_query: str = ""
    retrieval_grade_report: RetrievalGradeReport | None = None
    workflow_trace: list[str] = field(default_factory=list)
    match_analysis: MatchAnalysisResult | None = None
    generated_output: GeneratedOutput | None = None
    status: str = "created"
    error_message: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)
