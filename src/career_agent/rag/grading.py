from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.state import ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


GRADE_EXCELLENT = "excellent"
GRADE_GOOD = "good"
GRADE_WEAK = "weak"
GRADE_FAILED = "failed"

AVERAGE_SCORE_PASS_THRESHOLD = 0.35
MIN_RETRIEVAL_SCORE = 0.0
MAX_RETRIEVAL_SCORE = 1.0
KEYWORD_COVERAGE_PASS_THRESHOLD = 0.5
SOURCE_DIVERSITY_TARGET = 3
TOTAL_SCORE_FAILED_THRESHOLD = 0.35
TOTAL_SCORE_GOOD_THRESHOLD = 0.65
TOTAL_SCORE_EXCELLENT_THRESHOLD = 0.85


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
    traceable = all(_is_traceable(ev) for ev in evidence)

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
            passed=average_score >= AVERAGE_SCORE_PASS_THRESHOLD,
            message=f"Average evidence score is {average_score:.2f}.",
        ),
        RetrievalGradeItem(
            name="keyword_coverage",
            score=keyword_coverage,
            passed=keyword_coverage >= KEYWORD_COVERAGE_PASS_THRESHOLD,
            message=f"Keyword coverage is {keyword_coverage:.2f}.",
        ),
        RetrievalGradeItem(
            name="source_diversity",
            score=min(source_diversity / SOURCE_DIVERSITY_TARGET, 1.0),
            passed=source_diversity >= SOURCE_DIVERSITY_TARGET,
            message=f"Evidence comes from {source_diversity} source(s).",
            metadata={"source_count": source_diversity},
        ),
        RetrievalGradeItem(
            name="traceability",
            score=1.0 if traceable and evidence_count > 0 else 0.0,
            passed=traceable and evidence_count > 0,
            message=(
                "All evidence has source_path, chunk_id, and numeric score."
                if traceable and evidence_count > 0
                else "Some evidence is missing source_path, chunk_id, or numeric score."
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
    if not all(_has_numeric_score(ev) for ev in evidence):
        return 0.0
    return round(sum(ev.score for ev in evidence) / len(evidence), 4)


def _is_traceable(ev: RetrievedEvidence) -> bool:
    return bool(ev.source_path and ev.chunk_id and _has_numeric_score(ev))


def _has_numeric_score(ev: RetrievedEvidence) -> bool:
    if isinstance(ev.score, bool):
        return False
    if not isinstance(ev.score, (int, float)):
        return False
    score = float(ev.score)
    return (
        math.isfinite(score)
        and MIN_RETRIEVAL_SCORE <= score <= MAX_RETRIEVAL_SCORE
    )


def _keyword_coverage(
    parsed_jd: ParsedJD | None,
    evidence: list[RetrievedEvidence],
) -> float:
    if parsed_jd is None:
        return 0.0

    expected = set(parsed_jd.hard_skills + parsed_jd.bonus_skills + parsed_jd.keywords)
    expected = {_normalize_keyword(kw) for kw in expected if _normalize_keyword(kw)}
    if not expected:
        return 0.0

    matched_keywords = {
        _normalize_keyword(kw)
        for ev in evidence
        for kw in ev.matched_keywords
        if _normalize_keyword(kw)
    }
    evidence_text = _normalize_keyword(" ".join(ev.content for ev in evidence))

    matched = {
        kw
        for kw in expected
        if kw in matched_keywords or _contains_term(evidence_text, kw)
    }
    return round(len(matched) / len(expected), 4)


def _normalize_keyword(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _contains_term(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None


def _grade_from_score(total_score: float, evidence_count: int, traceable: bool) -> str:
    if (
        evidence_count == 0
        or not traceable
        or total_score < TOTAL_SCORE_FAILED_THRESHOLD
    ):
        return GRADE_FAILED
    if total_score >= TOTAL_SCORE_EXCELLENT_THRESHOLD:
        return GRADE_EXCELLENT
    if total_score >= TOTAL_SCORE_GOOD_THRESHOLD:
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
