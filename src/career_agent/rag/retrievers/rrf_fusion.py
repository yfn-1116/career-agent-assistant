"""RRF (Reciprocal Rank Fusion) — merge multiple ranked lists.

RRF is a rank-aggregation method that does not require score calibration
between different retrieval systems. It simply uses ranks:

    RRF_score(d) = Σ 1 / (k + rank_i(d))

where:
- k is a constant (default 60) to dampen high ranks
- rank_i(d) is the position of document d in ranked list i (1-based)

Reference: Cormack et al., "Reciprocal Rank Fusion outperforms Condorcet
and individual rank learning methods", SIGIR 2009.
"""

from __future__ import annotations

from typing import Any


def reciprocal_rank_fusion(
    *ranked_lists: list[Any],
    k: int = 60,
) -> list[Any]:
    """Fuse multiple ranked lists into one using RRF.

    Parameters
    ----------
    *ranked_lists : list
        One or more ranked lists.  Items must be hashable (str, int, etc.)
        or have a ``chunk_id`` / ``evidence_id`` attribute.
    k : int
        RRF constant (default 60).  Higher = flatter weighting.

    Returns
    -------
    list
        Fused list sorted by descending RRF score.

    Example
    -------
    >>> bm25_results = ["chunk_A", "chunk_B", "chunk_C"]
    >>> emb_results  = ["chunk_C", "chunk_A", "chunk_D"]
    >>> fused = reciprocal_rank_fusion(bm25_results, emb_results, k=60)
    >>> fused[:2]
    ["chunk_A", "chunk_C"]
    """
    if not ranked_lists:
        return []

    scores: dict[Any, float] = {}

    for rl in ranked_lists:
        if not rl:
            continue
        for rank, item in enumerate(rl, start=1):  # 1-based rank
            key = _item_key(item)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)

    fused = sorted(scores.items(), key=lambda x: -x[1])
    return [item for item, _score in fused]


def rrf_fuse_evidence_lists(
    *ranked_evidence_lists: list[Any],
    k: int = 60,
) -> list[Any]:
    """Fuse multiple RetrievedEvidence lists using chunk_id as key.

    Returns the original evidence items in RRF-fused order.
    """
    if not ranked_evidence_lists:
        return []

    # Build chunk_id → evidence object mapping
    evidence_map: dict[str, Any] = {}
    for ev_list in ranked_evidence_lists:
        for ev in ev_list:
            cid = getattr(ev, "chunk_id", str(id(ev)))
            if cid not in evidence_map:
                evidence_map[cid] = ev

    # Fuse by chunk_id
    id_lists = [
        [getattr(ev, "chunk_id", str(id(ev))) for ev in rl]
        for rl in ranked_evidence_lists
    ]

    fused_ids = reciprocal_rank_fusion(*id_lists, k=k)

    result = []
    seen: set[str] = set()
    for cid in fused_ids:
        if cid not in seen and cid in evidence_map:
            seen.add(cid)
            result.append(evidence_map[cid])

    return result


def _item_key(item: Any) -> str:
    """Extract a hashable key from a ranked item."""
    if isinstance(item, str):
        return item
    # Try common id attributes
    for attr in ("chunk_id", "evidence_id", "document_id", "id"):
        val = getattr(item, attr, None)
        if isinstance(val, str):
            return val
    return str(id(item))
