"""Tests for unified Agent Run Service."""

import tempfile
from pathlib import Path

from career_agent.service.agent_run import AgentRunRequest, AgentRunService

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
