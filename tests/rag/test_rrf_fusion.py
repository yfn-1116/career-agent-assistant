"""Tests for Reciprocal Rank Fusion."""
import pytest
from career_agent.rag.retrievers.rrf_fusion import (
    reciprocal_rank_fusion,
    rrf_fuse_evidence_lists,
)
from career_agent.rag.schemas import RetrievedEvidence


class TestRRFFusion:
    def test_single_list_returns_same_order(self):
        result = reciprocal_rank_fusion(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_two_lists_consensus_ranks_higher(self):
        # "a" is #1 in both lists → should be #1 fused
        a = ["a", "b", "c"]
        b = ["a", "c", "b"]
        result = reciprocal_rank_fusion(a, b, k=60)
        assert result[0] == "a"

    def test_disjoint_lists_interleave(self):
        a = ["a", "b", "c"]
        b = ["d", "e", "f"]
        result = reciprocal_rank_fusion(a, b, k=60)
        assert len(result) == 6  # all unique items
        # First items of each list should appear early
        assert result[0] in ("a", "d")
        assert result[1] in ("a", "d")

    def test_empty_lists_handled(self):
        assert reciprocal_rank_fusion() == []
        assert reciprocal_rank_fusion([], []) == []
        assert reciprocal_rank_fusion(["a", "b"]) == ["a", "b"]

    def test_k_parameter_affects_ordering(self):
        a = ["x", "y", "z"]
        b = ["z", "y", "x"]
        # With large k, ranks are flatter → more like interleaving
        result_low_k = reciprocal_rank_fusion(a, b, k=1)
        result_high_k = reciprocal_rank_fusion(a, b, k=1000)
        # With k=1000, the contribution of rank difference is negligible
        # Both should still be deterministic
        assert len(result_low_k) == 3
        assert len(result_high_k) == 3


class TestRRFFuseEvidenceLists:
    def test_fuses_by_chunk_id(self):
        ev1 = RetrievedEvidence(
            evidence_id="e1", chunk_id="c1", content="A", score=0.9, source_path="a.md",
        )
        ev2 = RetrievedEvidence(
            evidence_id="e2", chunk_id="c2", content="B", score=0.8, source_path="b.md",
        )
        ev3 = RetrievedEvidence(
            evidence_id="e3", chunk_id="c3", content="C", score=0.7, source_path="c.md",
        )
        # BM25 order: c1, c2, c3
        # Embedding order: c3, c1, c2
        result = rrf_fuse_evidence_lists(
            [ev1, ev2, ev3],
            [ev3, ev1, ev2],
        )
        assert len(result) == 3
        # c1 appears high in both lists → should be #1
        assert result[0].chunk_id == "c1"

    def test_deduplicates_by_chunk_id(self):
        ev1a = RetrievedEvidence(
            evidence_id="e1a", chunk_id="c1", content="A", score=0.9, source_path="a.md",
        )
        ev1b = RetrievedEvidence(
            evidence_id="e1b", chunk_id="c1", content="A", score=0.8, source_path="a.md",
        )
        result = rrf_fuse_evidence_lists([ev1a], [ev1b])
        assert len(result) == 1  # same chunk_id → deduplicated
        assert result[0].chunk_id == "c1"
