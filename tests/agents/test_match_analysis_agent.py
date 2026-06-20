"""Tests for MatchAnalysisAgent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import MatchAnalysisResult, ParsedJD
from career_agent.rag.schemas import RetrievedEvidence


def _make_evidence(
    evidence_id: str = "ev-1",
    title: str = "RAG 项目",
    matched_keywords: list[str] | None = None,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=evidence_id,
        chunk_id="c-1",
        title=title,
        content="基于 LangChain + Chroma...",
        score=0.85,
        source_path="/data/projects.md",
        matched_keywords=matched_keywords or ["Python", "RAG"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWithEvidence:
    def test_strengths_not_empty(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python", "RAG"])
        evidence = [_make_evidence(matched_keywords=["Python", "RAG"])]
        result = agent.analyze(jd, evidence)
        assert len(result.strengths) > 0
        assert any("Python" in s for s in result.strengths)

    def test_matched_keywords_aggregated(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python", "RAG", "LangChain"])
        evidence = [
            _make_evidence("e1", matched_keywords=["Python"]),
            _make_evidence("e2", matched_keywords=["RAG", "LangChain"]),
        ]
        result = agent.analyze(jd, evidence)
        assert "Python" in result.matched_keywords
        assert "RAG" in result.matched_keywords
        assert "LangChain" in result.matched_keywords

    def test_recommended_projects_from_titles(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python"])
        evidence = [
            _make_evidence("e1", title="RAG 知识库"),
            _make_evidence("e2", title="多 Agent 协作"),
        ]
        result = agent.analyze(jd, evidence)
        assert "RAG 知识库" in result.recommended_projects
        assert "多 Agent 协作" in result.recommended_projects

    def test_returns_match_analysis_result(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python"])
        evidence = [_make_evidence()]
        result = agent.analyze(jd, evidence)
        assert isinstance(result, MatchAnalysisResult)


class TestWithoutEvidence:
    def test_empty_evidence_does_not_error(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python", "Go"])
        result = agent.analyze(jd, [])
        assert isinstance(result, MatchAnalysisResult)
        assert result.strengths == []
        assert len(result.weaknesses) > 0  # all skills missing

    def test_suggestions_provided(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python"])
        result = agent.analyze(jd, [])
        assert len(result.suggestions) > 0


class TestMissingSkills:
    def test_unmatched_skills_go_to_weaknesses(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python", "Go"])
        evidence = [_make_evidence(matched_keywords=["Python"])]
        result = agent.analyze(jd, evidence)
        assert any("Go" in w for w in result.weaknesses)

    def test_suggestions_include_gap_advice(self):
        agent = MatchAnalysisAgent()
        jd = ParsedJD(hard_skills=["Python", "Go", "Rust"])
        evidence = [_make_evidence(matched_keywords=["Python"])]
        result = agent.analyze(jd, evidence)
        assert any("缺失" in s or "补充" in s for s in result.suggestions)


class TestEndToEnd:
    """Small integration: JD parser → retrieve → match analysis."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.retrieve_agent = RAGRetrieveAgent()
        self.retrieve_agent.ingest_profile_dir("data/samples/profile")
        self.parser = JDParserAgent()
        self.analysis_agent = MatchAnalysisAgent()

    def test_full_flow_on_sample_jd(self):
        jd_text = (Path("data/samples/jobs") / "agent_intern_jd.md").read_text(
            encoding="utf-8"
        )
        parsed = self.parser.parse(jd_text)
        evidence = self.retrieve_agent.retrieve(parsed, top_k=5)
        result = self.analysis_agent.analyze(parsed, evidence)

        assert isinstance(result, MatchAnalysisResult)
        assert len(result.matched_keywords) > 0

    def test_no_external_dependencies(self):
        agent = MatchAnalysisAgent()
        result = agent.analyze(ParsedJD(), [_make_evidence()])
        assert result is not None
