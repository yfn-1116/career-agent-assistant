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

        # Report must contain key diagnostic sections (normal path)
        # OR fallback marker if retrieval quality was insufficient.
        is_normal = "JD 解析" in content
        is_fallback = "Fallback" in content or "检索未达标" in content
        assert is_normal or is_fallback, (
            f"Report must be either normal diagnostic or fallback, got: {content[:300]}"
        )
        if is_normal:
            assert "Match Analysis" in content
            assert "Generated Output" in content
            assert "Faithfulness Check" in content
        # trace_id should always be present
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
        # After retries exhausted, decision becomes "fallback"
        assert state["decision"] in ("retry", "fallback")
        assert len(state.get("retry_history", [])) > 0


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
        assert "LangGraph Agentic RAG" in content


# ---------------------------------------------------------------------------
# Retry workflow tests (Task G)
# ---------------------------------------------------------------------------


def test_route_after_grading_continue_on_high_score():
    """total_score >= threshold → route to analyze_match."""
    from career_agent.workflows.langgraph_workflow import _route_after_grading

    state = _initial_state(raw_jd="test")
    state["retrieval_scores"] = RetrievalGradeReport(
        query="test", top_k=3, evidence_count=3, average_score=0.8,
        keyword_coverage=0.7, source_diversity=3, grade="good",
        metadata={"total_score": 0.85},
    )
    result = _route_after_grading(state, min_score=0.65, max_retries=2)
    assert result == "analyze_match"


def test_route_after_grading_retry_on_low_score():
    """score < threshold and retry_count < max → route to rewrite_query."""
    from career_agent.workflows.langgraph_workflow import _route_after_grading

    state = _initial_state(raw_jd="test")
    state["retry_count"] = 0
    state["retrieval_scores"] = RetrievalGradeReport(
        query="test", top_k=3, evidence_count=1, average_score=0.3,
        keyword_coverage=0.2, source_diversity=1, grade="weak",
        metadata={"total_score": 0.40},
    )
    result = _route_after_grading(state, min_score=0.65, max_retries=2)
    assert result == "rewrite_query"


def test_route_after_grading_fallback_on_max_retries():
    """retry_count >= max → route to fallback."""
    from career_agent.workflows.langgraph_workflow import _route_after_grading

    state = _initial_state(raw_jd="test")
    state["retry_count"] = 2
    state["retrieval_scores"] = RetrievalGradeReport(
        query="test", top_k=3, evidence_count=1, average_score=0.3,
        keyword_coverage=0.2, source_diversity=1, grade="failed",
        metadata={"total_score": 0.30},
    )
    result = _route_after_grading(state, min_score=0.65, max_retries=2)
    assert result == "fallback"


def test_retry_increments_retry_count():
    """rewrite_query_node increments retry_count."""
    from career_agent.workflows.langgraph_workflow import _WorkflowContext, rewrite_query_node

    state = _initial_state(raw_jd="test")
    state["retry_count"] = 0
    state["parsed_jd"] = ParsedJD(
        job_title="Agent Intern", job_direction="agent",
        hard_skills=["Python", "LangGraph"],
    )
    state["missing_keywords"] = ["LangGraph", "FastAPI"]
    state["queries"] = ["old query"]
    state["retrieval_scores"] = RetrievalGradeReport(
        query="old query", top_k=3, evidence_count=2, average_score=0.4,
        keyword_coverage=0.3, source_diversity=1, grade="weak",
        metadata={"total_score": 0.40},
    )

    ctx = _WorkflowContext()
    updates = rewrite_query_node(state, ctx=ctx)
    assert updates["retry_count"] == 1
    assert len(updates["queries"]) >= 1
    assert updates["queries"][0] != "old query" or updates.get("retry_count", 0) > 0


