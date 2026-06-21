"""Tests for domain schema standardization."""

import math

import pytest

from career_agent.domain.schemas import (
    AgentDecision,
    Evidence,
    GeneratedBullet,
    MatchAnalysis,
    ParsedJD,
    RetrievedChunk,
    RetrievalQuery,
    RetrievalScore,
    ToolCallTrace,
    WorkflowTrace,
)
from career_agent.domain.validation import validate_score


# ---------------------------------------------------------------------------
# Score validation
# ---------------------------------------------------------------------------


class TestScoreValidation:
    def test_accepts_zero(self):
        assert validate_score(0.0) == 0.0

    def test_accepts_half(self):
        assert validate_score(0.5) == 0.5

    def test_accepts_one(self):
        assert validate_score(1.0) == 1.0

    def test_accepts_int_zero(self):
        assert validate_score(0) == 0.0

    def test_accepts_int_one(self):
        assert validate_score(1) == 1.0

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="must be in"):
            validate_score(-0.1)

    def test_rejects_above_one(self):
        with pytest.raises(ValueError, match="must be in"):
            validate_score(1.1)

    def test_rejects_nan(self):
        with pytest.raises(ValueError, match="finite"):
            validate_score(math.nan)

    def test_rejects_inf(self):
        with pytest.raises(ValueError, match="finite"):
            validate_score(math.inf)

    def test_rejects_neg_inf(self):
        with pytest.raises(ValueError, match="finite"):
            validate_score(-math.inf)

    def test_rejects_bool_true(self):
        with pytest.raises(ValueError, match="bool"):
            validate_score(True)

    def test_rejects_bool_false(self):
        with pytest.raises(ValueError, match="bool"):
            validate_score(False)

    def test_rejects_none(self):
        with pytest.raises(ValueError, match="float"):
            validate_score(None)

    def test_rejects_string(self):
        with pytest.raises(ValueError, match="float"):
            validate_score("0.8")

    def test_custom_name_in_error(self):
        with pytest.raises(ValueError, match="my_score"):
            validate_score(-1.0, name="my_score")


# ---------------------------------------------------------------------------
# ParsedJD
# ---------------------------------------------------------------------------


class TestParsedJD:
    def test_construct_minimal(self):
        jd = ParsedJD()
        assert jd.job_title == ""
        assert jd.job_direction == "general"
        assert jd.hard_skills == []

    def test_construct_full(self):
        jd = ParsedJD(
            job_title="AI Agent 开发实习生",
            job_direction="agent",
            hard_skills=["Python", "LangGraph"],
            bonus_skills=["FastAPI"],
            soft_skills=["沟通"],
            keywords=["Agent", "RAG"],
            raw_text="# JD text",
        )
        assert jd.job_title == "AI Agent 开发实习生"
        assert len(jd.hard_skills) == 2

    def test_to_dict_roundtrip(self):
        jd = ParsedJD(job_title="Test", hard_skills=["Python"])
        d = jd.to_dict()
        restored = ParsedJD.from_dict(d)
        assert restored.job_title == "Test"
        assert restored.hard_skills == ["Python"]


# ---------------------------------------------------------------------------
# RetrievalQuery
# ---------------------------------------------------------------------------


class TestRetrievalQuery:
    def test_construct(self):
        q = RetrievalQuery(query_text="Python RAG Agent")
        assert q.query_text == "Python RAG Agent"
        assert q.round == 1

    def test_to_dict_roundtrip(self):
        q = RetrievalQuery(query_text="search", round=2, reason="retry for LangGraph")
        d = q.to_dict()
        restored = RetrievalQuery.from_dict(d)
        assert restored.query_text == "search"
        assert restored.round == 2
        assert restored.reason == "retry for LangGraph"


# ---------------------------------------------------------------------------
# RetrievedChunk
# ---------------------------------------------------------------------------


class TestRetrievedChunk:
    def test_construct_minimal(self):
        c = RetrievedChunk(
            chunk_id="c1",
            source="profile.md",
            content="some content",
            summary="short",
        )
        assert c.chunk_id == "c1"
        assert c.keyword_score == 0.0
        assert c.vector_score == 0.0
        assert c.final_hybrid_score == 0.0

    def test_scores_must_be_valid(self):
        with pytest.raises(ValueError):
            RetrievedChunk(chunk_id="c1", source="s", content="x", summary="y", keyword_score=1.5)

    def test_accepts_valid_scores(self):
        c = RetrievedChunk(
            chunk_id="c1",
            source="s",
            content="x",
            summary="y",
            keyword_score=0.8,
            vector_score=0.6,
            metadata_score=0.5,
            final_hybrid_score=0.65,
            rerank_score=0.7,
        )
        assert c.keyword_score == 0.8
        assert c.rerank_score == 0.7

    def test_to_dict_roundtrip(self):
        c = RetrievedChunk(
            chunk_id="c1", source="s", content="x", summary="y",
            matched_skills=["Python"], rerank_reason="good skill match",
        )
        d = c.to_dict()
        restored = RetrievedChunk.from_dict(d)
        assert restored.chunk_id == "c1"
        assert restored.matched_skills == ["Python"]


