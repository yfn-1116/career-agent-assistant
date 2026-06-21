from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.state import ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


GRADE_EXCELLENT = "excellent"
GRADE_GOOD = "good"
GRADE_WEAK = "weak"
GRADE_FAILED = "failed"


@dataclass
class RetrievalGradeItem:
    name: str
    score: float
    passed: bool
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalGradeReport:
    query: str
    top_k: int
    evidence_count: int
    average_score: float
    keyword_coverage: float
    source_diversity: int
    grade: str
    items: list[RetrievalGradeItem] = field(default_factory=list)
    evidence_summaries: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def grade_retrieval(
    query: str,
    parsed_jd: ParsedJD | None,
    evidence: list[RetrievedEvidence],
    top_k: int,
) -> RetrievalGradeReport:
    evidence_count = len(evidence)
    average_score = _average_score(evidence)
    keyword_coverage = _keyword_coverage(parsed_jd, evidence)
    source_diversity = len({ev.source_path for ev in evidence if ev.source_path})
    traceable = all(ev.source_path and ev.chunk_id for ev in evidence)

    items = [
        RetrievalGradeItem(
            name="evidence_count",
            score=1.0 if evidence_count > 0 else 0.0,
            passed=evidence_count > 0,
            message=(
                f"Retrieved {evidence_count} evidence items."
                if evidence_count > 0
                else "No evidence retrieved."
            ),
            metadata={"count": evidence_count, "top_k": top_k},
        ),
        RetrievalGradeItem(
            name="average_score",
            score=average_score,
            passed=average_score >= 0.35,
            message=f"Average evidence score is {average_score:.2f}.",
        ),
        RetrievalGradeItem(
            name="keyword_coverage",
            score=keyword_coverage,
            passed=keyword_coverage >= 0.5,
            message=f"Keyword coverage is {keyword_coverage:.2f}.",
        ),
        RetrievalGradeItem(
            name="source_diversity",
            score=min(source_diversity / 3, 1.0),
            passed=source_diversity >= 1,
            message=f"Evidence comes from {source_diversity} source(s).",
            metadata={"source_count": source_diversity},
        ),
        RetrievalGradeItem(
            name="traceability",
            score=1.0 if traceable and evidence_count > 0 else 0.0,
            passed=traceable and evidence_count > 0,
            message=(
                "All evidence has source_path and chunk_id."
                if traceable and evidence_count > 0
                else "Some evidence is missing source_path or chunk_id."
            ),
        ),
    ]

    total_score = sum(item.score for item in items) / len(items)
    grade = _grade_from_score(total_score, evidence_count, traceable)

    return RetrievalGradeReport(
        query=query,
        top_k=top_k,
        evidence_count=evidence_count,
        average_score=average_score,
        keyword_coverage=keyword_coverage,
        source_diversity=source_diversity,
        grade=grade,
        items=items,
        evidence_summaries=[_summarize_evidence(ev) for ev in evidence],
        metadata={"total_score": round(total_score, 4)},
    )


def _average_score(evidence: list[RetrievedEvidence]) -> float:
    if not evidence:
        return 0.0
    return round(sum(ev.score for ev in evidence) / len(evidence), 4)


def _keyword_coverage(
    parsed_jd: ParsedJD | None,
    evidence: list[RetrievedEvidence],
) -> float:
    if parsed_jd is None:
        return 0.0

    expected = set(parsed_jd.hard_skills + parsed_jd.bonus_skills + parsed_jd.keywords)
    expected = {kw.lower() for kw in expected if kw}
    if not expected:
        return 0.0

    evidence_text = " ".join(
        [" ".join(ev.matched_keywords) + " " + ev.content for ev in evidence]
    ).lower()
    matched = {kw for kw in expected if kw.lower() in evidence_text}
    return round(len(matched) / len(expected), 4)


def _grade_from_score(total_score: float, evidence_count: int, traceable: bool) -> str:
    if evidence_count == 0 or not traceable or total_score < 0.35:
        return GRADE_FAILED
    if total_score >= 0.85:
        return GRADE_EXCELLENT
    if total_score >= 0.65:
        return GRADE_GOOD
    return GRADE_WEAK


def _summarize_evidence(ev: RetrievedEvidence) -> dict[str, Any]:
    return {
        "evidence_id": ev.evidence_id,
        "chunk_id": ev.chunk_id,
        "title": ev.title,
        "score": ev.score,
        "source_path": ev.source_path,
        "matched_keywords": list(ev.matched_keywords),
        "snippet": ev.content[:240].replace("\n", " "),
    }
