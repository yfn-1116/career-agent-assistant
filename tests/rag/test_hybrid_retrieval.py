"""Tests for HybridRetriever — keyword + embedding fusion."""

import pytest

from career_agent.domain.schemas import ParsedJD, RetrievedChunk
from career_agent.rag.embeddings.hash_provider import HashEmbeddingProvider
from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
from career_agent.rag.retrievers.hybrid_retriever import (
    HybridRetriever,
    metadata_score_for_chunk,
    normalize_scores,
)
from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _chunk(
    chunk_id: str = "doc1_0",
    content: str = "Python RAG pipeline with LangChain",
    source_path: str = "data/samples/profile/projects.md",
    item_type: str = "project",
) -> DocumentChunk:
    """Build a rag.DocumentChunk (the existing one used by vector stores)."""
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="doc1",
        content=content,
        source_path=source_path,
        metadata={"item_type": item_type, "filename": source_path.split("/")[-1]},
    )


def _ev(chunk: DocumentChunk, score: float = 0.8, store: str = "memory") -> RetrievedEvidence:
    """Build a RetrievedEvidence for a chunk."""
    prefix = "evidence" if store == "memory" else "emb"
    return RetrievedEvidence(
        evidence_id=f"{prefix}-{chunk.chunk_id}",
        chunk_id=chunk.chunk_id,
        title="Test",
        content=chunk.content,
        score=score,
        source_path=chunk.source_path,
        matched_keywords=["Python", "RAG"],
        metadata={**chunk.metadata, "store": store},
    )


def _keyword_retriever(chunks_and_scores):
    """Factory: return a callable that returns pre-configured results."""
    def retrieve(query, top_k=5):
        results = []
        for chunk, score in chunks_and_scores[:top_k]:
            results.append(_ev(chunk, score, store="memory"))
        return results
    return retrieve


def _emb_retriever(chunks_and_scores):
    """Factory: return a callable that returns pre-configured results."""
    def retrieve(query, top_k=5):
        results = []
        for chunk, score in chunks_and_scores[:top_k]:
            results.append(_ev(chunk, score, store="embedding"))
        return results
    return retrieve


# ---------------------------------------------------------------------------
# metadata_score_for_chunk
# ---------------------------------------------------------------------------


class TestMetadataScore:
    def test_project_source_gets_higher_weight_than_unknown(self):
        c1 = _chunk(chunk_id="a_0", source_path="projects.md", item_type="project")
        c2 = _chunk(chunk_id="b_0", source_path="unknown.txt", item_type="document")

        s1 = metadata_score_for_chunk(c1, {"Python"})
        s2 = metadata_score_for_chunk(c2, {"Python"})
        assert s1 > s2

    def test_skill_overlap_raises_score(self):
        c = _chunk(chunk_id="a_0", content="Python LangGraph Agent RAG")
        s1 = metadata_score_for_chunk(c, {"Python", "LangGraph"})
        s2 = metadata_score_for_chunk(c, {"Java", "Spring"})
        assert s1 > s2

    def test_score_in_valid_range(self):
        c = _chunk(chunk_id="a_0")
        s = metadata_score_for_chunk(c, {"Python"})
        assert 0.0 <= s <= 1.0

    def test_no_skills_returns_base_weight(self):
        c = _chunk(chunk_id="a_0", item_type="project")
        s = metadata_score_for_chunk(c, set())
        # project weight = 0.9, no skill overlap → 0.5*0.9 + 0.5*0 = 0.45
        assert 0.4 <= s <= 0.5


# ---------------------------------------------------------------------------
# normalize_scores
# ---------------------------------------------------------------------------


