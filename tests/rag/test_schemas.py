import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.rag.schemas import (
    DocumentChunk,
    ProfileDocument,
    ProfileItem,
    RetrievedEvidence,
)


def test_profile_item_can_be_created_with_defaults():
    item = ProfileItem(
        item_id="project-001",
        item_type="project",
        title="RAG 求职助手",
        summary="基于个人资料的岗位匹配项目",
        source="profile/projects.md",
    )

    assert item.item_id == "project-001"
    assert item.item_type == "project"
    assert item.title == "RAG 求职助手"
    assert item.summary == "基于个人资料的岗位匹配项目"
    assert item.source == "profile/projects.md"
    assert item.tags == []
    assert item.tech_stack == []
    assert item.highlights == []
    assert item.metadata == {}


def test_profile_document_can_be_created_with_metadata():
    document = ProfileDocument(
        document_id="doc-001",
        source_path="profile/resume.md",
        title="个人简历",
        content="Python 项目经历",
        item_type="resume",
        metadata={"owner": "demo-user"},
    )

    assert document.document_id == "doc-001"
    assert document.source_path == "profile/resume.md"
    assert document.title == "个人简历"
    assert document.content == "Python 项目经历"
    assert document.item_type == "resume"
    assert document.metadata["owner"] == "demo-user"


def test_document_chunk_can_be_created_with_source_metadata():
    chunk = DocumentChunk(
        chunk_id="chunk-001",
        document_id="doc-001",
        content="使用 Python 构建 RAG 原型",
        chunk_index=0,
        source_path="profile/projects.md",
        metadata={"section": "projects"},
    )

    assert chunk.chunk_id == "chunk-001"
    assert chunk.document_id == "doc-001"
    assert chunk.content == "使用 Python 构建 RAG 原型"
    assert chunk.chunk_index == 0
    assert chunk.source_path == "profile/projects.md"
    assert chunk.metadata["section"] == "projects"


def test_retrieved_evidence_can_store_score_and_keywords():
    evidence = RetrievedEvidence(
        evidence_id="evidence-001",
        chunk_id="chunk-001",
        title="RAG 求职助手",
        content="实现了岗位 JD 与项目经历的匹配分析",
        score=0.87,
        source_path="profile/projects.md",
        matched_keywords=["RAG", "JD", "匹配分析"],
        metadata={"retriever": "memory"},
    )

    assert evidence.evidence_id == "evidence-001"
    assert evidence.chunk_id == "chunk-001"
    assert evidence.title == "RAG 求职助手"
    assert evidence.content == "实现了岗位 JD 与项目经历的匹配分析"
    assert evidence.score == 0.87
    assert evidence.source_path == "profile/projects.md"
    assert evidence.matched_keywords == ["RAG", "JD", "匹配分析"]
    assert evidence.metadata["retriever"] == "memory"


def test_default_lists_and_dicts_are_not_shared():
    first_item = ProfileItem(item_id="a", item_type="skill", title="Python")
    second_item = ProfileItem(item_id="b", item_type="skill", title="LLM")
    first_item.tags.append("backend")
    first_item.metadata["level"] = "intermediate"

    first_evidence = RetrievedEvidence(evidence_id="e1", chunk_id="c1")
    second_evidence = RetrievedEvidence(evidence_id="e2", chunk_id="c2")
    first_evidence.matched_keywords.append("RAG")
    first_evidence.metadata["source"] = "test"

    assert second_item.tags == []
    assert second_item.metadata == {}
    assert second_evidence.matched_keywords == []
    assert second_evidence.metadata == {}


def test_metadata_can_preserve_source_information():
    chunk = DocumentChunk(
        chunk_id="chunk-002",
        document_id="doc-002",
        metadata={
            "source_file": "profile/internship.md",
            "section": "internship",
            "line_start": 12,
        },
    )

    assert chunk.metadata["source_file"] == "profile/internship.md"
    assert chunk.metadata["section"] == "internship"
    assert chunk.metadata["line_start"] == 12
