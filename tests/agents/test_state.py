"""Tests for agent state models."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.state import (
    AgentTaskState,
    GeneratedOutput,
    MatchAnalysisResult,
    ParsedJD,
)
from career_agent.rag.schemas import RetrievedEvidence


class TestParsedJD:
    def test_default_creation(self):
        jd = ParsedJD()
        assert jd.job_title == ""
        assert jd.hard_skills == []
        assert jd.raw_text == ""

    def test_lists_not_shared(self):
        jd1 = ParsedJD()
        jd2 = ParsedJD()
        jd1.hard_skills.append("Python")
        assert jd2.hard_skills == []

    def test_can_set_fields(self):
        jd = ParsedJD(
            job_title="AI Agent 实习生",
            hard_skills=["Python", "RAG"],
            keywords=["Agent", "LangGraph"],
        )
        assert jd.job_title == "AI Agent 实习生"
        assert "Python" in jd.hard_skills
        assert "Agent" in jd.keywords

    def test_metadata_can_store_custom_info(self):
        jd = ParsedJD(metadata={"parser": "test", "source": "sample"})
        assert jd.metadata["parser"] == "test"


class TestMatchAnalysisResult:
    def test_default_lists_not_shared(self):
        m1 = MatchAnalysisResult()
        m2 = MatchAnalysisResult()
        m1.strengths.append("Python 经验")
        assert m2.strengths == []

    def test_can_set_fields(self):
        result = MatchAnalysisResult(
            strengths=["Python 熟练"],
            weaknesses=["缺少 Go 经验"],
            recommended_projects=["RAG 知识库"],
            matched_keywords=["Python", "RAG"],
        )
        assert len(result.strengths) == 1
        assert len(result.weaknesses) == 1
        assert "RAG 知识库" in result.recommended_projects


class TestGeneratedOutput:
    def test_default_lists_not_shared(self):
        g1 = GeneratedOutput()
        g2 = GeneratedOutput()
        g1.resume_bullets.append("test bullet")
        assert g2.resume_bullets == []

    def test_communication_message_empty_by_default(self):
        g = GeneratedOutput()
        assert g.communication_message == ""


class TestAgentTaskState:
    def test_default_status_is_created(self):
        state = AgentTaskState()
        assert state.status == "created"

    def test_task_id_non_empty(self):
        state = AgentTaskState()
        assert len(state.task_id) > 0
        assert len(state.task_id) == 12

    def test_task_id_unique(self):
        s1 = AgentTaskState()
        s2 = AgentTaskState()
        assert s1.task_id != s2.task_id

    def test_can_save_parsed_jd(self):
        state = AgentTaskState()
        jd = ParsedJD(job_title="AI 实习生", hard_skills=["Python"])
        state.parsed_jd = jd
        assert state.parsed_jd.job_title == "AI 实习生"

    def test_can_save_retrieved_evidence(self):
        state = AgentTaskState()
        ev = RetrievedEvidence(
            evidence_id="ev-1",
            chunk_id="c-1",
            title="RAG 项目",
            content="基于 LangChain...",
            score=0.85,
            source_path="/data/projects.md",
            matched_keywords=["Python", "RAG"],
        )
        state.retrieved_evidence.append(ev)
        assert len(state.retrieved_evidence) == 1
        assert state.retrieved_evidence[0].evidence_id == "ev-1"

    def test_status_can_be_updated(self):
        state = AgentTaskState()
        state.status = "completed"
        assert state.status == "completed"

    def test_error_message_default_empty(self):
        state = AgentTaskState()
        assert state.error_message == ""

    def test_metadata_can_store_custom_info(self):
        state = AgentTaskState(metadata={"pipeline": "v1", "model": "mock"})
        assert state.metadata["pipeline"] == "v1"

    def test_default_retrieved_evidence_is_empty_list(self):
        state = AgentTaskState()
        assert state.retrieved_evidence == []

    def test_default_parsed_jd_is_none(self):
        state = AgentTaskState()
        assert state.parsed_jd is None

    def test_created_at_is_set(self):
        state = AgentTaskState()
        assert state.created_at != ""
        assert "T" in state.created_at  # ISO format
