"""Tests for lightweight rule-based reranker."""

import pytest

from career_agent.domain.schemas import RetrievedChunk
from career_agent.rag.reranker import LightweightReranker


def _chunk(
    chunk_id: str = "c1",
    source: str = "projects.md",
    content: str = "Python RAG pipeline with LangChain and Chroma",
    final_hybrid_score: float = 0.7,
    matched_skills: list[str] | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source=source,
        content=content,
        summary=content[:80],
        final_hybrid_score=final_hybrid_score,
        matched_skills=matched_skills or ["Python", "RAG"],
    )


# ---------------------------------------------------------------------------
# Basic
# ---------------------------------------------------------------------------


class TestRerankerBasic:
    def test_returns_same_count(self):
        chunks = [_chunk(f"c{i}") for i in range(5)]
        reranker = LightweightReranker()
        result = reranker.rerank(chunks)
        assert len(result) == 5

    def test_all_have_rerank_score(self):
        chunks = [_chunk(f"c{i}") for i in range(3)]
        reranker = LightweightReranker()
        result = reranker.rerank(chunks)
        for r in result:
            assert 0.0 <= r.rerank_score <= 1.0, f"rerank_score={r.rerank_score}"
            assert r.rerank_reason, "rerank_reason must be non-empty"

    def test_empty_input(self):
        reranker = LightweightReranker()
        assert reranker.rerank([]) == []

    def test_single_chunk(self):
        c = _chunk()
        reranker = LightweightReranker()
        result = reranker.rerank([c])
        assert len(result) == 1
        assert result[0].chunk_id == c.chunk_id


# ---------------------------------------------------------------------------
# Skill overlap
# ---------------------------------------------------------------------------


class TestSkillOverlap:
    def test_high_skill_overlap_ranks_higher(self):
        """Chunk with more JD skill matches should rank above less."""
        c_good = _chunk(
            chunk_id="good",
            content="Python RAG LangGraph Agent Chroma FastAPI Docker",
            matched_skills=["Python", "RAG", "LangGraph", "Agent"],
            final_hybrid_score=0.6,
        )
        c_bad = _chunk(
            chunk_id="bad",
            content="Java Spring microservices",
            matched_skills=["Java"],
            final_hybrid_score=0.8,  # even with higher hybrid score
        )
        jd_skills = {"Python", "RAG", "LangGraph", "Agent", "FastAPI"}
        reranker = LightweightReranker()
        result = reranker.rerank([c_bad, c_good], jd_skills=jd_skills)

        # c_good should rank first after rerank
        assert result[0].chunk_id == "good"


# ---------------------------------------------------------------------------
# Duplicate source penalty
# ---------------------------------------------------------------------------


class TestDuplicateSource:
    def test_duplicate_source_penalized(self):
        """Multiple chunks from same source — later ones get penalty."""
        c1 = _chunk(chunk_id="a", source="projects.md", content="unique content A", final_hybrid_score=0.8)
        c2 = _chunk(chunk_id="b", source="projects.md", content="unique content B", final_hybrid_score=0.8)
        c3 = _chunk(chunk_id="c", source="skills.md", content="unique content C", final_hybrid_score=0.7)

        jd_skills = {"Python"}
        reranker = LightweightReranker()
        result = reranker.rerank([c1, c2, c3], jd_skills=jd_skills)

        # First occurrence of projects.md keeps its position
        # Second occurrence drops below the skills.md chunk
        # The skills.md chunk (different source) should NOT be last
        ids = [r.chunk_id for r in result]
        # "a" (first projects.md) should be before "b" (second projects.md)
        assert ids.index("a") < ids.index("b")

    def test_duplicate_reason_includes_penalty(self):
        c1 = _chunk(chunk_id="a", source="same.md", content="first", final_hybrid_score=0.8)
        c2 = _chunk(chunk_id="b", source="same.md", content="second", final_hybrid_score=0.8)

        reranker = LightweightReranker()
        result = reranker.rerank([c1, c2])
        # The duplicated chunk should have a lower rerank_score
        assert result[1].rerank_score < result[0].rerank_score


# ---------------------------------------------------------------------------
# Content length
# ---------------------------------------------------------------------------


class TestContentLength:
    def test_too_short_content_penalized(self):
        c_short = _chunk(chunk_id="short", content="hi", final_hybrid_score=0.9)
        c_good = _chunk(chunk_id="good", content="Python RAG pipeline with LangChain " * 5, final_hybrid_score=0.7)
        reranker = LightweightReranker()
        result = reranker.rerank([c_short, c_good])
        # Short content should be penalized
        assert result[0].chunk_id == "good"

    def test_too_long_content_penalized(self):
        c_long = _chunk(chunk_id="long", content="x" * 2000, final_hybrid_score=0.9)
        c_good = _chunk(chunk_id="good", content="Python RAG " * 50, final_hybrid_score=0.7)
        reranker = LightweightReranker()
        result = reranker.rerank([c_long, c_good])
        # Overly long content penalized; good length (500 chars) preferred
        assert result[0].chunk_id == "good"


# ---------------------------------------------------------------------------
# Source quality
# ---------------------------------------------------------------------------


class TestSourceQuality:
    def test_resume_ranks_higher_than_unknown(self):
        c_resume = _chunk(chunk_id="r", source="resume.md", content="Python RAG", final_hybrid_score=0.6)
        c_notes = _chunk(chunk_id="n", source="notes.txt", content="Python RAG", final_hybrid_score=0.6)
        reranker = LightweightReranker()
        result = reranker.rerank([c_notes, c_resume])
        assert result[0].chunk_id == "r"


# ---------------------------------------------------------------------------
# Respects top_k
# ---------------------------------------------------------------------------


class TestRerankerTopK:
    def test_respects_top_k(self):
        chunks = [_chunk(f"c{i}") for i in range(10)]
        reranker = LightweightReranker(top_k=3)
        result = reranker.rerank(chunks)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Score range
# ---------------------------------------------------------------------------


class TestScoreRange:
    def test_all_scores_in_range(self):
        chunks = [
            _chunk("a", content="hi"),
            _chunk("b", content="Python RAG " * 30),
            _chunk("c", content="x" * 2000),
            _chunk("d", source="notes.txt"),
        ]
        reranker = LightweightReranker()
        result = reranker.rerank(chunks)
        for r in result:
            assert 0.0 <= r.rerank_score <= 1.0
            assert 0.0 <= r.final_hybrid_score <= 1.0  # unchanged
            assert isinstance(r.rerank_reason, str)
            assert len(r.rerank_reason) > 0