# ---------------------------------------------------------------------------
# RetrievalScore
# ---------------------------------------------------------------------------


class TestRetrievalScore:
    def test_construct(self):
        rs = RetrievalScore(
            total_score=0.75,
            grade="good",
        )
        assert rs.total_score == 0.75
        assert rs.grade == "good"

    def test_total_score_must_be_valid(self):
        with pytest.raises(ValueError):
            RetrievalScore(total_score=1.5)

    def test_total_score_rejects_bool(self):
        with pytest.raises(ValueError):
            RetrievalScore(total_score=True)

    def test_accepts_edge_values(self):
        assert RetrievalScore(total_score=0.0).total_score == 0.0
        assert RetrievalScore(total_score=1.0).total_score == 1.0

    def test_to_dict_roundtrip(self):
        rs = RetrievalScore(
            total_score=0.82,
            grade="good",
            evidence_count=5,
            keyword_coverage=0.67,
            average_score=0.55,
            source_diversity=3,
        )
        d = rs.to_dict()
        restored = RetrievalScore.from_dict(d)
        assert restored.total_score == 0.82
        assert restored.grade == "good"
        assert restored.evidence_count == 5


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class TestEvidence:
    def test_construct(self):
        ev = Evidence(
            evidence_id="ev-1",
            chunk_id="c1",
            source="profile.md",
            content="built a RAG pipeline",
            supported_claims=["RAG experience"],
            confidence=0.9,
        )
        assert ev.evidence_id == "ev-1"
        assert ev.confidence == 0.9
        assert ev.supported_claims == ["RAG experience"]

    def test_confidence_must_be_valid(self):
        with pytest.raises(ValueError):
            Evidence(evidence_id="e1", chunk_id="c1", source="s", content="x", confidence=1.5)

    def test_to_dict_roundtrip(self):
        ev = Evidence(
            evidence_id="ev-1", chunk_id="c1", source="s", content="x",
            supported_claims=["claim1"], confidence=0.8,
        )
        d = ev.to_dict()
        restored = Evidence.from_dict(d)
        assert restored.evidence_id == "ev-1"
        assert restored.supported_claims == ["claim1"]


# ---------------------------------------------------------------------------
# MatchAnalysis
# ---------------------------------------------------------------------------


class TestMatchAnalysis:
    def test_construct(self):
        ma = MatchAnalysis(
            strengths=["has Python"],
            weaknesses=["missing LangGraph"],
            recommendations=["add agent project"],
        )
        assert len(ma.strengths) == 1
        assert len(ma.weaknesses) == 1

    def test_to_dict_roundtrip(self):
        ma = MatchAnalysis(strengths=["a"], matched_skills=["Python"])
        d = ma.to_dict()
        restored = MatchAnalysis.from_dict(d)
        assert restored.strengths == ["a"]
        assert restored.matched_skills == ["Python"]


# ---------------------------------------------------------------------------
# GeneratedBullet
# ---------------------------------------------------------------------------


class TestGeneratedBullet:
    def test_construct_with_evidence(self):
        gb = GeneratedBullet(
            text="Built RAG pipeline with Chroma",
            evidence_ids=["ev-1", "ev-2"],
            source_paths=["projects.md"],
            confidence=0.85,
        )
        assert gb.text == "Built RAG pipeline with Chroma"
        assert gb.evidence_ids == ["ev-1", "ev-2"]
        assert gb.confidence == 0.85

    def test_has_evidence_ids_or_source_paths(self):
        """A bullet is still constructable without evidence, but consumers should check."""
        gb = GeneratedBullet(text="some text")
        assert gb.evidence_ids == []
        assert gb.source_paths == []

    def test_has_evidence_ids_property(self):
        gb = GeneratedBullet(
            text="x", evidence_ids=["ev-1"], source_paths=["profile.md"]
        )
        assert gb.has_evidence is True

    def test_has_evidence_false_when_empty(self):
        gb = GeneratedBullet(text="x")
        assert gb.has_evidence is False

    def test_confidence_must_be_valid(self):
        with pytest.raises(ValueError):
            GeneratedBullet(text="x", confidence=-0.1)

    def test_to_dict_roundtrip(self):
        gb = GeneratedBullet(
            text="Built API", evidence_ids=["ev-1"], confidence=0.9
        )
        d = gb.to_dict()
        restored = GeneratedBullet.from_dict(d)
        assert restored.text == "Built API"
        assert restored.evidence_ids == ["ev-1"]
        assert restored.confidence == 0.9


