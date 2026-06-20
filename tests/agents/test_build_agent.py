"""Tests for BuildAgent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.state import (
    GeneratedOutput,
    MatchAnalysisResult,
    ParsedJD,
)
from career_agent.models.mock_provider import MockProvider
from career_agent.rag.schemas import RetrievedEvidence


def _make_evidence(
    evidence_id: str = "ev-1",
    title: str = "RAG 知识库项目",
    content: str = "基于 LangChain + Chroma 构建的本地知识库 RAG 系统",
    source_path: str = "/data/projects.md",
    matched_keywords: list[str] | None = None,
) -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=evidence_id,
        chunk_id="c-1",
        title=title,
        content=content,
        score=0.85,
        source_path=source_path,
        matched_keywords=matched_keywords or ["Python", "RAG"],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWithEvidence:
    def test_generates_resume_bullets(self):
        agent = BuildAgent()
        jd = ParsedJD(job_title="AI Agent 实习生")
        evidence = [_make_evidence()]
        analysis = MatchAnalysisResult(strengths=["具备 Python 相关经验"])
        output = agent.build(jd, evidence, analysis)

        assert len(output.resume_bullets) > 0
        assert any("RAG 知识库项目" in b for b in output.resume_bullets)

    def test_evidence_refs_not_empty(self):
        agent = BuildAgent()
        jd = ParsedJD()
        evidence = [_make_evidence("ev-1"), _make_evidence("ev-2")]
        analysis = MatchAnalysisResult()
        output = agent.build(jd, evidence, analysis)

        assert len(output.evidence_refs) == 2
        assert "ev-1" in output.evidence_refs

    def test_communication_message_not_empty(self):
        agent = BuildAgent()
        jd = ParsedJD(job_title="RAG 工程师实习生")
        evidence = [_make_evidence()]
        analysis = MatchAnalysisResult(strengths=["具备 Python 相关经验"])
        output = agent.build(jd, evidence, analysis)

        assert len(output.communication_message) > 0
        assert "RAG 工程师" in output.communication_message

    def test_summary_not_empty(self):
        agent = BuildAgent()
        jd = ParsedJD(job_title="AI 实习生")
        evidence = [_make_evidence()]
        analysis = MatchAnalysisResult(
            strengths=["具备 Python 相关经验"],
            weaknesses=["缺少 Go 经验"],
        )
        output = agent.build(jd, evidence, analysis)

        assert len(output.summary) > 0

    def test_returns_generated_output(self):
        agent = BuildAgent()
        jd = ParsedJD()
        output = agent.build(jd, [_make_evidence()], MatchAnalysisResult())
        assert isinstance(output, GeneratedOutput)

    def test_bullet_contains_evidence_title_or_source(self):
        agent = BuildAgent()
        jd = ParsedJD()
        evidence = [_make_evidence(title="多 Agent 协作系统")]
        analysis = MatchAnalysisResult()
        output = agent.build(jd, evidence, analysis)

        text = " ".join(output.resume_bullets)
        assert "多 Agent 协作系统" in text or "/data/projects.md" in text


class TestWithoutEvidence:
    def test_empty_evidence_does_not_fabricate(self):
        agent = BuildAgent()
        jd = ParsedJD(job_title="AI 实习生", hard_skills=["Python", "Go"])
        analysis = MatchAnalysisResult(weaknesses=["缺少 Python 经验"])
        output = agent.build(jd, [], analysis)

        # Should produce a conservative message, not invent projects
        joined = " ".join(output.resume_bullets)
        assert "不足" in joined or "暂无" in joined or "补充" in joined

    def test_no_fake_project_names(self):
        agent = BuildAgent()
        jd = ParsedJD()
        output = agent.build(jd, [], MatchAnalysisResult())
        # Should not mention any project names
        joined = " ".join(output.resume_bullets)
        assert "RAG 知识库项目" not in joined


class TestNoExternalDependencies:
    def test_pure_rule_based(self):
        agent = BuildAgent()
        output = agent.build(ParsedJD(), [_make_evidence()], MatchAnalysisResult())
        assert output is not None
        assert output.evidence_refs == ["ev-1"]


# ---------------------------------------------------------------------------
# LLM integration tests
# ---------------------------------------------------------------------------

class TestDefaultNoLLM:
    """Default BuildAgent (no provider) must behave exactly like Phase 1."""

    def test_default_is_rule_based(self):
        agent = BuildAgent()
        assert not agent.use_llm

    def test_llm_false_with_provider_still_rule_based(self):
        mock = MockProvider(fixed_response="LLM 生成的内容")
        agent = BuildAgent(model_provider=mock, use_llm=False)
        assert not agent.use_llm
        # Should still use template-based communication
        jd = ParsedJD(job_title="测试")
        output = agent.build(jd, [_make_evidence()], MatchAnalysisResult())
        assert "您好" in output.communication_message


class TestWithMockLLM:
    def test_use_llm_true_calls_provider(self):
        mock = MockProvider(fixed_response="LLM 生成的联系话术。")
        agent = BuildAgent(model_provider=mock, use_llm=True)
        assert agent.use_llm

        jd = ParsedJD(job_title="AI 实习生")
        analysis = MatchAnalysisResult(strengths=["具备 Python 相关经验"])
        output = agent.build(jd, [_make_evidence()], analysis)

        assert mock.call_count == 1
        assert "LLM 生成" in output.communication_message

    def test_prompt_contains_evidence(self):
        mock = MockProvider()
        agent = BuildAgent(model_provider=mock, use_llm=True)

        ev = _make_evidence(title="RAG 项目", content="基于 LangChain 构建")
        agent.build(ParsedJD(), [ev], MatchAnalysisResult())

        assert mock.last_prompt is not None
        assert "RAG 项目" in mock.last_prompt
        assert "LangChain" in mock.last_prompt

    def test_prompt_contains_no_fabrication_constraint(self):
        mock = MockProvider()
        agent = BuildAgent(model_provider=mock, use_llm=True)

        agent.build(ParsedJD(), [_make_evidence()], MatchAnalysisResult())

        assert mock.last_system_prompt is not None
        assert "不得编造" in mock.last_system_prompt

    def test_provider_failure_falls_back_to_rule(self):
        class _FailingProvider(MockProvider):
            def generate(self, prompt, *, system_prompt=None, metadata=None):
                super().generate(prompt, system_prompt=system_prompt, metadata=metadata)
                raise RuntimeError("API 不可用")

        agent = BuildAgent(model_provider=_FailingProvider(), use_llm=True)
        jd = ParsedJD(job_title="AI 实习生")
        analysis = MatchAnalysisResult(strengths=["具备 Python 相关经验"])
        output = agent.build(jd, [_make_evidence()], analysis)

        # Should fall back to template communication
        assert "您好" in output.communication_message

    def test_empty_evidence_no_fabrication_with_llm(self):
        mock = MockProvider()
        agent = BuildAgent(model_provider=mock, use_llm=True)
        output = agent.build(ParsedJD(), [], MatchAnalysisResult())

        # resume bullets still use template (not LLM), so no fabrication
        joined = " ".join(output.resume_bullets)
        assert "不足" in joined or "暂无" in joined or "补充" in joined

    def test_evidence_refs_preserved_with_llm(self):
        mock = MockProvider()
        agent = BuildAgent(model_provider=mock, use_llm=True)
        ev = _make_evidence("ev-1")
        output = agent.build(ParsedJD(), [ev], MatchAnalysisResult())

        assert "ev-1" in output.evidence_refs
