"""Job Discovery — batch screening and ranking."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from career_agent.job_sources.schema import JobPosting
from career_agent.matching.scorer import JobMatchResult, JobMatchScorer


@dataclass
class RankedJob:
    job_posting: JobPosting | None = None
    match_score: float = 0.0
    recommended_action: str = "skip"
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    reason_summary: str = ""
    generated_message_preview: str = ""
    resume_template_suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in self.__dataclass_fields__}


class JobRanker:
    """Rank jobs by match quality."""

    def rank(self, postings: list[JobPosting], profile_items: list[Any]) -> list[RankedJob]:
        scorer = JobMatchScorer()
        ranked = []
        for p in postings:
            result = scorer.score(p.job_title, p.hard_skills, [], profile_items)
            ranked.append(RankedJob(
                job_posting=p,
                match_score=result.match_score,
                recommended_action=result.recommended_action,
                matched_skills=result.matched_skills,
                missing_skills=result.missing_skills,
                reason_summary="; ".join(result.reasons),
                resume_template_suggestion=self._pick_template(p),
            ))
        ranked.sort(key=lambda r: r.match_score, reverse=True)
        return ranked

    @staticmethod
    def _pick_template(posting: JobPosting) -> str:
        skills = [s.lower() for s in posting.hard_skills]
        if any(k in skills for k in ["rag", "agent", "langgraph"]): return "agent_role"
        if any(k in skills for k in ["opencv", "cnn", "pytorch", "cv"]): return "cv_role"
        if any(k in skills for k in ["fastapi", "django", "backend", "api"]): return "backend_role"
        return "general_intern"
