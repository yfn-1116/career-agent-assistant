"""Tests for lightweight evaluation rules."""

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
from career_agent.evaluation.rules import (
    evaluate_evidence_count,
    evaluate_evidence_refs,
    evaluate_generated_output_non_empty,
    evaluate_keyword_coverage,
    evaluate_no_empty_status,
    evaluate_state,
)
from career_agent.evaluation.schemas import EvaluationItem, EvaluationReport
from career_agent.rag.schemas import RetrievedEvidence


def _make_evidence(ev_id: str = "ev-1") -> RetrievedEvidence:
    return RetrievedEvidence(
        evidence_id=ev_id,
        chunk_id="c-1",
        title="Test",
        content="test content",
        score=0.8,
        source_path="/data/test.md",
        matched_keywords=["Python"],
    )


def _make_state(**kw) -> AgentTaskState:
    defaults = {
        "status": "completed",
        "error_message": "",
        "parsed_jd": ParsedJD(
            hard_skills=["Python"],
            keywords=["Python", "RAG"],
        ),
        "retrieved_evidence": [_make_evidence("ev-1")],
        "generated_output": GeneratedOutput(
            summary="Test summary",
            resume_bullets=["- bullet 1"],
            communication_message="Hello",
            evidence_refs=["ev-1"],
        ),
    }
    defaults.update(kw)
    return AgentTaskState(**defaults)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    def test_evaluation_item_defaults(self):
        item = EvaluationItem()
        assert item.name == ""
        assert not item.passed
        assert item.score == 0.0

    def test_evaluation_report_defaults(self):
        report = EvaluationReport()
        assert report.case_id == ""
        assert report.total_score == 0.0
        assert report.items == []

    def test_lists_not_shared(self):
        r1 = EvaluationReport()
        r2 = EvaluationReport()
        r1.items.append(EvaluationItem(name="test"))
        assert r2.items == []


# ---------------------------------------------------------------------------
# Rule tests
# ---------------------------------------------------------------------------

class TestNoEmptyStatus:
    def test_completed_passes(self):
        state = _make_state(status="completed")
        item = evaluate_no_empty_status(state)
        assert item.passed
        assert item.score == 1.0

    def test_failed_fails(self):
        state = _make_state(status="failed", error_message="test error")
        item = evaluate_no_empty_status(state)
        assert not item.passed


class TestEvidenceCount:
    def test_with_evidence_passes(self):
        state = _make_state()
        item = evaluate_evidence_count(state)
        assert item.passed

    def test_empty_evidence_fails(self):
        state = _make_state(retrieved_evidence=[])
        item = evaluate_evidence_count(state)
        assert not item.passed


class TestGeneratedOutputNonEmpty:
    def test_full_output_passes(self):
        state = _make_state()
        item = evaluate_generated_output_non_empty(state)
        assert item.passed
        assert item.score == 1.0

    def test_none_output_fails(self):
        state = _make_state(generated_output=None)
        item = evaluate_generated_output_non_empty(state)
        assert not item.passed


class TestEvidenceRefs:
    def test_valid_refs_pass(self):
        state = _make_state()
        item = evaluate_evidence_refs(state)
        assert item.passed
        assert item.score == 1.0

    def test_missing_refs_fail(self):
        state = _make_state(
            generated_output=GeneratedOutput(
                summary="s", evidence_refs=[]
            )
        )
        item = evaluate_evidence_refs(state)
        assert not item.passed


class TestKeywordCoverage:
    def test_partial_coverage(self):
        state = _make_state()
        item = evaluate_keyword_coverage(state)
        assert item.passed
        assert 0 < item.score <= 1.0

    def test_no_jd_keywords(self):
        state = _make_state(
            parsed_jd=ParsedJD(hard_skills=[], keywords=[]),
        )
        item = evaluate_keyword_coverage(state)
        assert item.passed
        assert item.score == 1.0

    def test_null_parsed_jd(self):
        state = _make_state(parsed_jd=None)
        item = evaluate_keyword_coverage(state)
        assert not item.passed


class TestEvaluateState:
    def test_returns_evaluation_report(self):
        state = _make_state()
        report = evaluate_state(state, case_id="test-1", job_file="test.md")
        assert isinstance(report, EvaluationReport)
        assert report.case_id == "test-1"

    def test_total_score_between_0_and_1(self):
        state = _make_state()
        report = evaluate_state(state)
        assert 0.0 <= report.total_score <= 1.0

    def test_summary_contains_case_id(self):
        report = evaluate_state(_make_state(), case_id="abc")
        assert "abc" in report.summary

    def test_no_external_dependencies(self):
        report = evaluate_state(_make_state())
        assert report.total_score > 0
