"""Tests for unified Agent Run Service."""

import tempfile
from pathlib import Path

from career_agent.service.agent_run import AgentRunRequest, AgentRunService
from career_agent.agents.state import GeneratedOutput, MatchAnalysisResult, ParsedJD
from career_agent.evaluation.faithfulness import FaithfulnessReport

PROFILE_DIR = str(Path(__file__).resolve().parents[2] / "data" / "samples" / "profile")

SAMPLE_JD = """# AI Agent 开发实习生

岗位要求：
- Python, LangChain, LangGraph, RAG
- 加分：Agent 系统经验, FastAPI
"""


class TestAgentRunService:
    def test_run_analyze_mode(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentRunRequest(
                user_message="分析这个岗位匹配度",
                raw_jd=SAMPLE_JD,
                mode="analyze",
            )
            result = svc.run(request, output_dir=tmp)
            assert result.trace_id
            assert result.final_answer
            assert "Agent" in result.final_answer or "agent" in result.final_answer.lower()
            assert result.status == "completed"

    def test_run_resume_mode(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentRunRequest(
                user_message="帮我生成简历 bullet",
                raw_jd=SAMPLE_JD,
                mode="resume",
            )
            result = svc.run(request, output_dir=tmp)
            assert result.trace_id
            assert result.final_answer

    def test_result_has_all_fields(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentRunRequest(user_message="test", raw_jd=SAMPLE_JD)
            result = svc.run(request, output_dir=tmp)
            assert result.trace_id
            assert isinstance(result.final_answer, str)
            assert isinstance(result.retrieval_grade, str)
            assert isinstance(result.warnings, list)
            assert result.status in ("completed", "failed", "fallback")

    def test_report_written(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentRunRequest(user_message="test", raw_jd=SAMPLE_JD)
            result = svc.run(request, output_dir=tmp)
            if result.report_path:
                assert Path(result.report_path).is_file()

    def test_missing_jd_still_works(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            request = AgentRunRequest(user_message="我有什么项目经历？", mode="chat")
            result = svc.run(request, output_dir=tmp)
            assert result.trace_id
            assert result.final_answer or result.status == "fallback"

    def test_convenience_analyze_job_entrypoint(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        with tempfile.TemporaryDirectory() as tmp:
            result = svc.analyze_job(SAMPLE_JD, output_dir=tmp)
            assert result.trace_id
            assert result.status == "completed"
            assert result.generated_bullets

    def test_generate_message_entrypoint(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        result = svc.generate_message(
            job_title="AI Agent 实习生",
            matched_skills=["Python", "RAG"],
        )
        assert result.trace_id
        assert result.message_draft is not None
        assert "AI Agent" in result.communication_script

    def test_chat_about_job_entrypoint(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        result = svc.chat_about_job("请问你什么时候可以到岗？")
        assert result.trace_id
        assert result.approval_required
        assert result.message_draft is not None

    def test_save_application_entrypoint(self):
        svc = AgentRunService(profile_dir=PROFILE_DIR)
        result = svc.generate_message(job_title="Backend Intern", matched_skills=["Python"])
        with tempfile.TemporaryDirectory() as tmp:
            record = svc.save_application(
                result,
                job_title="Backend Intern",
                jd_text="Python backend intern",
                runtime_dir=tmp,
            )
            assert record.application_id
            assert record.job_title == "Backend Intern"

    def test_output_constraints_are_visible_in_result(self, monkeypatch):
        from career_agent.service import agent_run as agent_run_module

        class _RetrievalScores:
            grade = "good"
            metadata = {"total_score": 0.8}

        def fake_workflow(**kwargs):
            return {
                "trace_id": "trace-safe",
                "decision": "continue",
                "retry_count": 1,
                "missing_keywords": [],
                "retrieved_chunks": [],
                "parsed_jd": ParsedJD(job_title="AI Agent 实习生", hard_skills=["Python"]),
                "match_analysis": MatchAnalysisResult(strengths=["具备 Python 相关经验"]),
                "generated_result": GeneratedOutput(
                    resume_bullets=["- 计划补强 Kubernetes 部署"],
                    communication_message="您好，我对该岗位感兴趣。",
                    summary="基于证据生成。",
                    evidence_refs=["ev-planned"],
                    metadata={
                        "warnings": ["planned evidence 不能直接写入简历"],
                        "can_write_claims": [],
                        "needs_confirmation_claims": [],
                        "learning_plan_claims": ["- 计划补强 Kubernetes 部署"],
                    },
                ),
                "retrieval_scores": _RetrievalScores(),
                "faithfulness_report": FaithfulnessReport(
                    faithfulness_score=0.4,
                    decision="revise_required",
                    unsupported_claims=[{"text": "unsupported"}],
                ),
                "report_path": "",
                "status": "completed",
            }

        monkeypatch.setattr(agent_run_module, "run_langgraph_workflow", fake_workflow)
        result = AgentRunService(profile_dir=PROFILE_DIR).analyze_job(SAMPLE_JD)

        assert result.approval_required
        assert "planned evidence 不能直接写入简历" in result.warnings
        assert any("Faithfulness" in warning for warning in result.warnings)
        assert result.can_write_claims == []
        assert result.cannot_write_claims == ["- 计划补强 Kubernetes 部署"]
