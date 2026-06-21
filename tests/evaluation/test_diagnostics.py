"""Tests for diagnostics writer and eval runner."""

import json
import tempfile
from pathlib import Path

from career_agent.evaluation.diagnostics import write_diagnostics
from career_agent.rag.grading import RetrievalGradeReport


def test_diagnostics_json_created():
    state = {
        "trace_id": "test123",
        "raw_jd": "# Test JD",
        "parsed_jd": None,
        "queries": ["Python Agent"],
        "retrieved_chunks": [],
        "retrieval_scores": RetrievalGradeReport(
            query="test", top_k=3, evidence_count=2, average_score=0.6,
            keyword_coverage=0.5, source_diversity=2, grade="good",
            metadata={"total_score": 0.75},
        ),
        "retry_history": [
            {"round": 1, "query": "q1", "top_k": 3, "evidence_count": 2,
             "total_score": 0.45, "grade": "weak", "decision": "retry",
             "missing_keywords": ["LangGraph"]},
        ],
        "missing_keywords": ["LangGraph"],
        "decision": "continue",
        "fallback_reason": "",
        "match_analysis": None,
        "generated_result": None,
        "retry_count": 1,
        "status": "completed",
        "report_path": "/tmp/report.md",
    }

    with tempfile.TemporaryDirectory() as tmp:
        path = write_diagnostics(state, output_dir=tmp)
        assert path.is_file()
        data = json.loads(path.read_text())
        assert data["trace_id"] == "test123"
        assert data["retrieval_scores"]["grade"] == "good"
        assert len(data["retry_history"]) == 1
        assert data["retry_history"][0]["total_score"] == 0.45


def test_diagnostics_contains_retry_history():
    state = {
        "trace_id": "retry_test",
        "raw_jd": "test",
        "queries": ["q1", "q2"],
        "retrieved_chunks": [],
        "retrieval_scores": RetrievalGradeReport(
            query="q2", top_k=3, evidence_count=3, average_score=0.7,
            keyword_coverage=0.6, source_diversity=3, grade="good",
            metadata={"total_score": 0.75},
        ),
        "retry_history": [
            {"round": 1, "query": "q1", "top_k": 3, "evidence_count": 1,
             "total_score": 0.40, "grade": "weak", "decision": "retry",
             "missing_keywords": ["LangGraph"]},
            {"round": 2, "query": "q2", "top_k": 3, "evidence_count": 3,
             "total_score": 0.75, "grade": "good", "decision": "continue",
             "missing_keywords": []},
        ],
        "missing_keywords": [],
        "decision": "continue",
        "fallback_reason": "",
        "match_analysis": None,
        "generated_result": None,
        "retry_count": 2,
        "status": "completed",
        "report_path": "/tmp/r.md",
    }

    with tempfile.TemporaryDirectory() as tmp:
        path = write_diagnostics(state, output_dir=tmp)
        data = json.loads(path.read_text())
        assert len(data["retry_history"]) == 2
        assert data["retry_count"] == 2
        assert data["decision"] == "continue"


def test_eval_dataset_exists():
    """The eval dataset must exist and be valid JSONL."""
    dataset = Path(__file__).resolve().parents[2] / "data" / "eval" / "jd_cases.jsonl"
    assert dataset.is_file(), f"Missing eval dataset at {dataset}"
    cases = []
    with open(dataset) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    assert len(cases) >= 8
    for case in cases:
        assert "case_id" in case
        assert "jd_text" in case
        assert "expected_skills" in case


def test_diagnostics_handles_none_values():
    state = {
        "trace_id": "none_test",
        "raw_jd": "",
        "queries": [],
        "retrieved_chunks": [],
        "retrieval_scores": None,
        "retry_history": [],
        "missing_keywords": [],
        "decision": "fallback",
        "fallback_reason": "no evidence",
        "match_analysis": None,
        "generated_result": None,
        "retry_count": 0,
        "status": "completed",
        "report_path": "",
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = write_diagnostics(state, output_dir=tmp)
        data = json.loads(path.read_text())
        assert data["retrieval_scores"] is None
        assert data["decision"] == "fallback"
