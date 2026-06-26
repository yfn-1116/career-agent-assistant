"""Orchestrator Agent — master coordinator using LLM-driven autonomous mode.

The OrchestratorAgent delegates to AutonomousAgent (LLM-driven tool calling)
by default. Falls back to rule-based PPAM pipeline when no LLM is available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.memory import ConversationMemory, MemoryEntry


@dataclass
class AgentResponse:
    """Structured response from the OrchestratorAgent."""

    message: str = ""
    intent: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    memory_used: bool = False
    perception_summary: str = ""
    plan_summary: str = ""
    action_summary: str = ""
    steps: list[str] = field(default_factory=list)


class OrchestratorAgent:
    """Master agent using LLM-driven autonomous tool calling.

    Parameters
    ----------
    memory : ConversationMemory
        Short-term + long-term conversation memory.
    agent_service : AgentRunService, optional
        Service for running analysis workflows.
    kb_service : KnowledgeBaseService, optional
        Service for knowledge-base operations.
    tool_registry : ToolRegistry, optional
        Registry of tools for autonomous mode.
    llm_provider : LLMProvider, optional
        LLM backend for autonomous mode. If None, falls back to rule-based PPAM.
    """

    def __init__(
        self,
        memory: ConversationMemory | None = None,
        agent_service: Any = None,
        kb_service: Any = None,
        tool_registry: Any = None,
        llm_provider: Any = None,
    ) -> None:
        self.memory = memory or ConversationMemory()
        self._agent_service = agent_service
        self._kb_service = kb_service
        self._tool_registry = tool_registry
        self._llm_provider = llm_provider
        self._autonomous_agent: Any = None

    def handle(self, user_message: str) -> AgentResponse:
        # === Try autonomous mode first ===
        if self._tool_registry and self._llm_provider:
            return self._handle_autonomous(user_message)
        # === Fallback to rule-based PPAM ===
        return self._handle_ppam(user_message)

    def _handle_autonomous(self, user_message: str) -> AgentResponse:
        """LLM-driven autonomous agent: LLM decides which tools to call."""
        if self._autonomous_agent is None:
            from career_agent.agents.autonomous_agent import AutonomousAgent
            self._autonomous_agent = AutonomousAgent(
                llm=self._llm_provider,
                tool_registry=self._tool_registry,
                memory=self.memory,
            )

        result = self._autonomous_agent.run(user_message)
        return AgentResponse(
            message=result.answer,
            intent="autonomous",
            data={"total_steps": result.total_steps, "tools_called": result.total_tools_called},
            steps=[s.tool_called for s in result.steps],
            perception_summary="LLM 自主感知用户意图",
            plan_summary=f"LLM 自主规划 → 调用 {result.total_tools_called} 个工具",
            action_summary=" → ".join(s.tool_called for s in result.steps) if result.steps else "直接回答",
        )

    def _handle_ppam(self, user_message: str) -> AgentResponse:
        """Rule-based PPAM pipeline (fallback when no LLM available)."""
        intent, keywords = self._perceive(user_message)
        self.memory.user_says(user_message)
        plan = self._plan(intent, user_message)
        result = self._act(plan, user_message, intent, keywords)
        self.memory.assistant_says(result.message[:300], intent=intent, plan=plan)
        result.intent = intent
        return result

    # -- Perception (fallback rule-based) ----------------------------------

    @staticmethod
    def _perceive(text: str) -> tuple[str, list[str]]:
        t = text.lower()
        keywords = [kw for kw in ["Python","RAG","Agent","LangGraph","FastAPI","简历","JD","匹配","GitHub","面试"]
                    if kw.lower() in t]

        if len(text) > 200 and any(kw in text for kw in [
            "岗位要求", "岗位职责", "任职要求", "职位描述", "薪资", "招聘",
        ]):
            return ("analyze_job", keywords)
        if any(kw in text for kw in ["简历", "bullet", "项目描述"]):
            return ("tailor_resume", keywords)
        if any(kw in text for kw in ["话术", "沟通", "HR"]):
            return ("generate_message", keywords)
        if any(kw in t for kw in ["知道我", "我的资料", "知识库", "了解我", "个人画像"]):
            return ("show_profile", keywords)
        if "github.com" in t:
            return ("github_ingest", keywords)
        if len(text) > 100 and any(kw in text for kw in ["岗位", "实习", "JD"]):
            return ("analyze_job", keywords)
        return ("chat", keywords)

    # -- Planning (fallback) -----------------------------------------------

    @staticmethod
    def _plan(intent: str, user_message: str) -> str:
        return {
            "analyze_job": "langgraph_job_match",
            "tailor_resume": "langgraph_job_match",
            "generate_message": "message_agent",
            "show_profile": "kb_lookup",
            "github_ingest": "github_ingest",
            "chat": "rag_chat",
        }.get(intent, "rag_chat")

    # -- Action (fallback) -------------------------------------------------

    def _act(self, plan: str, user_message: str, intent: str, keywords: list[str]) -> AgentResponse:
        return {
            "langgraph_job_match": self._execute_job_analysis,
            "message_agent": self._execute_message_generation,
            "kb_lookup": self._execute_profile_lookup,
            "github_ingest": self._execute_github_ingest,
            "rag_chat": self._execute_rag_chat,
        }.get(plan, self._execute_rag_chat)(user_message)

    def _execute_job_analysis(self, jd_text: str) -> AgentResponse:
        if self._agent_service is None:
            from career_agent.service.agent_run import AgentRunRequest, AgentRunService
            self._agent_service = AgentRunService()
        result = self._agent_service.run(AgentRunRequest(user_message=jd_text, raw_jd=jd_text, mode="analyze_job"))
        match_pct = f"{result.match_score:.0%}" if result.match_score else "N/A"
        return AgentResponse(message=f"**匹配度：{match_pct}**", data={"result": result})

    def _execute_message_generation(self, _: str) -> AgentResponse:
        from career_agent.service.agent_run import AgentRunService
        r = AgentRunService().generate_message(job_title="目标岗位")
        return AgentResponse(message=r.communication_script or "已生成")

    def _execute_profile_lookup(self) -> AgentResponse:
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        s = self._kb_service.get_summary()
        return AgentResponse(message=f"知识库: {s['chunk_count']} 片段 / {s['source_count']} 来源")

    def _execute_github_ingest(self, text: str) -> AgentResponse:
        import re
        m = re.search(r"github\.com/([^/\s]+/[^/\s]+)", text)
        if m and self._kb_service:
            r = self._kb_service.ingest_github_repo(m.group(1).rstrip("/"))
            return AgentResponse(message=f"已拉取 {m.group(1)}: {r.chunk_count} 条")
        return AgentResponse(message="请提供 GitHub 链接")

    def _execute_rag_chat(self, user_message: str) -> AgentResponse:
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        evidence = self._kb_service.search(user_message, top_k=5)
        return AgentResponse(
            message=f"检索到 {len(evidence)} 条证据",
            data={"evidence_count": len(evidence)},
        )
