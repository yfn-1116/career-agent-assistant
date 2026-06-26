"""Tests for CrossEncoderReranker."""
import pytest
from career_agent.rag.reranker.cross_encoder_reranker import CrossEncoderReranker
from career_agent.rag.schemas import RetrievedEvidence


@pytest.fixture(scope="module")
def reranker():
    """Load once for all tests to avoid repeated model downloads."""
    return CrossEncoderReranker(device="cpu")


def _ev(cid: str, content: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=f"e-{cid}", chunk_id=cid, content=content,
        score=0.5, source_path=f"{cid}.md",
    )


class TestCrossEncoderReranker:
    def test_lazy_loading(self, reranker):
        assert not reranker.is_loaded
        # First call triggers loading
        results = reranker.rerank("test", [_ev("c1", "test content")], top_n=1)
        assert reranker.is_loaded
        assert reranker.device == "cpu"

    def test_rerank_relevance(self, reranker):
        query = "Python 后端开发 FastAPI"
        chunks = [
            _ev("c1", "熟练掌握 Python，有 FastAPI 后端开发经验，熟悉 Docker"),
            _ev("c2", "计算机视觉 PyTorch OpenCV CNN 图像分类"),
            _ev("c3", "精通 React TypeScript 前端开发 CSS"),
        ]
        results = reranker.rerank(query, chunks, top_n=3)
        assert len(results) == 3
        # c1 should rank highest: it directly matches Python backend
        assert results[0][0].chunk_id == "c1", (
            f"Most relevant chunk should be c1, got {results[0][0].chunk_id}"
        )
        # c2 and c3 are both irrelevant; we just check c1 is on top
        # (exact ordering of c2 vs c3 depends on the model's internal judgment)

    def test_rerank_respects_top_n(self, reranker):
        chunks = [_ev(f"c{i}", f"document {i} about Python") for i in range(10)]
        results = reranker.rerank("Python", chunks, top_n=3)
        assert len(results) == 3

    def test_empty_chunks_returns_empty(self, reranker):
        assert reranker.rerank("query", [], top_n=5) == []

    def test_scores_are_floats(self, reranker):
        chunks = [_ev("c1", "Python development"), _ev("c2", "Machine learning")]
        results = reranker.rerank("Python", chunks, top_n=2)
        for _, score in results:
            assert isinstance(score, float)

    def test_scores_descending(self, reranker):
        chunks = [_ev(f"c{i}", f"document {i}") for i in range(5)]
        results = reranker.rerank("test", chunks, top_n=5)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_and_filter_min_score(self, reranker):
        query = "Python 后端开发 FastAPI 数据库"
        chunks = [
            _ev("c1", "Python FastAPI Docker PostgreSQL 后端开发"),
            _ev("c2", "React TypeScript 前端开发"),
        ]
        selected, all_ranked, enough = reranker.rerank_and_filter(
            query, chunks, top_n=5, min_score=0.0,
        )
        # Both should be selected since min_score=0 is very low
        assert enough is True
        assert len(selected) > 0

    def test_rerank_and_filter_enough_evidence(self, reranker):
        query = "Python 后端开发"
        chunks = [
            _ev("c1", "Python FastAPI Docker PostgreSQL"),
            _ev("c2", "React TypeScript CSS"),
        ]
        selected, all_ranked, enough = reranker.rerank_and_filter(
            query, chunks, top_n=5, min_score=100.0,  # very high threshold
        )
        # No chunk should pass such a high threshold
        assert enough is False
        assert selected == []
