"""Diagnostics JSON writer — captures full workflow state per run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_diagnostics(
    state: dict[str, Any],
    output_dir: str | Path = "outputs/diagnostics",
) -> Path:
    """Write a diagnostics JSON file from workflow state.

    Returns the path to the written file.
    """
    diag_dir = Path(output_dir)
    diag_dir.mkdir(parents=True, exist_ok=True)
    trace_id = state.get("trace_id", "unknown")
    path = diag_dir / f"{trace_id}.json"

    rs = state.get("retrieval_scores")
    gr = state.get("generated_result")

    diagnostics = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_jd": state.get("raw_jd", ""),
        "parsed_jd": _serialize_parsed_jd(state.get("parsed_jd")),
        "query_rounds": _build_query_rounds(state),
        "retrieval_scores": _serialize_retrieval_scores(rs),
        "retry_history": state.get("retry_history", []),
        "missing_keywords": state.get("missing_keywords", []),
        "decision": state.get("decision", ""),
        "fallback_reason": state.get("fallback_reason", ""),
        "match_analysis": _serialize_match(state.get("match_analysis")),
        "generated_bullets": list(gr.resume_bullets) if gr is not None else [],
        "communication_script": gr.communication_message if gr is not None else "",
        "evidence_sources": _collect_sources(state),
        "retry_count": state.get("retry_count", 0),
        "status": state.get("status", ""),
        "report_path": state.get("report_path", ""),
    }

    path.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _serialize_parsed_jd(pj: Any) -> dict | None:
    if pj is None:
        return None
    return {
        "job_title": getattr(pj, "job_title", ""),
        "job_direction": getattr(pj, "job_direction", "general"),
        "hard_skills": list(getattr(pj, "hard_skills", [])),
        "bonus_skills": list(getattr(pj, "bonus_skills", [])),
        "keywords": list(getattr(pj, "keywords", [])),
    }


def _serialize_retrieval_scores(rs: Any) -> dict | None:
    if rs is None:
        return None
    return {
        "grade": getattr(rs, "grade", "unknown"),
        "total_score": getattr(rs, "metadata", {}).get("total_score", 0),
        "evidence_count": getattr(rs, "evidence_count", 0),
        "average_score": getattr(rs, "average_score", 0),
        "keyword_coverage": getattr(rs, "keyword_coverage", 0),
        "source_diversity": getattr(rs, "source_diversity", 0),
    }


def _serialize_match(ma: Any) -> dict | None:
    if ma is None:
        return None
    return {
        "strengths": list(getattr(ma, "strengths", [])),
        "weaknesses": list(getattr(ma, "weaknesses", [])),
        "recommendations": list(getattr(ma, "recommended_projects", [])),
        "matched_skills": list(getattr(ma, "matched_keywords", [])),
        "suggestions": list(getattr(ma, "suggestions", [])),
    }


def _build_query_rounds(state: dict) -> list[dict]:
    history = state.get("retry_history", [])
    if history:
        return history
    # Fallback: single round from current state
    rs = state.get("retrieval_scores")
    return [{
        "round": 1,
        "query": state.get("queries", [""])[0] if state.get("queries") else "",
        "evidence_count": rs.evidence_count if rs is not None else 0,
        "total_score": rs.metadata.get("total_score", 0) if rs is not None else 0,
        "grade": rs.grade if rs is not None else "unknown",
    }]


def _collect_sources(state: dict) -> list[str]:
    sources: list[str] = []
    for ev in state.get("retrieved_chunks", []):
        src = getattr(ev, "source_path", "")
        if src and src not in sources:
            sources.append(src)
    return sources
