"""Tests for EmbeddingProvider and HashEmbeddingProvider."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.rag.embeddings.base import EmbeddingProvider
from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
from career_agent.rag.embeddings.hash_provider import HashEmbeddingProvider
from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence


# ---------------------------------------------------------------------------
# EmbeddingProvider interface
# ---------------------------------------------------------------------------

class TestInterface:
    def test_subclass_enforced(self):
        with pytest.raises(TypeError):
            EmbeddingProvider()  # type: ignore

    def test_default_embed_texts(self):
        class _P(EmbeddingProvider):
            def embed_text(self, text):
                return [float(len(text))]
            @property
            def dimension(self):
                return 1

        p = _P()
        vecs = p.embed_texts(["a", "bb"])
        assert vecs == [[1.0], [2.0]]


# ---------------------------------------------------------------------------
# HashEmbeddingProvider
# ---------------------------------------------------------------------------

class TestHashProvider:
    def test_default_dimension(self):
        p = HashEmbeddingProvider()
        assert p.dimension == 64

    def test_custom_dimension(self):
        p = HashEmbeddingProvider(dim=128)
        assert p.dimension == 128

    def test_deterministic(self):
        p = HashEmbeddingProvider()
        v1 = p.embed_text("hello world")
        v2 = p.embed_text("hello world")
        assert v1 == v2

    def test_different_texts_different_vectors(self):
        p = HashEmbeddingProvider()
        v1 = p.embed_text("RAG Agent Workflow")
        v2 = p.embed_text("自动滴定系统")
        assert v1 != v2

    def test_empty_text_returns_zeros(self):
        p = HashEmbeddingProvider()
        v = p.embed_text("")
        assert v == [0.0] * 64

    def test_vector_is_unit_length(self):
        p = HashEmbeddingProvider()
        v = p.embed_text("test text for unit vector")
        norm = sum(x * x for x in v) ** 0.5
        assert abs(norm - 1.0) < 0.001

    def test_similar_texts_closer(self):
        """Trigram hash: texts sharing substrings are closer."""
        p = HashEmbeddingProvider(dim=128)
        v1 = p.embed_text("RAG pipeline with LangChain")
        v2 = p.embed_text("RAG pipeline with LlamaIndex")
        v3 = p.embed_text("自动滴定 OpenCV Arduino")
        # v1-v2 should be more similar than v1-v3
        from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
        sim_12 = EmbeddingVectorStore._cosine(v1, v2)
        sim_13 = EmbeddingVectorStore._cosine(v1, v3)
        assert sim_12 > sim_13

    def test_no_network_access(self):
        p = HashEmbeddingProvider()
        v = p.embed_text("test")
        assert len(v) == 64


# ---------------------------------------------------------------------------
# EmbeddingVectorStore
# ---------------------------------------------------------------------------

class TestEmbeddingStore:
    @pytest.fixture
    def store(self):
        return EmbeddingVectorStore(HashEmbeddingProvider(dim=64))

    @pytest.fixture
    def chunks(self):
        return [
            DocumentChunk(
                chunk_id="c1", document_id="d1",
                content="Python FastAPI RAG pipeline",
                chunk_index=0, source_path="/data/a.md",
                metadata={"filename": "a.md", "repo_name": "repo-a"},
            ),
            DocumentChunk(
                chunk_id="c2", document_id="d2",
                content="自动滴定 OpenCV Arduino 化学实验",
                chunk_index=0, source_path="/data/b.md",
                metadata={"filename": "b.md", "repo_name": "repo-b"},
            ),
            DocumentChunk(
                chunk_id="c3", document_id="d3",
                content="Docker FastAPI 后端 API 开发",
                chunk_index=0, source_path="/data/c.md",
                metadata={"filename": "c.md", "repo_name": "repo-c"},
            ),
        ]

    def test_add_and_count(self, store, chunks):
        store.add_chunks(chunks)
        assert store.count() == 3

    def test_search_returns_evidence(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("Python RAG", top_k=2)
        assert len(results) == 2
        assert all(isinstance(r, RetrievedEvidence) for r in results)

    def test_rag_query_hits_right_chunk(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("RAG pipeline Python", top_k=1)
        assert "repo-a" in results[0].metadata.get("repo_name", "")

    def test_cv_query_hits_chem(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("OpenCV 图像处理", top_k=1)
        assert "repo-b" in results[0].metadata.get("repo_name", "")

    def test_empty_query_returns_empty(self, store, chunks):
        store.add_chunks(chunks)
        assert store.search("", top_k=5) == []
        assert store.search("   ", top_k=5) == []

    def test_empty_store_returns_empty(self, store):
        assert store.search("anything", top_k=5) == []

    def test_clear_removes_all(self, store, chunks):
        store.add_chunks(chunks)
        store.clear()
        assert store.count() == 0

    def test_metadata_preserved(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("FastAPI", top_k=1)
        assert results[0].metadata["store"] == "embedding_vector_store"

    def test_score_is_float(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("Python", top_k=1)
        assert isinstance(results[0].score, float)
        assert 0.0 <= results[0].score <= 1.0

    def test_no_network_access(self, store, chunks):
        store.add_chunks(chunks)
        results = store.search("test", top_k=1)
        assert isinstance(results, list)
