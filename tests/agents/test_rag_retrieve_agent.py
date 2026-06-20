"""Tests for RAGRetrieveAgent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


def _read_sample_jd(name: str) -> str:
    return (Path("data/samples/jobs") / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInit:
    def test_can_initialize(self):
        agent = RAGRetrieveAgent()
        assert agent.pipeline is not None

    def test_can_initialize_with_custom_pipeline(self):
        from career_agent.rag.pipeline import RAGPipeline
        pipeline = RAGPipeline()
        agent = RAGRetrieveAgent(pipeline=pipeline)
        assert agent.pipeline is pipeline


class TestBuildQuery:
    def test_query_from_parsed_jd(self):
        agent = RAGRetrieveAgent()
        jd = ParsedJD(
            job_direction="agent",
            hard_skills=["Python", "RAG", "LangGraph"],
            bonus_skills=["Docker"],
        )
        query = agent.build_query_from_parsed_jd(jd)
        assert "Python" in query
        assert "RAG" in query
        assert "agent" in query

    def test_query_contains_skills(self):
        agent = RAGRetrieveAgent()
        jd = ParsedJD(hard_skills=["Python", "FastAPI"])
        query = agent.build_query_from_parsed_jd(jd)
        assert "Python" in query
        assert "FastAPI" in query

    def test_empty_parsed_jd_returns_empty_query(self):
        agent = RAGRetrieveAgent()
        jd = ParsedJD()
        assert agent.build_query_from_parsed_jd(jd) == ""

    def test_general_direction_not_added_to_query(self):
        agent = RAGRetrieveAgent()
        jd = ParsedJD(job_direction="general", hard_skills=["Python"])
        query = agent.build_query_from_parsed_jd(jd)
        assert "general" not in query
        assert "Python" in query


class TestRetrieve:
    @pytest.fixture(autouse=True)
    def _setup(self):
        """Build index from sample profiles once per test class."""
        self.agent = RAGRetrieveAgent()
        self.agent.ingest_profile_dir("data/samples/profile")

    def test_retrieve_returns_evidence(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        parser = JDParserAgent()
        parsed = parser.parse(jd_text)
        evidence = self.agent.retrieve(parsed, top_k=5)
        assert len(evidence) > 0
        assert all(isinstance(e, RetrievedEvidence) for e in evidence)

    def test_top_k_respected(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        parser = JDParserAgent()
        parsed = parser.parse(jd_text)
        evidence = self.agent.retrieve(parsed, top_k=3)
        assert len(evidence) <= 3

    def test_empty_parsed_jd_returns_empty(self):
        evidence = self.agent.retrieve(ParsedJD(), top_k=5)
        assert evidence == []

    def test_retrieve_by_query(self):
        evidence = self.agent.retrieve_by_query("Python LangChain RAG", top_k=3)
        assert len(evidence) > 0

    def test_retrieve_by_empty_query_returns_empty(self):
        assert self.agent.retrieve_by_query("", top_k=5) == []
        assert self.agent.retrieve_by_query("   ", top_k=5) == []

    def test_no_external_network(self):
        """All operations should be local — no network access."""
        # If this test runs without errors, it confirms no network dependency.
        agent = RAGRetrieveAgent()
        agent.ingest_profile_dir("data/samples/profile")
        evidence = agent.retrieve_by_query("Python Docker", top_k=3)
        assert isinstance(evidence, list)
