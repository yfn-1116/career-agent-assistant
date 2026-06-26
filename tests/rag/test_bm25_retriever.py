"""Tests for BM25Retriever."""
import pytest
from career_agent.rag.retrievers.bm25_retriever import BM25Retriever
from career_agent.rag.schemas import DocumentChunk


def _chunk(cid: str, content: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=cid, document_id=f"d-{cid}", content=content,
        source_path=f"{cid}.md", metadata={"filename": f"{cid}.md"},
    )


class TestBM25Retriever:
    def test_empty_returns_empty(self):
        ret = BM25Retriever()
        assert ret.search("test") == []

    def test_index_and_search(self):
        ret = BM25Retriever()
        ret.add_chunks([
            _chunk("c1", "Python FastAPI 后端开发 数据库"),
            _chunk("c2", "计算机视觉 PyTorch OpenCV"),
            _chunk("c3", "AI Agent RAG LangGraph Python"),
        ])
        results = ret.search("Python 后端开发", top_k=2)
        assert len(results) == 2
        # c1 should rank highest for "后端开发"
        assert results[0].chunk_id == "c1"

    def test_top_k_respected(self):
        ret = BM25Retriever()
        ret.add_chunks([_chunk(f"c{i}", f"文档{i} Python") for i in range(10)])
        assert len(ret.search("Python", top_k=3)) == 3

    def test_clear(self):
        ret = BM25Retriever()
        ret.add_chunks([_chunk("c1", "test")])
        ret.clear()
        assert ret.search("test") == []
        assert ret.chunk_count == 0

    def test_chunk_count(self):
        ret = BM25Retriever()
        ret.add_chunks([_chunk("c1", "a"), _chunk("c2", "b")])
        assert ret.chunk_count == 2

    def test_search_returns_scored_results(self):
        """BM25 returns ranked results with valid scores."""
        ret = BM25Retriever()
        ret.add_chunks([
            _chunk("c1", "Python 开发经验，熟悉后端技术框架"),
            _chunk("c2", "Python FastAPI Docker 后端开发 Python 项目"),
            _chunk("c3", "计算机视觉 PyTorch OpenCV 图像处理"),
        ])
        results = ret.search("Python 后端开发", top_k=3)
        assert len(results) >= 1
        # All returned results should have valid metadata
        for r in results:
            assert isinstance(r.score, float)
            assert "bm25_score" in r.metadata
            assert r.metadata["retriever"] == "bm25"

    def test_callable_interface(self):
        """BM25Retriever should be callable as a RetrieverFn."""
        ret = BM25Retriever()
        ret.add_chunks([_chunk("c1", "Python RAG")])
        results = ret("Python", top_k=1)
        assert len(results) == 1
        assert results[0].chunk_id == "c1"

    def test_score_in_metadata(self):
        ret = BM25Retriever()
        ret.add_chunks([_chunk("c1", "Python FastAPI")])
        results = ret.search("Python", top_k=1)
        assert "bm25_score" in results[0].metadata
        assert results[0].metadata["retriever"] == "bm25"
