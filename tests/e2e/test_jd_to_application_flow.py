"""End-to-end pipeline test — JD → Parse → Retrieve → Analyze → Generate → Message.

Runs the full pipeline without real network or real LLM:
- Uses tempfile.TemporaryDirectory with MemoryVectorStore for RAG
- Uses real JDParserAgent, MatchAnalysisAgent, BuildAgent (rule-based)
- Uses real MessageAgent for communication scripts
- Verifies structural invariants (not exact text)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import GeneratedOutput, MatchAnalysisResult
from career_agent.messages.agent import MessageAgent, MessageDraft
from career_agent.rag.pipeline import RAGPipeline
from tests.fixtures.realistic_jobs import JOBS
from tests.fixtures.user_profile import PROFILE_ITEMS


def _write_profile_files(temp_dir: Path) -> None:
    """Write realistic profile markdown files from PROFILE_ITEMS into temp_dir."""
    for item in PROFILE_ITEMS:
        tags = ", ".join(item.metadata.get("tags", []))
        source_url = item.metadata.get("source_url", "")
        content = f"""# {item.title}

## 项目信息
- 状态：{item.status}
- 置信度：{item.confidence}
- 技术栈：{', '.join(item.skills)}
- Tags：{tags}
- 来源：{source_url}

## 详细描述
{item.raw_content or '（无详细描述）'}

