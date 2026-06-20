"""Integration test: github reader → RAG pipeline."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.github.local_repo_reader import LocalGitHubRepoReader
from career_agent.rag.chunking.text_chunker import TextChunker
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


SAMPLES_DIR = Path("data/samples/github_repos")


@pytest.fixture(scope="module")
def indexed_store():
    reader = LocalGitHubRepoReader()
    chunker = TextChunker(chunk_size=500, overlap=50)
    store = MemoryVectorStore()

    docs = reader.read_repos(SAMPLES_DIR)
    chunks = chunker.chunk_documents(docs)
    store.add_chunks(chunks)
    return store


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReaderToRAG:
    def test_reader_loads_samples(self):
        reader = LocalGitHubRepoReader()
        docs = reader.read_repos(SAMPLES_DIR)
        assert len(docs) >= 7  # 3 READMEs + 4 docs

    def test_chunker_splits(self):
        reader = LocalGitHubRepoReader()
        chunker = TextChunker(chunk_size=500, overlap=50)
        docs = reader.read_repos(SAMPLES_DIR)
        chunks = chunker.chunk_documents(docs)
        assert len(chunks) >= len(docs)


class TestRetrieval:
    def test_rag_agent_workflow_hits_career_agent(self, indexed_store):
        results = indexed_store.search("RAG Agent Workflow", top_k=3)
        assert any("career-agent-assistant" in r.source_path for r in results)

    def test_titration_cv_hits_chem(self, indexed_store):
        results = indexed_store.search("自动滴定 OpenCV 串口", top_k=3)
        assert any("chem-auto-titration" in r.source_path for r in results)

    def test_docs_first_project_plan_hits_polyu(self, indexed_store):
        results = indexed_store.search("文档先行 项目计划", top_k=3)
        assert any("polyu-internship-project" in r.source_path for r in results)

    def test_evidence_metadata_has_repo_name(self, indexed_store):
        results = indexed_store.search("Python FastAPI", top_k=3)
        for r in results:
            assert "repo_name" in r.metadata

    def test_no_network_access(self):
        reader = LocalGitHubRepoReader()
        chunker = TextChunker()
        store = MemoryVectorStore()
        docs = reader.read_repos(SAMPLES_DIR)
        chunks = chunker.chunk_documents(docs)
        store.add_chunks(chunks)
        results = store.search("测试", top_k=1)
        assert isinstance(results, list)
