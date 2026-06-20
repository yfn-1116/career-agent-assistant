"""Tests for JobMatchWorkflow."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from career_agent.agents.state import AgentTaskState
from career_agent.workflows.job_match_workflow import JobMatchWorkflow


def _read_sample_jd(name: str) -> str:
    return (Path("data/samples/jobs") / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWorkflowInit:
    def test_can_initialize(self):
        wf = JobMatchWorkflow()
        assert wf.jd_parser is not None
        assert wf.rag_retrieve_agent is not None
        assert wf.match_analysis_agent is not None
        assert wf.build_agent is not None

    def test_can_ingest_profile_dir(self):
        wf = JobMatchWorkflow(profile_dir="data/samples/profile")
        assert wf.rag_pipeline.count() > 0


class TestWorkflowRun:
    @pytest.fixture(autouse=True)
    def _setup(self):
        self.wf = JobMatchWorkflow(profile_dir="data/samples/profile")

    def test_run_agent_intern_jd(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        assert isinstance(state, AgentTaskState)
        assert state.status == "completed"

    def test_parsed_jd_not_empty(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        assert state.parsed_jd is not None
        assert state.parsed_jd.job_title != ""

    def test_retrieved_evidence_is_list(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        assert isinstance(state.retrieved_evidence, list)

    def test_match_analysis_not_empty(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        assert state.match_analysis is not None

    def test_generated_output_not_empty(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        assert state.generated_output is not None
        assert len(state.generated_output.summary) > 0

    def test_evidence_refs_not_fabricated(self):
        jd_text = _read_sample_jd("agent_intern_jd.md")
        state = self.wf.run(jd_text, top_k=5)

        refs = state.generated_output.evidence_refs
        assert isinstance(refs, list)
        # Refs should match what retrieval returned
        ev_ids = {ev.evidence_id for ev in state.retrieved_evidence}
        for ref in refs:
            assert ref in ev_ids

    def test_empty_jd_does_not_crash(self):
        state = self.wf.run("", top_k=5)
        assert isinstance(state, AgentTaskState)
        assert state.status in ("completed", "failed")

    def test_no_external_dependencies(self):
        jd_text = _read_sample_jd("rag_engineer_intern_jd.md")
        state = self.wf.run(jd_text, top_k=3)
        assert state.status == "completed"

    def test_run_all_four_jds(self):
        for jd_file in [
            "agent_intern_jd.md",
            "rag_engineer_intern_jd.md",
            "ai_application_intern_jd.md",
            "backend_ai_intern_jd.md",
        ]:
            jd_text = _read_sample_jd(jd_file)
            state = self.wf.run(jd_text, top_k=3)
            assert state.status == "completed", f"Failed on {jd_file}"
            assert state.generated_output is not None, f"No output for {jd_file}"