class TestNormalizeScores:
    def test_all_positive(self):
        scores = [0.1, 0.5, 0.9]
        result = normalize_scores(scores)
        assert len(result) == 3
        assert all(0.0 <= s <= 1.0 for s in result)
        assert max(result) > min(result)

    def test_all_equal(self):
        scores = [0.5, 0.5, 0.5]
        result = normalize_scores(scores)
        assert result == [0.5, 0.5, 0.5]

    def test_single_element(self):
        assert normalize_scores([0.7]) == [0.7]

    def test_empty(self):
        assert normalize_scores([]) == []

    def test_clips_cosine_negative(self):
        """Cosine can be negative; clip to 0."""
        scores = [-0.3, 0.5, 0.8]
        result = normalize_scores(scores)
        assert result[0] >= 0.0

    def test_different_ranges_normalized(self):
        scores = [0.01, 0.02, 0.03]
        result = normalize_scores(scores)
        # Should be spread to 0-1 range
        assert min(result) == 0.0
        assert max(result) == 1.0


# ---------------------------------------------------------------------------
# HybridRetriever
# ---------------------------------------------------------------------------


class TestHybridRetriever:
    def test_keyword_only_mode(self):
        c = _chunk(chunk_id="a_0", content="Python RAG")
        kw = _keyword_retriever([(c, 0.8)])
        hr = HybridRetriever(keyword_retriever=kw)
        results = hr.retrieve("Python RAG", top_k=3)

        assert len(results) == 1
        assert isinstance(results[0], RetrievedChunk)
        assert results[0].chunk_id == "a_0"
        assert results[0].keyword_score > 0
        assert results[0].vector_score == 0.0  # no embedding retriever

    def test_embedding_only_mode(self):
        c = _chunk(chunk_id="a_0", content="Python RAG")
        emb = _emb_retriever([(c, 0.7)])
        hr = HybridRetriever(embedding_retriever=emb)
        results = hr.retrieve("Python RAG", top_k=3)

        assert len(results) == 1
        assert results[0].vector_score > 0
        assert results[0].keyword_score == 0.0

    def test_hybrid_combines_both_scores(self):
        """When a chunk appears in both retrievers, it gets both scores."""
        c = _chunk(chunk_id="shared_0", content="Python RAG Agent pipeline")
        kw = _keyword_retriever([(c, 0.9)])
        emb = _emb_retriever([(c, 0.7)])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)
        results = hr.retrieve("Python RAG Agent", top_k=3)

        assert len(results) == 1
        assert results[0].keyword_score > 0
        assert results[0].vector_score > 0
        assert results[0].final_hybrid_score > 0

    def test_fusion_boosts_chunk_seen_by_both(self):
        """A chunk returned by both retrievers ranks higher than keyword-only."""
        c_both = _chunk(chunk_id="both_0", content="Python RAG Agent LangGraph")
        c_kw_only = _chunk(chunk_id="kw_0", content="generic text")

        kw = _keyword_retriever([(c_both, 0.8), (c_kw_only, 0.8)])
        emb = _emb_retriever([(c_both, 0.6)])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)
        results = hr.retrieve("Python RAG", top_k=5)

        # c_both should rank first (seen by both)
        assert results[0].chunk_id == "both_0"

    def test_deduplication(self):
        """Same chunk should not appear twice."""
        c = _chunk(chunk_id="c_0", content="Python")
        kw = _keyword_retriever([(c, 0.8)])
        emb = _emb_retriever([(c, 0.6)])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)
        results = hr.retrieve("Python", top_k=5)
        assert len(results) == 1

    def test_all_scores_in_valid_range(self):
        chunks = [
            _chunk(chunk_id=f"c_{i}", content=f"skill_{i}")
            for i in range(5)
        ]
        kw = _keyword_retriever([(c, 0.3 + i * 0.1) for i, c in enumerate(chunks)])
        emb = _emb_retriever([(c, 0.4 + i * 0.1) for i, c in enumerate(chunks)])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)

        results = hr.retrieve("test", top_k=5)
        for r in results:
            assert 0.0 <= r.keyword_score <= 1.0, f"keyword_score={r.keyword_score}"
            assert 0.0 <= r.vector_score <= 1.0, f"vector_score={r.vector_score}"
            assert 0.0 <= r.metadata_score <= 1.0
            assert 0.0 <= r.final_hybrid_score <= 1.0

    def test_respects_top_k(self):
        chunks = [_chunk(chunk_id=f"c_{i}") for i in range(10)]
        kw = _keyword_retriever([(c, 0.8) for c in chunks])
        emb = _emb_retriever([(c, 0.6) for c in chunks[:3]])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)
        assert len(hr.retrieve("test", top_k=3)) == 3

    def test_empty_results(self):
        kw = _keyword_retriever([])
        emb = _emb_retriever([])
        hr = HybridRetriever(keyword_retriever=kw, embedding_retriever=emb)
        assert hr.retrieve("nothing", top_k=5) == []