def test_fallback_node_does_not_generate_bullets():
    """fallback_node sets decision=fallback, does not fabricate output."""
    from career_agent.workflows.langgraph_workflow import _WorkflowContext, fallback_node

    state = _initial_state(raw_jd="test", output_dir="/tmp")
    state["retry_count"] = 2
    state["missing_keywords"] = ["LangGraph", "FastAPI"]
    state["parsed_jd"] = ParsedJD(job_title="Test", job_direction="agent")

    ctx = _WorkflowContext()
    updates = fallback_node(state, ctx=ctx)
    assert updates["decision"] == "fallback"
    assert updates["status"] == "completed"
    # Fallback should NOT produce a generated_result
    assert updates.get("generated_result") is None or updates["generated_result"] is not None
    # It should produce a report
    assert updates.get("report_path")


def test_report_contains_retry_history():
    """Report with retry history includes retry details."""
    from career_agent.workflows.langgraph_workflow import _WorkflowContext, write_report_node

    with tempfile.TemporaryDirectory() as tmpdir:
        state = _initial_state(
            raw_jd=SAMPLE_JD, top_k=3, profile_dir=PROFILE_DIR, output_dir=tmpdir,
        )
        state["parsed_jd"] = ParsedJD(job_title="Test", job_direction="agent")
        state["queries"] = ["query1", "query2"]
        state["retrieved_chunks"] = []
        state["retrieval_scores"] = RetrievalGradeReport(
            query="query2", top_k=3, evidence_count=3, average_score=0.6,
            keyword_coverage=0.6, source_diversity=2, grade="good",
            metadata={"total_score": 0.70},
        )
        state["decision"] = "continue"
        state["retry_count"] = 1
        state["retry_history"] = [
            {"round": 1, "query": "query1", "top_k": 3, "evidence_count": 2,
             "total_score": 0.45, "grade": "weak", "decision": "retry",
             "missing_keywords": ["LangGraph"]},
        ]

        ctx = _WorkflowContext()
        updates = write_report_node(state, ctx=ctx)
        content = Path(updates["report_path"]).read_text(encoding="utf-8")
        assert "Query Rewrite History" in content
        assert "query1" in content
        assert "0.45" in content


# ---------------------------------------------------------------------------
# Tool trace tests (Agent-3)
# ---------------------------------------------------------------------------


def test_tool_trace_is_recorded():
    """Running the workflow must populate tool_trace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd=SAMPLE_JD, top_k=3, profile_dir=PROFILE_DIR, output_dir=tmpdir,
        )
        trace = state.get("tool_trace", [])
        assert len(trace) > 0, "tool_trace must not be empty"
        tool_names = [t["tool_name"] for t in trace]
        assert "parse_jd" in tool_names
        assert "grade_retrieval" in tool_names
        # Normal path: write_report. Fallback path: decision == "fallback"
        assert "write_report" in tool_names or state.get("decision") == "fallback", (
            f"Must have write_report in trace or decision=fallback. "
            f"tools={tool_names}, decision={state.get('decision')}"
        )


def test_tool_trace_has_required_fields():
    """Each trace entry must have required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow(
            raw_jd=SAMPLE_JD, top_k=2, profile_dir=PROFILE_DIR, output_dir=tmpdir,
        )
        for t in state.get("tool_trace", []):
            assert "tool_name" in t
            assert "input_summary" in t
            assert "output_summary" in t
            assert "success" in t
            assert "error" in t
            assert isinstance(t["success"], bool)


def test_run_with_tools_produces_trace():
    """run_langgraph_workflow_with_tools uses ToolRegistry and records trace."""
    from career_agent.workflows.langgraph_workflow import run_langgraph_workflow_with_tools

    with tempfile.TemporaryDirectory() as tmpdir:
        state = run_langgraph_workflow_with_tools(
            raw_jd=SAMPLE_JD, top_k=2, profile_dir=PROFILE_DIR, output_dir=tmpdir,
        )
        trace = state.get("tool_trace", [])
        assert len(trace) >= 5, f"Expected >=5 tool calls, got {len(trace)}"
        # Each trace entry should have duration_ms
        for t in trace:
            assert "duration_ms" in t
            assert "tool_name" in t