## 可支撑的 Claims
{chr(10).join(f'- {c}' for c in item.claims)}
"""
        filename = f"{item.item_id}.md"
        (temp_dir / filename).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Full pipeline fixture
# ---------------------------------------------------------------------------


class TestFullPipelineE2E:
    """End-to-end: JD → Parse → Retrieve → Analyze → Generate → Message."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        _write_profile_files(Path(self.temp_dir.name))
        self.pipeline = RAGPipeline()
        self.pipeline.build_index(self.temp_dir.name)
        self.parser = JDParserAgent()
        self.retriever = RAGRetrieveAgent(pipeline=self.pipeline)
        self.analyzer = MatchAnalysisAgent()
        self.builder = BuildAgent()
        self.messenger = MessageAgent()

    def teardown_method(self):
        self.temp_dir.cleanup()

    # -- Full flow ----------------------------------------------------------

    def test_agent_jd_full_flow_produces_all_outputs(self):
        """Agent JD should produce parse/retrieve/analyze/generate/message."""
        jd = JOBS["agent_intern"]

        # Step 1: parse
        parsed = self.parser.parse(jd.raw_text)
        assert parsed.job_title != "", "Parsed JD must have a title"
        assert parsed.job_direction == "agent", (
            f"Expected direction=agent, got {parsed.job_direction}"
        )

        # Step 2: retrieve
        evidence = self.retriever.retrieve(parsed, top_k=5)
        assert len(evidence) > 0, "Should retrieve at least one evidence item"

        # Step 3: analyze
        analysis = self.analyzer.analyze(parsed, evidence)
        assert isinstance(analysis, MatchAnalysisResult)
        assert len(analysis.strengths) + len(analysis.weaknesses) > 0, (
            "Must have at least one strength or weakness"
        )

        # Step 4: generate bullets
        output = self.builder.build(parsed, evidence, analysis)
        assert isinstance(output, GeneratedOutput)
        assert len(output.resume_bullets) > 0, "Must generate at least one bullet"
        assert len(output.summary) > 0, "Must generate a summary"

        # Step 5: generate BOSS message
        msg = self.messenger.generate(
            message_type="boss_greeting",
            job_title=parsed.job_title,
            matched_skills=list(analysis.matched_keywords)[:5],
            strengths=analysis.strengths[:3],
            evidence_paths=[ev.source_path for ev in evidence],
        )
        assert isinstance(msg, MessageDraft)
        assert len(msg.text) > 0, "BOSS message must not be empty"

    # -- No fabrication -----------------------------------------------------

    def test_evidence_refs_match_retrieved_evidence(self):
        """Every evidence_ref in generated output must correspond to an
        actual retrieved evidence ID."""
        jd = JOBS["agent_intern"]
        parsed = self.parser.parse(jd.raw_text)
        evidence = self.retriever.retrieve(parsed, top_k=5)
        analysis = self.analyzer.analyze(parsed, evidence)
        output = self.builder.build(parsed, evidence, analysis)

        ev_ids = {ev.evidence_id for ev in evidence}
        for ref in output.evidence_refs:
            assert ref in ev_ids, (
                f"Fabricated evidence ref '{ref}' not in retrieved IDs: {ev_ids}"
            )

    # -- All JD types complete without crash ---------------------------------

    @pytest.mark.parametrize("jd_key", sorted(JOBS.keys()))
    def test_all_jd_types_complete_without_crash(self, jd_key):
        """Every JD fixture must complete the full pipeline without exception."""
        jd = JOBS[jd_key]
        parsed = self.parser.parse(jd.raw_text)
        evidence = self.retriever.retrieve(parsed, top_k=5)
        analysis = self.analyzer.analyze(parsed, evidence)
        output = self.builder.build(parsed, evidence, analysis)

        assert output.summary != "", f"{jd_key}: summary must not be empty"
        assert isinstance(output, GeneratedOutput)

        # For JDs yielding zero evidence, output must be conservative
        if len(evidence) == 0:
            joined = " ".join(output.resume_bullets)
            conservative = "不足" in joined or "暂无" in joined or "补充" in joined
            assert conservative, (
                f"{jd_key}: no-evidence output should be conservative, "
                f"got: {joined[:200]}"
            )

    # -- Message agent all platforms ----------------------------------------

    @pytest.mark.parametrize("msg_type", [
        "boss_greeting", "email_intro", "hr_reply", "follow_up",
    ])
    def test_message_agent_all_platforms_with_evidence(self, msg_type):
        """All four message types generate valid output with evidence."""
        msg = self.messenger.generate(
            message_type=msg_type,
            job_title="AI Agent 开发实习生",
            matched_skills=["Python", "RAG", "LangGraph"],
            strengths=["具备 Python 相关经验"],
            evidence_paths=["projects/career-agent-assistant.md"],
            hr_question="请问你有相关项目经验吗？",
        )
        assert len(msg.text) > 0, f"{msg_type}: message must not be empty"

    @pytest.mark.parametrize("msg_type", [
        "boss_greeting", "email_intro", "hr_reply", "follow_up",
    ])
    def test_message_agent_without_evidence_still_works(self, msg_type):
        """Without evidence, messages should still generate but include warnings."""
        msg = self.messenger.generate(message_type=msg_type)
        assert len(msg.text) > 0, f"{msg_type}: message must not be empty"
        # Without evidence, should have risk warnings
        assert msg.risk_warnings, (
            f"{msg_type}: without evidence should have risk warnings"
        )

    # -- Structural output checks -------------------------------------------

    def test_output_metadata_contains_constraints(self):
        """BuildAgent output metadata must include constraint categories."""
        jd = JOBS["agent_intern"]
        parsed = self.parser.parse(jd.raw_text)
        evidence = self.retriever.retrieve(parsed, top_k=5)
        analysis = self.analyzer.analyze(parsed, evidence)
        output = self.builder.build(parsed, evidence, analysis)

        meta = output.metadata
        assert "can_write_claims" in meta, "Must have can_write_claims"
        assert "needs_confirmation_claims" in meta, "Must have needs_confirmation_claims"
        assert "learning_plan_claims" in meta, "Must have learning_plan_claims"
        assert "warnings" in meta, "Must have warnings list"
        assert "bullet_evidence_map" in meta, "Must have bullet_evidence_map"

        # bullet_evidence_map should have one entry per bullet
        assert len(meta["bullet_evidence_map"]) == len(output.resume_bullets), (
            f"bullet_evidence_map count ({len(meta['bullet_evidence_map'])}) "
            f"must match bullets count ({len(output.resume_bullets)})"
        )

    def test_communication_message_not_empty_for_agent_jd(self):
        """Communication message should be meaningful for a relevant JD."""
        jd = JOBS["agent_intern"]
        parsed = self.parser.parse(jd.raw_text)
        evidence = self.retriever.retrieve(parsed, top_k=5)
        analysis = self.analyzer.analyze(parsed, evidence)
        output = self.builder.build(parsed, evidence, analysis)

        assert len(output.communication_message) > 0
        # Should reference the job or contain greeting
        assert "您好" in output.communication_message or len(output.communication_message) > 20, (
            f"Communication message too short or missing greeting: "
            f"'{output.communication_message[:100]}'"
        )