class TestHybridRetrieverIntegration:
    """Integration tests with real MemoryVectorStore and EmbeddingVectorStore."""

    def test_with_real_memory_store(self):
        store = MemoryVectorStore()
        store.add_chunks([
            _chunk(chunk_id="a_0", content="Python FastAPI RAG pipeline"),
            _chunk(chunk_id="b_0", content="Java Spring Boot microservices"),
        ])
        hr = HybridRetriever(keyword_retriever=store.search)
        results = hr.retrieve("Python RAG FastAPI", top_k=3)
        assert len(results) >= 1
        # The Python/FastAPI/RAG chunk should rank higher
        assert "a_0" in [r.chunk_id for r in results]

    def test_with_real_embedding_store(self):
        provider = HashEmbeddingProvider(dim=64)
        store = EmbeddingVectorStore(provider)
        store.add_chunks([
            _chunk(chunk_id="a_0", content="Python FastAPI RAG pipeline"),
            _chunk(chunk_id="b_0", content="Java Spring Boot microservices"),
        ])
        hr = HybridRetriever(embedding_retriever=store.search)
        results = hr.retrieve("Python RAG FastAPI", top_k=3)
        assert len(results) >= 1

    def test_hybrid_with_real_stores(self):
        """Full hybrid: MemoryVectorStore + EmbeddingVectorStore."""
        chunks = [
            _chunk(chunk_id="a_0", content="Python FastAPI RAG pipeline", source_path="projects.md"),
            _chunk(chunk_id="b_0", content="Java Spring Boot", source_path="unknown.txt"),
            _chunk(chunk_id="c_0", content="Python LangGraph Agent tool calling", source_path="projects.md"),
        ]
        kw_store = MemoryVectorStore()
        kw_store.add_chunks(chunks)

        provider = HashEmbeddingProvider(dim=64)
        emb_store = EmbeddingVectorStore(provider)
        emb_store.add_chunks(chunks)

        hr = HybridRetriever(
            keyword_retriever=kw_store.search,
            embedding_retriever=emb_store.search,
        )
        results = hr.retrieve("Python RAG LangGraph Agent", top_k=3)
        assert len(results) >= 1
        # All results must be RetrievedChunk
        for r in results:
            assert isinstance(r, RetrievedChunk)
            assert r.chunk_id
            assert r.source

    def test_metadata_boost_improves_project_rank(self):
        """Project chunks rank above unknown-document chunks, all else equal."""
        c_project = _chunk(chunk_id="proj_0", content="Python RAG Agent", source_path="projects.md", item_type="project")
        c_unknown = _chunk(chunk_id="unk_0", content="Python RAG Agent", source_path="notes.txt", item_type="document")

        store = MemoryVectorStore()
        store.add_chunks([c_project, c_unknown])

        provider = HashEmbeddingProvider(dim=64)
        emb_store = EmbeddingVectorStore(provider)
        emb_store.add_chunks([c_project, c_unknown])

        hr = HybridRetriever(
            keyword_retriever=store.search,
            embedding_retriever=emb_store.search,
        )
        results = hr.retrieve("Python RAG Agent", top_k=2)
        # project chunk should rank first due to metadata boost
        assert results[0].chunk_id == "proj_0"
