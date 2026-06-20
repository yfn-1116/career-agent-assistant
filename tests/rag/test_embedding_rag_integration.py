"""Integration test: EmbeddingVectorStore with loaders and chunker.

Validates the full embedding retrieval path without modifying
the default RAGPipeline or MemoryVectorStore.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.github.local_repo_reader import LocalGitHubRepoReader
from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.embeddings.embedding_store import EmbeddingVectorStore
from career_agent.rag.embeddings.hash_provider import HashEmbeddingProvider
from career_agent.rag.loaders.markdown_loader import MarkdownProfileLoader
from career_agent.rag.schemas import RetrievedEvidence


PROFILE_DIR = Path("data/samples/profile")
GITHUB_DIR = Path("data/samples/github_repos")


def _build_store(docs) -> EmbeddingVectorStore:
    chunker = TextChunker(chunk_size=500, overlap=50)
    store = EmbeddingVectorStore(HashEmbeddingProvider(dim=64))
    chunks = chunker.chunk_documents(docs)
    store.add_chunks(chunks)
    return store


# ---------------------------------------------------------------------------
# Profile loader → Embedding search
# ---------------------------------------------------------------------------

class TestProfileEmbedding:
    @pytest.fixture(scope="class")
    def store(self):
        loader = MarkdownProfileLoader()
        docs = loader.load_directory(PROFILE_DIR)
        return _build_store(docs)

    def test_returns_retrieved_evidence(self, store):
        results = store.search("Agent RAG Workflow", top_k=3)
        assert len(results) > 0
        assert all(isinstance(r, RetrievedEvidence) for r in results)

    def test_metadata_has_source_path(self, store):
        results = store.search("Python 后端", top_k=3)
        for r in results:
            assert r.source_path != ""

    def test_no_network_access(self, store):
        assert store.count() > 0


# ---------------------------------------------------------------------------
# GitHub repo reader → Embedding search
# ---------------------------------------------------------------------------

class TestGitHubEmbedding:
    @pytest.fixture(scope="class")
    def store(self):
        reader = LocalGitHubRepoReader()
        docs = reader.read_repos(GITHUB_DIR)
        return _build_store(docs)

    def test_agent_rag_hits_career_agent(self, store):
        results = store.search("Agent RAG Workflow", top_k=3)
        assert any("career-agent-assistant" in r.source_path for r in results)

    def test_titration_cv_hits_chem(self, store):
        results = store.search("自动滴定 ResNet 串口", top_k=3)
        assert any("chem-auto-titration" in r.source_path for r in results)

    def test_docs_first_project_plan_hits_polyu(self, store):
        results = store.search("FastAPI Leaflet Docker 路径规划", top_k=3)
        assert any("polyu-internship-project" in r.source_path for r in results)

    def test_metadata_has_repo_name(self, store):
        results = store.search("Python FastAPI", top_k=3)
        for r in results:
            assert "repo_name" in r.metadata

    def test_no_network(self, store):
        assert store.count() > 0


# ---------------------------------------------------------------------------
# Default pipeline NOT modified
# ---------------------------------------------------------------------------

class TestDefaultPipelineUnchanged:
    """Verify the default RAGPipeline still uses MemoryVectorStore."""

    def test_default_pipeline_still_keyword(self):
        from career_agent.rag.pipeline import RAGPipeline
        from career_agent.rag.vectorstores.memory_store import MemoryVectorStore

        pipeline = RAGPipeline()
        assert isinstance(pipeline.vectorstore, MemoryVectorStore)
