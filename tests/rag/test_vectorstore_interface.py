import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.rag.schemas import DocumentChunk, RetrievedEvidence
from career_agent.rag.vectorstores.base import VectorStore
from career_agent.rag.vectorstores.memory_store import MemoryVectorStore


def _chunk(
    chunk_id: str,
    content: str,
    source_path: str = "profile/projects.md",
    **metadata,
) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        content=content,
        chunk_index=0,
        source_path=source_path,
        metadata=metadata,
    )


def test_memory_vectorstore_implements_vectorstore_interface():
    store = MemoryVectorStore()

    assert isinstance(store, VectorStore)
    assert store.count() == 0


def test_add_chunks_and_count():
    store = MemoryVectorStore()
    chunks = [
        _chunk("c1", "Python RAG 项目"),
        _chunk("c2", "HR 沟通话术生成"),
    ]

    store.add_chunks(chunks)

    assert store.count() == 2


def test_search_returns_retrieved_evidence_with_source_and_metadata():
    store = MemoryVectorStore()
    store.add_chunks(
        [
            _chunk(
                "c1",
                "使用 Python 构建 RAG 检索和岗位匹配分析",
                title="RAG 求职助手",
                section="projects",
            )
        ]
    )

    results = store.search("Python RAG 匹配", top_k=1)

    assert len(results) == 1
    evidence = results[0]
    assert isinstance(evidence, RetrievedEvidence)
    assert evidence.chunk_id == "c1"
    assert evidence.content == "使用 Python 构建 RAG 检索和岗位匹配分析"
    assert evidence.source_path == "profile/projects.md"
    assert evidence.title == "RAG 求职助手"
    assert evidence.metadata["section"] == "projects"
    assert evidence.metadata["vectorstore"] == "memory"
    assert set(evidence.matched_keywords) >= {"Python", "RAG"}
    assert evidence.score > 0


def test_search_orders_by_keyword_overlap_score():
    store = MemoryVectorStore()
    store.add_chunks(
        [
            _chunk("c1", "Python 后端接口开发"),
            _chunk("c2", "Python RAG 检索 匹配分析"),
            _chunk("c3", "校园活动运营"),
        ]
    )

    results = store.search("Python RAG 匹配", top_k=2)

    assert [r.chunk_id for r in results] == ["c2", "c1"]
    assert results[0].score > results[1].score


def test_search_respects_top_k():
    store = MemoryVectorStore()
    store.add_chunks(
        [
            _chunk("c1", "Python RAG"),
            _chunk("c2", "Python RAG JD"),
            _chunk("c3", "Python"),
        ]
    )

    assert len(store.search("Python RAG JD", top_k=2)) == 2


def test_search_empty_query_returns_empty_list():
    store = MemoryVectorStore()
    store.add_chunks([_chunk("c1", "Python RAG")])

    assert store.search("") == []
    assert store.search("   ") == []


def test_clear_removes_all_chunks():
    store = MemoryVectorStore()
    store.add_chunks([_chunk("c1", "Python RAG")])

    store.clear()

    assert store.count() == 0
    assert store.search("Python") == []
