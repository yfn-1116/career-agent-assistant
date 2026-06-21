"""Faithfulness / grounding checker — every claim must have evidence.

Detects unsupported claims, exaggerations, and missing source bindings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from career_agent.domain.schemas import Evidence, GeneratedBullet

# Exaggeration patterns — Chinese and English
_EXAGGERATION_PATTERNS = [
    (r"完整(?:实现|开发|部署|搭建)", "reserved/partial"),
    (r"全面(?:覆盖|支持|实现)", "reserved/partial"),
    (r"深度(?:优化|定制|集成)", "reserved/partial"),
    (r"大规模(?:部署|应用|落地)", "reserved/partial"),
    (r"(?:fully|completely)\s+(?:implement|deploy|build)", "reserved/partial"),
]


@dataclass
class FaithfulnessReport:
    """Result of faithfulness checking."""

    faithfulness_score: float = 0.0
    decision: str = "revise_required"  # pass / revise_required
    unsupported_claims: list[dict[str, Any]] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "faithfulness_score": self.faithfulness_score,
            "decision": self.decision,
            "unsupported_claims": list(self.unsupported_claims),
            "details": list(self.details),
            "metadata": dict(self.metadata),
        }


def _extract_skills(text: str) -> set[str]:
    """Extract technical terms from text for comparison."""
    tokens = set()
    lower = text.lower()
    # English words (3+ chars) — catch RAG, API, FastAPI, pipeline, etc.
    for m in re.finditer(r"\b[a-zA-Z]{3,}\b", lower):
        tokens.add(m.group(0))
    # Chinese tech terms (2-6 chars)
    for m in re.finditer(r"[一-鿿]{2,6}", text):
        tokens.add(m.group(0))
    return tokens


def _detect_exaggeration(bullet_text: str, evidence_text: str) -> tuple[bool, str]:
    """Check if bullet claims exceed what evidence supports."""
    bullet_lower = bullet_text.lower()
    evidence_lower = evidence_text.lower()

    for pattern, label in _EXAGGERATION_PATTERNS:
        if re.search(pattern, bullet_lower):
            # Check if evidence also has this pattern (not exaggerated)
            if not re.search(pattern, evidence_lower):
                return True, f"exaggeration: '{label}' in bullet but not in evidence"
            # Check if the specific technology name appears in evidence
            # e.g., "完整实现MCP" but evidence says "预留MCP接口"
            tech_match = re.search(
                pattern.replace(r"(?:\\w\+)", r"(\w+)"),
                bullet_lower,
            )
            if tech_match:
                tech_term = tech_match.group(1) if tech_match.lastindex else ""
                if tech_term and tech_term not in evidence_lower:
                    return True, f"exaggeration: '{tech_term}' claimed but not in evidence"

    return False, ""


def check_bullet_grounding(
    bullet: GeneratedBullet,
    evidences: list[Evidence],
) -> dict[str, Any]:
    """Check one bullet against available evidence.

    Returns a dict with grounded, score, matched_terms, exaggerated, reason.
    """
    if not bullet.has_evidence:
        return {
            "bullet_text": bullet.text[:120],
            "grounded": False,
            "score": 0.0,
            "matched_terms": [],
            "exaggerated": False,
            "reason": "no evidence_ids or source_paths",
        }

    # Find matching evidence
    bullet_ev_ids = set(bullet.evidence_ids)
    matched_ev = [ev for ev in evidences if ev.evidence_id in bullet_ev_ids]

    if not matched_ev:
        return {
            "bullet_text": bullet.text[:120],
            "grounded": False,
            "score": 0.0,
            "matched_terms": [],
            "exaggerated": False,
            "reason": f"evidence_ids {list(bullet.evidence_ids)} not found",
        }

    # Check content overlap
    bullet_skills = _extract_skills(bullet.text)
    evidence_text = " ".join(ev.content for ev in matched_ev)
    evidence_skills = _extract_skills(evidence_text)

    matched_terms = sorted(bullet_skills & evidence_skills)
    skill_overlap = len(matched_terms) / max(len(bullet_skills), 1)

    # Check exaggeration
    is_exaggerated, exag_reason = _detect_exaggeration(bullet.text, evidence_text)

    # Compute score
    evidence_score = 1.0  # has evidence
    overlap_score = min(1.0, skill_overlap * 2)  # scale up
    exag_penalty = 0.4 if is_exaggerated else 0.0

    score = max(0.0, evidence_score * 0.3 + overlap_score * 0.7 - exag_penalty)

    return {
        "bullet_text": bullet.text[:120],
        "grounded": True,
        "score": round(score, 4),
        "matched_terms": matched_terms,
        "exaggerated": is_exaggerated,
        "reason": exag_reason if is_exaggerated else f"matched {len(matched_terms)} terms",
    }


class FaithfulnessChecker:
    """Rule-based faithfulness checker — no external LLM required.

    Parameters
    ----------
    pass_threshold : float
        Minimum faithfulness_score to pass (default 0.75).
    """

    def __init__(self, pass_threshold: float = 0.75) -> None:
        self.pass_threshold = pass_threshold

    def check(
        self,
        bullets: list[GeneratedBullet],
        evidences: list[Evidence],
    ) -> FaithfulnessReport:
        """Check all bullets and return a report."""
        if not bullets:
            return FaithfulnessReport(
                faithfulness_score=1.0,
                decision="pass",
            )

        details = []
        unsupported = []
        scores = []

        for i, bullet in enumerate(bullets):
            result = check_bullet_grounding(bullet, evidences)
            result["bullet_index"] = i
            details.append(result)
            scores.append(result["score"])

            if not result["grounded"]:
                unsupported.append({
                    "bullet_index": i,
                    "text": bullet.text[:120],
                    "reason": result["reason"],
                })

        avg_score = sum(scores) / len(scores) if scores else 0.0
        decision = "pass" if avg_score >= self.pass_threshold else "revise_required"

        return FaithfulnessReport(
            faithfulness_score=round(avg_score, 4),
            decision=decision,
            unsupported_claims=unsupported,
            details=details,
            metadata={
                "checker": "faithfulness_checker",
                "total_bullets": len(bullets),
                "unsupported_count": len(unsupported),
                "pass_threshold": self.pass_threshold,
            },
        )
