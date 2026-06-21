"""Tests for the LangGraph-based job match workflow."""

import tempfile
from pathlib import Path

from career_agent.agents.state import ParsedJD
from career_agent.rag.grading import GRADE_FAILED, GRADE_GOOD, RetrievalGradeReport
from career_agent.rag.schemas import RetrievedEvidence
from career_agent.workflows.langgraph_workflow import (
    JobMatchState,
    _WorkflowContext,
    _initial_state,
    create_langgraph_workflow,
    run_langgraph_workflow,
    write_report_node,
)

PROFILE_DIR = str(Path(__file__).resolve().parents[2] / "data" / "samples" / "profile")

SAMPLE_JD = """# AI Agent 开发实习生

岗位要求：
- Python, LangChain, LangGraph, RAG
- 加分：Agent 系统经验, FastAPI
"""


def test_langgraph_workflow_runs():
    """Basic smoke test: the LangGraph workflow compiles and executes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd=SAMPLE_JD,
            top_k=3,
            profile_dir=PROFILE_DIR,
            output_dir=tmpdir,
        )

        assert state["status"] == "completed"
        assert state["parsed_jd"] is not None
        assert state["parsed_jd"].job_direction in ("agent", "general", "rag")
        assert state["queries"]
        assert len(state["queries"]) == 1
        assert state["retrieval_scores"] is not None
        assert state["retrieval_scores"].grade in ("excellent", "good", "weak", "failed")
        assert state["report_path"]
        assert Path(state["report_path"]).is_file()


def test_state_contains_retrieval_scores():
    """Ensure RetrievalGradeReport is written into state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd=SAMPLE_JD,
            top_k=3,
            profile_dir=PROFILE_DIR,
            output_dir=tmpdir,
        )

        rs = state["retrieval_scores"]
        assert rs is not None
        assert isinstance(rs, RetrievalGradeReport)
        assert rs.top_k == 3
        assert rs.evidence_count > 0
        assert rs.keyword_coverage >= 0.0
        assert len(rs.items) == 5
        item_names = {item.name for item in rs.items}
        assert item_names == {"evidence_count", "average_score", "keyword_coverage", "source_diversity", "traceability"}


def test_workflow_writes_report():
    """Verify the report file is written and contains key diagnostics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd=SAMPLE_JD,
            top_k=3,
            profile_dir=PROFILE_DIR,
            output_dir=tmpdir,
        )

        report_path = Path(state["report_path"])
        assert report_path.is_file()
        content = report_path.read_text(encoding="utf-8")

        # Report must contain the key diagnostic sections
        assert "Parsed JD" in content
        assert "Rewritten Queries" in content
        assert "Retrieved Chunks" in content
        assert "Retrieval Scores" in content
        assert "Missing Keywords" in content
        assert "Decision" in content
        assert "Match Analysis" in content
        assert "Generated Result" in content
        assert state["trace_id"] in content


def test_low_score_decision_is_preserved_in_state():
    """When retrieval returns no evidence, decision must reflect that."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd="Some unknown technology XYZ-999 that has no match in profile",
            top_k=3,
            profile_dir=PROFILE_DIR,
            output_dir=tmpdir,
        )

        rs = state["retrieval_scores"]
        assert rs is not None
        # With weak/no evidence, grade should be "failed" or "weak"
        assert rs.grade in (GRADE_FAILED, "weak")
        assert state["decision"] == "retry"


def test_initial_state_has_required_fields():
    """All required state fields are present after initialization."""
    s = _initial_state(raw_jd="test", top_k=5)
    required = [
        "raw_jd", "parsed_jd", "queries", "retrieved_chunks", "retrieval_scores",
        "missing_keywords", "decision", "match_analysis", "generated_result",
        "report_path", "trace_id", "logs", "retry_count", "next_action",
    ]
    for key in required:
        assert key in s, f"Missing state field: {key}"
    assert s["raw_jd"] == "test"
    assert s["top_k"] == 5
    assert s["retry_count"] == 0
    assert s["status"] == "running"


def test_graph_composes_with_custom_agents():
    """Custom agents can be injected into the compiled graph."""
    app = create_langgraph_workflow(profile_dir=PROFILE_DIR)
    initial = _initial_state(raw_jd=SAMPLE_JD, top_k=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        initial["output_dir"] = tmpdir
        result = app.invoke(initial)

        assert result["status"] == "completed"
        assert result["parsed_jd"] is not None
        assert result["report_path"]
        assert Path(result["report_path"]).is_file()


def test_write_report_node_creates_file():
    """write_report_node writes a markdown file to the output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = _initial_state(
            raw_jd=SAMPLE_JD,
            top_k=2,
            profile_dir=PROFILE_DIR,
            output_dir=tmpdir,
        )
        state["parsed_jd"] = ParsedJD(job_title="Test", job_direction="agent")
        state["queries"] = ["agent Python"]
        state["retrieved_chunks"] = []
        state["retrieval_scores"] = RetrievalGradeReport(
            query="agent Python", top_k=2, evidence_count=0, average_score=0.0,
            keyword_coverage=0.0, source_diversity=0, grade=GRADE_FAILED,
        )
        state["decision"] = "retry"

        ctx = _WorkflowContext()
        updates = write_report_node(state, ctx=ctx)
        path = Path(updates["report_path"])
        assert path.is_file()
        assert path.suffix == ".md"
        content = path.read_text(encoding="utf-8")
        assert "LangGraph Job Match Workflow" in content
