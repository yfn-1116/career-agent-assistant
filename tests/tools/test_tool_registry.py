"""Tests for Tool Registry and Tool abstraction."""

import pytest

from career_agent.tools.base import Tool, ToolResult
from career_agent.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------


class TestToolResult:
    def test_success(self):
        r = ToolResult(success=True, output={"key": "val"}, summary="done")
        assert r.success
        assert r.output == {"key": "val"}
        assert r.error == ""

    def test_failure(self):
        r = ToolResult(success=False, output={}, error="something broke", summary="fail")
        assert not r.success
        assert r.error == "something broke"

    def test_to_dict(self):
        r = ToolResult(success=True, output={"a": 1}, summary="ok", duration_ms=12.5)
        d = r.to_dict()
        assert d["success"] is True
        assert d["output"] == {"a": 1}
        assert d["error"] == ""
        assert d["duration_ms"] == 12.5


# ---------------------------------------------------------------------------
# Tool ABC
# ---------------------------------------------------------------------------


class _DummyTool(Tool):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def description(self) -> str:
        return "A dummy tool for testing"

    def run(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output=kwargs, summary=f"dummy ran with {len(kwargs)} args")


class TestToolABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            Tool()

    def test_dummy_tool_has_all_fields(self):
        t = _DummyTool()
        assert t.name == "dummy"
        assert t.description == "A dummy tool for testing"
        assert isinstance(t.input_schema, dict)
        assert isinstance(t.output_schema, dict)
        assert isinstance(t.safety_notes, list)

    def test_dummy_tool_runs(self):
        t = _DummyTool()
        result = t.run(x=1, y=2)
        assert result.success
        assert result.output == {"x": 1, "y": 2}


# ---------------------------------------------------------------------------
# ToolRegistry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        t = _DummyTool()
        reg.register(t)
        assert reg.get("dummy") is t
        assert "dummy" in reg.list_tools()

    def test_register_duplicate_raises(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(_DummyTool())

    def test_get_unknown_raises(self):
        reg = ToolRegistry()
        with pytest.raises(KeyError, match="Tool 'unknown' not found"):
            reg.get("unknown")

    def test_list_tools(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        names = reg.list_tools()
        assert "dummy" in names

    def test_has(self):
        reg = ToolRegistry()
        reg.register(_DummyTool())
        assert reg.has("dummy")
        assert not reg.has("nonexistent")

    def test_tool_count(self):
        reg = ToolRegistry()
        assert reg.tool_count == 0
        reg.register(_DummyTool())
        assert reg.tool_count == 1


# ---------------------------------------------------------------------------
# Required tools
# ---------------------------------------------------------------------------


REQUIRED_TOOLS = [
    "parse_jd", "plan_queries", "rewrite_query", "retrieve_profile",
    "rerank_chunks", "grade_retrieval", "select_evidence",
    "analyze_match", "generate_grounded_answer", "check_faithfulness",
    "fallback", "write_report", "write_diagnostics",
    "web_search", "github_repo",
]


class TestRequiredTools:
    def test_all_required_tools_exist(self):
        """Every standard tool must be importable and constructable."""
        from career_agent.tools.registry import create_standard_registry
        reg = create_standard_registry()
        for name in REQUIRED_TOOLS:
            assert reg.has(name), f"Missing required tool: {name}"
            tool = reg.get(name)
            assert tool.name == name
            assert isinstance(tool.description, str) and len(tool.description) > 0
            assert isinstance(tool.safety_notes, list)

    def test_all_tools_run(self):
        """Each tool should run without crashing on minimal input."""
        from career_agent.tools.registry import create_standard_registry
        reg = create_standard_registry()
        # parse_jd needs raw_jd
        r = reg.get("parse_jd").run(raw_jd="# Test JD\nPython, FastAPI")
        assert r.success or r.error  # at least returns a result

        # plan_queries needs parsed_jd
        from career_agent.domain.schemas import ParsedJD
        r = reg.get("plan_queries").run(
            parsed_jd=ParsedJD(job_direction="agent", hard_skills=["Python"])
        )
        assert r.success

        # retrieve_profile needs queries + profile_dir
        r = reg.get("retrieve_profile").run(queries=["Python"], top_k=3, profile_dir="data/samples/profile")
        assert r.success

        # grade_retrieval needs evidence
        from career_agent.rag.schemas import RetrievedEvidence
        ev = RetrievedEvidence(
            evidence_id="ev-1", chunk_id="c1", content="Python RAG", score=0.8,
            source_path="test.md", matched_keywords=["Python"],
        )
        r = reg.get("grade_retrieval").run(
            query="Python", evidence=[ev], parsed_jd=None, top_k=3,
        )
        assert r.success

        # fallback
        r = reg.get("fallback").run(
            missing_keywords=["Kubernetes"], retry_count=2, max_retries=2,
            output_dir="/tmp",
        )
        assert r.success
        assert "fallback" in str(r.output.get("decision", "")).lower()

    def test_unknown_tool_rejected(self):
        """Calling an unregistered tool must fail clearly."""
        reg = ToolRegistry()
        with pytest.raises(KeyError):
            reg.get("not_registered")
