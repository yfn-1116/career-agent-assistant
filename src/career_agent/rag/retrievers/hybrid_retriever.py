"""Hybrid Retriever — keyword + embedding fusion with metadata boost.

Combines results from two independent retrievers (keyword and embedding),
normalises scores, applies source-type and skill-overlap metadata boosts,
and returns domain ``RetrievedChunk`` objects with per-signal scores.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any, Callable

from career_agent.domain.schemas import ParsedJD, RetrievedChunk
from career_agent.rag.schemas import RetrievedEvidence

# ---------------------------------------------------------------------------
# Source-type weights for metadata scoring
# ---------------------------------------------------------------------------

SOURCE_TYPE_WEIGHTS: dict[str, float] = {
    "resume": 1.0,
    "project": 0.9,
    "github_repo": 0.85,
    "skill": 0.8,
    "internship": 0.8,
}

_DEFAULT_SOURCE_WEIGHT = 0.5
_DEFAULT_PRIORITY = 0.5

# Fusion formula weights
_W_VECTOR = 0.40
_W_KEYWORD = 0.35
_W_METADATA = 0.15
_W_PRIORITY = 0.10


# ---------------------------------------------------------------------------
# Score normalisation
# ---------------------------------------------------------------------------


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalise *scores* to [0, 1].

    Clips any value below 0 to 0.  If all scores are identical they are
    returned unchanged.  An empty list is returned as-is.
    """
    if not scores:
        return []

    clipped = [max(0.0, s) for s in scores]
    lo, hi = min(clipped), max(clipped)
    if hi == lo:
        return clipped

    return [(s - lo) / (hi - lo) for s in clipped]


# ---------------------------------------------------------------------------
# Metadata score
# ---------------------------------------------------------------------------


def _source_type_weight(source_path: str, metadata: dict[str, Any]) -> float:
    """Infer source-type weight from path or metadata item_type."""
    item_type = str(metadata.get("item_type", "")).lower()
    if item_type in SOURCE_TYPE_WEIGHTS:
        return SOURCE_TYPE_WEIGHTS[item_type]

    # Fallback: guess from filename
    stem = _file_stem(source_path).lower()
    for key, weight in SOURCE_TYPE_WEIGHTS.items():
        if key in stem:
            return weight

    return _DEFAULT_SOURCE_WEIGHT


def _file_stem(path: str) -> str:
    return path.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def _skill_overlap(chunk_content: str, jd_skills: set[str]) -> float:
    """Fraction of JD skills found in chunk content (exact word-boundary match)."""
    if not jd_skills:
        return 0.0
    text_lower = chunk_content.lower()
    matched = 0
    for skill in jd_skills:
        skill_lower = skill.strip().lower()
        if not skill_lower:
            continue
        if re.search(rf"(?<!\w){re.escape(skill_lower)}(?!\w)", text_lower):
            matched += 1
    return matched / len(jd_skills)


def metadata_score_for_chunk(
    chunk: Any,
    jd_skills: set[str],
    priority: float = _DEFAULT_PRIORITY,
) -> float:
    """Compute the metadata boost score for a chunk.

    Returns a value in [0, 1].

    * 0.5 × source_type_weight
    * 0.5 × skill_overlap (JD skills vs chunk content)
    """
    source_path = getattr(chunk, "source_path", "")
    metadata = getattr(chunk, "metadata", {}) or {}
    source_w = _source_type_weight(source_path, metadata)
    content = getattr(chunk, "content", "")
    overlap = _skill_overlap(content, jd_skills)
    return 0.5 * source_w + 0.5 * overlap


# ---------------------------------------------------------------------------
# HybridRetriever
# ---------------------------------------------------------------------------


# Type for a retriever callable: (query: str, top_k: int) -> list[RetrievedEvidence]
RetrieverFn = Callable[[str, int], list[RetrievedEvidence]]


