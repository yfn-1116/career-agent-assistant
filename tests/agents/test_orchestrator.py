"""Tests for OrchestratorAgent."""
import pytest
from career_agent.agents.orchestrator import OrchestratorAgent, AgentResponse
from career_agent.agents.memory import ConversationMemory


class TestPerception:
    def test_analyze_job_intent(self):
        # Need >200 chars for analyze_job detection (realistic JD)
        jd = "# AI Agent 开发实习生\n\n## 岗位要求\n- Python\n- RAG\n- LangGraph\n- FastAPI\n" * 10
        intent, kw = OrchestratorAgent._perceive(jd)
        assert intent == "analyze_job"

    def test_tailor_resume_intent(self):
        intent, kw = OrchestratorAgent._perceive("帮我改简历，把 Python 经验突出")
        assert intent == "tailor_resume"

    def test_generate_message_intent(self):
        intent, kw = OrchestratorAgent._perceive("生成一个 BOSS 打招呼的话术")
        assert intent == "generate_message"

    def test_show_profile_intent(self):
        intent, kw = OrchestratorAgent._perceive("你了解我吗？我的个人画像是什么")
        assert intent == "show_profile"

    def test_github_ingest_intent(self):
        intent, kw = OrchestratorAgent._perceive("https://github.com/yfn-1116/career-agent-assistant")
        assert intent == "github_ingest"

    def test_default_chat_intent(self):
        intent, kw = OrchestratorAgent._perceive("今天天气真好")
        assert intent == "chat"

    def test_keyword_extraction(self):
        _, kw = OrchestratorAgent._perceive("Python RAG Agent 开发")
        assert "Python" in kw or "RAG" in kw or "Agent" in kw


class TestPlanning:
    def test_jd_analysis_plan(self):
        plan = OrchestratorAgent._plan("analyze_job", "...")
        assert plan == "langgraph_job_match"

    def test_chat_plan(self):
        plan = OrchestratorAgent._plan("chat", "...")
        assert plan == "rag_chat"


class TestOrchestratorEndToEnd:
    def test_basic_handle(self):
        orch = OrchestratorAgent()
        resp = orch.handle("你好")
        assert isinstance(resp, AgentResponse)
        assert resp.intent in ("chat", "show_profile")
        # Memory should have 2 entries (user + assistant)
        assert len(orch.memory.get_context()) == 2

    def test_ppam_trace_in_response(self):
        orch = OrchestratorAgent()
        resp = orch.handle("帮我分析这个岗位")
        assert isinstance(resp, AgentResponse)
        # Response should track PPAM stages
        assert resp.intent != ""
        # We don't assert on message content since it depends on service availability

    def test_memory_grows_with_multiple_turns(self):
        orch = OrchestratorAgent()
        orch.handle("第一轮对话")
        orch.handle("第二轮对话")
        ctx = orch.memory.get_context(n=10)
        assert len(ctx) == 4  # 2 user + 2 assistant
