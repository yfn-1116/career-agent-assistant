import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.rag.pipeline import RAGPipeline
from career_agent.rag.retrievers.simple_retriever import SimpleRetriever
from career_agent.rag.schemas import RetrievedEvidence


SAMPLE_PROFILE_DIR = Path(__file__).resolve().parents[2] / "data" / "samples" / "profile"


def test_pipeline_builds_index_from_markdown_directory():
    pipeline = RAGPipeline()

    pipeline.build_index(SAMPLE_PROFILE_DIR)

    assert pipeline.count() > 0


def test_pipeline_retrieves_evidence_from_sample_profile():
    pipeline = RAGPipeline()
    pipeline.build_index(SAMPLE_PROFILE_DIR)

    results = pipeline.retrieve("RAG Agent Python", top_k=3)

    assert results
    assert len(results) <= 3
    assert all(isinstance(item, RetrievedEvidence) for item in results)
    assert all(item.source_path for item in results)
    assert any("RAG" in item.content or "Agent" in item.content for item in results)


def test_pipeline_empty_query_returns_empty_list():
    pipeline = RAGPipeline()
    pipeline.build_index(SAMPLE_PROFILE_DIR)

    assert pipeline.retrieve("") == []


def test_pipeline_clear_removes_indexed_chunks():
    pipeline = RAGPipeline()
    pipeline.build_index(SAMPLE_PROFILE_DIR)

    pipeline.clear()

    assert pipeline.count() == 0
    assert pipeline.retrieve("Python") == []


def test_simple_retriever_delegates_to_vectorstore():
    pipeline = RAGPipeline()
    pipeline.build_index(SAMPLE_PROFILE_DIR)
    retriever = SimpleRetriever(pipeline.vectorstore)

    results = retriever.retrieve("Python RAG", top_k=2)

    assert len(results) <= 2
    assert all(isinstance(item, RetrievedEvidence) for item in results)