class HybridRetriever:
    """Parallel keyword + embedding retrieval with score fusion.

    Parameters
    ----------
    keyword_retriever : callable or None
        A callable ``(query, top_k) -> list[RetrievedEvidence]``.
    embedding_retriever : callable or None
        A callable ``(query, top_k) -> list[RetrievedEvidence]``.
    """

    def __init__(
        self,
        keyword_retriever: RetrieverFn | None = None,
        embedding_retriever: RetrieverFn | None = None,
    ) -> None:
        self._kw = keyword_retriever
        self._emb = embedding_retriever

    # -- public API ---------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        parsed_jd: ParsedJD | None = None,
    ) -> list[RetrievedChunk]:
        """Run hybrid retrieval and return domain ``RetrievedChunk`` objects."""
        if not query.strip():
            return []

        # 1. Run both retrievers
        kw_results = self._safe_retrieve(self._kw, query, top_k * 2)
        emb_results = self._safe_retrieve(self._emb, query, top_k * 2)

        # 2. Index by chunk_id
        by_chunk_id: OrderedDict[str, dict[str, Any]] = OrderedDict()

        # Normalise scores from each retriever independently
        kw_scores = [ev.score for ev in kw_results]
        kw_norm = normalize_scores(kw_scores)
        for ev, norm_s in zip(kw_results, kw_norm):
            cid = ev.chunk_id
            if cid not in by_chunk_id:
                by_chunk_id[cid] = self._init_entry(ev)
            by_chunk_id[cid]["keyword_score"] = round(max(
                by_chunk_id[cid]["keyword_score"], norm_s
            ), 4)

        emb_scores = [ev.score for ev in emb_results]
        emb_norm = normalize_scores(emb_scores)
        for ev, norm_s in zip(emb_results, emb_norm):
            cid = ev.chunk_id
            if cid not in by_chunk_id:
                by_chunk_id[cid] = self._init_entry(ev)
            by_chunk_id[cid]["vector_score"] = round(max(
                by_chunk_id[cid]["vector_score"], norm_s
            ), 4)

        # 3. Build JD skills set for metadata scoring
        jd_skills: set[str] = set()
        if parsed_jd is not None:
            jd_skills = set(
                kw.strip().lower()
                for pool in (parsed_jd.hard_skills, parsed_jd.keywords)
                for kw in pool
                if kw.strip()
            )

        # 4. Compute metadata + fusion scores
        results: list[RetrievedChunk] = []
        for cid, entry in by_chunk_id.items():
            meta = metadata_score_for_chunk(
                entry["_chunk_ref"], jd_skills, priority=_DEFAULT_PRIORITY,
            )
            entry["metadata_score"] = round(meta, 4)

            final = (
                _W_VECTOR * entry["vector_score"]
                + _W_KEYWORD * entry["keyword_score"]
                + _W_METADATA * meta
                + _W_PRIORITY * _DEFAULT_PRIORITY
            )
            entry["final_hybrid_score"] = round(final, 4)

            results.append(RetrievedChunk(
                chunk_id=cid,
                source=entry["source"],
                content=entry["content"],
                summary=entry["content"][:120].replace("\n", " "),
                keyword_score=entry["keyword_score"],
                vector_score=entry["vector_score"],
                metadata_score=entry["metadata_score"],
                final_hybrid_score=entry["final_hybrid_score"],
                matched_skills=list(entry["matched_keywords"]),
            ))

        # 5. Sort and return top_k
        results.sort(key=lambda r: r.final_hybrid_score, reverse=True)
        return results[:top_k]

    # -- internal -----------------------------------------------------------

    @staticmethod
    def _safe_retrieve(
        retriever: RetrieverFn | None,
        query: str,
        top_k: int,
    ) -> list[RetrievedEvidence]:
        if retriever is None:
            return []
        try:
            return retriever(query, top_k)
        except Exception:
            return []

    @staticmethod
    def _init_entry(ev: RetrievedEvidence) -> dict[str, Any]:
        return {
            "source": ev.source_path,
            "content": ev.content,
            "keyword_score": 0.0,
            "vector_score": 0.0,
            "metadata_score": 0.0,
            "final_hybrid_score": 0.0,
            "matched_keywords": set(ev.matched_keywords or []),
            "_chunk_ref": ev,
        }