# ---------------------------------------------------------------------------
# AgentDecision
# ---------------------------------------------------------------------------


class TestAgentDecision:
    def test_construct_continue(self):
        d = AgentDecision(decision="continue", reason="score ok")
        assert d.decision == "continue"
        assert d.next_action == "analyze_match"

    def test_construct_retry(self):
        d = AgentDecision(decision="retry", reason="score low", next_action="rewrite_query")
        assert d.decision == "retry"

    def test_construct_fallback(self):
        d = AgentDecision(decision="fallback", reason="max retries", next_action="end")
        assert d.decision == "fallback"

    def test_default_next_action_from_decision(self):
        assert AgentDecision(decision="continue").next_action == "analyze_match"
        assert AgentDecision(decision="retry").next_action == "rewrite_query"
        assert AgentDecision(decision="fallback").next_action == "end"

    def test_to_dict_roundtrip(self):
        d = AgentDecision(decision="retry", reason="keyword coverage 0.3")
        restored = AgentDecision.from_dict(d.to_dict())
        assert restored.decision == "retry"
        assert restored.reason == "keyword coverage 0.3"


# ---------------------------------------------------------------------------
# ToolCallTrace
# ---------------------------------------------------------------------------


class TestToolCallTrace:
    def test_construct(self):
        t = ToolCallTrace(
            tool_name="parse_jd_tool",
            input_summary="jd text 500 chars",
            output_summary="parsed Python, LangGraph",
            duration_ms=12.5,
            success=True,
            state_changes=["parsed_jd set"],
        )
        assert t.tool_name == "parse_jd_tool"
        assert t.duration_ms == 12.5
        assert t.success is True
        assert t.state_changes == ["parsed_jd set"]

    def test_failed_tool(self):
        t = ToolCallTrace(
            tool_name="retrieve_tool",
            input_summary="query",
            duration_ms=100,
            success=False,
            error="Network timeout",
        )
        assert t.success is False
        assert t.error == "Network timeout"

    def test_to_dict_roundtrip(self):
        t = ToolCallTrace(
            tool_name="grade_tool",
            input_summary="5 chunks",
            output_summary="grade=good",
            duration_ms=3.0,
            success=True,
            state_changes=["retrieval_scores set"],
        )
        restored = ToolCallTrace.from_dict(t.to_dict())
        assert restored.tool_name == "grade_tool"
        assert restored.state_changes == ["retrieval_scores set"]


# ---------------------------------------------------------------------------
# WorkflowTrace
# ---------------------------------------------------------------------------


class TestWorkflowTrace:
    def test_construct_empty(self):
        wt = WorkflowTrace(trace_id="abc123")
        assert wt.trace_id == "abc123"
        assert wt.tool_traces == []
        assert wt.status == "running"

    def test_aggregate_tool_traces(self):
        t1 = ToolCallTrace(
            tool_name="parse", input_summary="x", duration_ms=10, success=True,
        )
        t2 = ToolCallTrace(
            tool_name="retrieve", input_summary="y", duration_ms=20, success=True,
        )
        wt = WorkflowTrace(trace_id="t1", tool_traces=[t1, t2])
        assert len(wt.tool_traces) == 2
        assert wt.total_duration_ms == 30.0

    def test_final_decision(self):
        wt = WorkflowTrace(trace_id="t1", final_decision="continue", status="completed")
        assert wt.final_decision == "continue"
        assert wt.status == "completed"

    def test_to_dict_roundtrip(self):
        t = ToolCallTrace(
            tool_name="parse", input_summary="x", duration_ms=5, success=True,
        )
        wt = WorkflowTrace(
            trace_id="t1",
            tool_traces=[t],
            final_decision="continue",
            status="completed",
        )
        d = wt.to_dict()
        restored = WorkflowTrace.from_dict(d)
        assert restored.trace_id == "t1"
        assert len(restored.tool_traces) == 1
        assert restored.tool_traces[0].tool_name == "parse"
