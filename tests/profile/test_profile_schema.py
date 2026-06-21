"""Tests for profile schema and loader."""

import pytest
from career_agent.profile.schema import (
    STATUS_DESIGNED, STATUS_IMPLEMENTED, STATUS_PLANNED, STATUS_UNCERTAIN,
    ProfileItem,
)
from career_agent.profile.loader import ProfileLoader
from career_agent.rag.schemas import ProfileDocument


class TestProfileItem:
    def test_construct_minimal(self):
        item = ProfileItem(source_path="data/projects.md")
        assert item.source_path == "data/projects.md"
        assert item.status == STATUS_UNCERTAIN

    def test_source_path_required(self):
        with pytest.raises(ValueError, match="source_path"):
            ProfileItem()

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            ProfileItem(source_path="x", status="invalid")

    def test_valid_statuses_accepted(self):
        for s in [STATUS_IMPLEMENTED, STATUS_DESIGNED, STATUS_PLANNED, STATUS_UNCERTAIN]:
            item = ProfileItem(source_path="x", status=s)
            assert item.status == s

    def test_designed_not_implemented(self):
        item = ProfileItem(source_path="docs/design.md", status=STATUS_DESIGNED)
        assert item.status != STATUS_IMPLEMENTED

    def test_serializable(self):
        item = ProfileItem(
            source_path="data/projects.md", title="Agent Project",
            skills=["Python", "LangGraph"], claims=["built RAG pipeline"],
            status=STATUS_IMPLEMENTED,
        )
        d = item.to_dict()
        restored = ProfileItem.from_dict(d)
        assert restored.title == "Agent Project"
        assert restored.skills == ["Python", "LangGraph"]
        assert restored.status == STATUS_IMPLEMENTED

    def test_claims_not_empty(self):
        item = ProfileItem(source_path="x", claims=["claim 1", "claim 2"])
        assert len(item.claims) == 2


class TestProfileLoader:
    def test_load_project_as_implemented(self):
        doc = ProfileDocument(
            document_id="d1", source_path="data/projects.md",
            title="Smart Apply Agent", content="# 项目\n完成 RAG pipeline 实现\n技术栈：Python, LangGraph",
            item_type="project",
        )
        loader = ProfileLoader()
        item = loader.load(doc)
        assert item.status == STATUS_IMPLEMENTED
        assert len(item.claims) > 0

    def test_load_architecture_as_designed(self):
        doc = ProfileDocument(
            document_id="d1", source_path="docs/architecture/design.md",
            title="Architecture Design", content="# 架构设计\n预留 MCP 接口\n后续扩展 tool calling",
            item_type="document",
        )
        loader = ProfileLoader()
        item = loader.load(doc)
        assert item.status in (STATUS_DESIGNED, STATUS_PLANNED)

    def test_source_path_preserved(self):
        doc = ProfileDocument(document_id="d1", source_path="/tmp/resume.md", content="test", item_type="resume")
        item = ProfileLoader().load(doc)
        assert item.source_path == "/tmp/resume.md"

    def test_skills_extracted(self):
        doc = ProfileDocument(document_id="d1", source_path="x.md", content="Python, FastAPI, LangGraph, Docker", item_type="skills")
        item = ProfileLoader().load(doc)
        assert "Python" in item.skills or "FastAPI" in item.skills
