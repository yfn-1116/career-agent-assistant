"""Lightweight rule-based reranker — no external model required.

Re-ranks ``RetrievedChunk`` objects based on skill overlap, source quality,
evidence specificity, content-length penalty, and duplicate-source penalty.

Interface reserves ``Reranker`` as an ABC for future LLM-based re-rankers.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from career_agent.domain.schemas import RetrievedChunk

# ---------------------------------------------------------------------------
# Source quality weights (same as hybrid retriever)
# ---------------------------------------------------------------------------

SOURCE_WEIGHTS: dict[str, float] = {
    "resume": 1.0,
    "project": 0.9,
    "github_repo": 0.85,
    "skill": 0.8,
    "internship": 0.8,
}
_DEFAULT_SOURCE_WEIGHT = 0.5

# Sweet spot for content length (characters)
_LEN_MIN = 200
_LEN_MAX = 800
_LEN_TOO_SHORT = 50
_LEN_TOO_LONG = 2000

# Rerank formula weights
_W_SKILL = 0.35
_W_SOURCE = 0.25
_W_SPECIFICITY = 0.20
_W_LENGTH = 0.10
_W_DUP = 0.10


# ---------------------------------------------------------------------------
# ABC
# ---------------------------------------------------------------------------


class Reranker(ABC):
    """Abstract reranker — rule-based by default, LLM-replaceable later."""

    @abstractmethod
    def rerank(
        self,
        chunks: list[RetrievedChunk],
        jd_skills: set[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Re-rank *chunks* and return the top *top_k*."""


# ---------------------------------------------------------------------------
# LightweightReranker
# ---------------------------------------------------------------------------


class LightweightReranker(Reranker):
    """Rule-based reranker using skill, source, specificity, and dedup signals.

    Parameters
    ----------
    top_k : int
        Number of results to return after re-ranking (default 5).
    """

    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k

    # -- Reranker interface -------------------------------------------------

    def rerank(
        self,
        chunks: list[RetrievedChunk],
        jd_skills: set[str] | None = None,
    ) -> list[RetrievedChunk]:
        if not chunks:
            return []

        skills = jd_skills or set()
        source_counts: Counter[str] = Counter()

        for i, chunk in enumerate(chunks):
            source = chunk.source or ""
            source_counts[source] += 1
            is_dup = source_counts[source] > 1

            skill_s = _skill_overlap_score(chunk, skills)
            source_s = _source_quality_score(source)
            spec_s = _specificity_score(chunk.content)
            len_s = 1.0 - _length_penalty(chunk.content)
            dup_s = 0.5 if is_dup else 1.0

            rerank_score = round(
                _W_SKILL * skill_s
                + _W_SOURCE * source_s
                + _W_SPECIFICITY * spec_s
                + _W_LENGTH * len_s
                + _W_DUP * dup_s,
                4,
            )
            chunk.rerank_score = rerank_score
            chunk.rerank_reason = _build_reason(
                skill_s, source_s, spec_s, len_s, dup_s, is_dup, source,
            )

        # Sort by rerank_score descending, stable for equal scores
        chunks.sort(key=lambda c: c.rerank_score, reverse=True)
        return chunks[: self.top_k]


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _skill_overlap_score(chunk: RetrievedChunk, jd_skills: set[str]) -> float:
    """Proportion of chunk skills that overlap with JD skills."""
    if not jd_skills:
        return 0.5  # neutral
    chunk_skills = {s.lower().strip() for s in chunk.matched_skills}
    if not chunk_skills:
        # Fall back to checking content for JD skills
        text_lower = chunk.content.lower()
        matched = sum(
            1 for s in jd_skills
            if s.lower().strip() and re.search(
                rf"(?<!\w){re.escape(s.lower().strip())}(?!\w)", text_lower
            )
        )
        return matched / len(jd_skills) if jd_skills else 0.5

    matched = len(chunk_skills & {s.lower().strip() for s in jd_skills})
    return matched / len(jd_skills) if jd_skills else 0.5


def _source_quality_score(source_path: str) -> float:
    """Infer source quality weight from file path."""
    stem = _file_stem(source_path).lower()
    for key, weight in SOURCE_WEIGHTS.items():
        if key in stem:
            return weight
    return _DEFAULT_SOURCE_WEIGHT


def _specificity_score(content: str) -> float:
    """Reward content that is 'specific' — not too vague.

    Specificity is measured as the relative amount of non-stopword content.
    """
    if not content:
        return 0.0
    # Simple heuristic: presence of technical terms, numbers, proper nouns
    tech_terms = len(re.findall(
        r"\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b|\d+\.?\d*",
        content,
    ))
    # Normalize by length
    density = tech_terms / max(len(content) / 100, 1)
    return min(1.0, density)


def _length_penalty(content: str) -> float:
    """Penalize content that is too short or too long.

    Returns a penalty in [0, 1] where 0 = no penalty, 1 = max penalty.
    """
    length = len(content)
    if length < _LEN_TOO_SHORT:
        return 0.8
    if length < _LEN_MIN:
        return 0.3
    if length <= _LEN_MAX:
        return 0.0  # sweet spot
    if length > _LEN_TOO_LONG:
        return 0.8
    # Gradual penalty between _LEN_MAX and _LEN_TOO_LONG
    return 0.3 * (length - _LEN_MAX) / (_LEN_TOO_LONG - _LEN_MAX)


def _build_reason(
    skill_s: float,
    source_s: float,
    spec_s: float,
    len_s: float,
    dup_s: float,
    is_dup: bool,
    source: str,
) -> str:
    parts: list[str] = []
    if skill_s >= 0.6:
        parts.append(f"skill_high({skill_s:.2f})")
    elif skill_s < 0.3:
        parts.append(f"skill_low({skill_s:.2f})")
    else:
        parts.append(f"skill({skill_s:.2f})")

    parts.append(f"source({source_s:.2f})")

    if spec_s >= 0.5:
        parts.append(f"specific({spec_s:.2f})")

    if len_s < 0.5:
        parts.append(f"len_penalty({len_s:.2f})")

    if is_dup:
        parts.append(f"dup_penalty({dup_s:.2f})")

    return f"{_file_stem(source)}: " + ", ".join(parts)


def _file_stem(path: str) -> str:
    return path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
