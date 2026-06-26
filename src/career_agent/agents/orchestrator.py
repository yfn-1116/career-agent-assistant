"""Orchestrator Agent — master coordinator for the PPAM cognitive architecture.

Perception → Planning → Action → Memory

The OrchestratorAgent classifies user intent (Perception), chooses an
execution path (Planning), delegates to specialized agents and tools
(Action), and stores/retrieves context (Memory).
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


class OrchestratorAgent:
    """Master agent that coordinates the full PPAM pipeline.

    Parameters
    ----------
    memory : ConversationMemory
        Short-term + long-term conversation memory.
    agent_service : AgentRunService, optional
        Service for running analysis workflows.
    kb_service : KnowledgeBaseService, optional
        Service for knowledge-base operations.
    """

    def __init__(
        self,
        memory: ConversationMemory | None = None,
        agent_service: Any = None,
        kb_service: Any = None,
        autonomous: bool = False,
    ) -> None:
        self.memory = memory or ConversationMemory()
        self._agent_service = agent_service
        self._kb_service = kb_service
        self._autonomous = autonomous
        self._autonomous_agent: Any = None

    def set_autonomous(self, enabled: bool, tool_registry: Any = None, llm_provider: Any = None) -> None:
        """Enable or disable autonomous LLM-driven agent mode."""
        self._autonomous = enabled
        if enabled and tool_registry and llm_provider:
            from career_agent.agents.autonomous_agent import AutonomousAgent
            self._autonomous_agent = AutonomousAgent(
                llm=llm_provider, tool_registry=tool_registry, memory=self.memory,
            )
        else:
            self._autonomous_agent = None

    # -- PPAM Pipeline -------------------------------------------------------

    def handle(self, user_message: str) -> AgentResponse:
        # === Autonomous mode: delegate to LLM-driven agent ===
        if self._autonomous and self._autonomous_agent:
            return self._handle_autonomous(user_message)
        return self._handle_ppam(user_message)

    def _handle_autonomous(self, user_message: str) -> AgentResponse:
        """LLM-driven autonomous agent path."""
        result = self._autonomous_agent.run(user_message)
        return AgentResponse(
            message=result.answer,
            intent="autonomous",
            data={"steps": len(result.steps), "tools_called": result.total_tools_called},
            perception_summary="LLM 自主感知用户意图",
            plan_summary=f"LLM 自主规划，共调用 {result.total_tools_called} 个工具",
            action_summary=f"执行完毕：{[s.tool_called for s in result.steps]}",
        )

    def _handle_ppam(self, user_message: str) -> AgentResponse:
        """Full PPAM pipeline: Perceive → Plan → Act → Remember.

        Returns an AgentResponse with the result and metadata for debugging.
        """

        # === Perception: classify intent + extract key info ===
        intent, keywords = self._perceive(user_message)

        # === Memory: recall relevant past context ===
        self.memory.user_says(user_message)
        recalled = self._recall_context(user_message, intent)
        memory_used = len(recalled) > 0

        # === Planning: choose execution path ===
        plan = self._plan(intent, user_message)

        # === Action: execute ===
        result = self._act(plan, user_message, intent, keywords)

        # === Memory: store result ===
        self.memory.assistant_says(
            result.message[:300],
            intent=intent,
            plan=plan,
        )

        result.memory_used = memory_used
        result.intent = intent
        return result

    # -- Perception ----------------------------------------------------------

    @staticmethod
    def _perceive(text: str) -> tuple[str, list[str]]:
        """Classify user intent and extract keywords.

        Returns (intent, keywords).
        """
        t = text.lower()

        # Intent classification (same logic as Streamlit _route_intent)
        if len(text) > 200 and any(kw in text for kw in [
            "岗位要求", "岗位职责", "任职要求", "职位描述", "薪资", "招聘",
        ]):
            intent = "analyze_job"
        elif any(kw in text for kw in ["简历", "bullet", "项目描述", "写进简历",
                                          "帮我改", "修改简历", "改写"]):
            intent = "tailor_resume"
        elif any(kw in text for kw in ["话术", "沟通", "打招呼", "回复", "HR"]):
            intent = "generate_message"
        elif any(kw in text for kw in [
            "知道我", "我的资料", "知识库", "上传了", "了解我", "个人画像",
        ]):
            intent = "show_profile"
        elif any(kw in text for kw in [
            "适合我吗", "匹配", "适不适合", "分析一下", "帮我评估",
        ]):
            intent = "analyze_job"
        elif "github.com" in t:
            intent = "github_ingest"
        elif len(text) > 100 and any(kw in text for kw in [
            "岗位", "实习", "招聘", "JD",
        ]):
            intent = "analyze_job"
        else:
            intent = "chat"

        # Keyword extraction
        keywords = list(set(
            kw for kw in [
                "Python", "RAG", "Agent", "LangGraph", "FastAPI",
                "简历", "JD", "匹配", "GitHub", "面试",
            ] if kw.lower() in t
        ))

        return intent, keywords

    # -- Memory retrieval ----------------------------------------------------

    def _recall_context(
        self, query: str, intent: str
    ) -> list[MemoryEntry]:
        """Retrieve relevant past conversations from long-term memory."""
        try:
            return self.memory.recall(query, top_k=3)
        except Exception:
            return []

    # -- Planning ------------------------------------------------------------

    @staticmethod
    def _plan(intent: str, user_message: str) -> str:
        """Choose the execution plan based on intent.

        Returns a plan identifier string.
        """
        plans = {
            "analyze_job": "langgraph_job_match",
            "tailor_resume": "langgraph_job_match",
            "generate_message": "message_agent",
            "show_profile": "kb_lookup",
            "github_ingest": "github_ingest",
            "chat": "rag_chat",
        }
        return plans.get(intent, "rag_chat")

    # -- Action --------------------------------------------------------------

    def _act(
        self, plan: str, user_message: str, intent: str, keywords: list[str],
    ) -> AgentResponse:
        """Execute the chosen plan via the appropriate service/agent."""

        if plan == "langgraph_job_match":
            return self._execute_job_analysis(user_message)

        if plan == "message_agent":
            return self._execute_message_generation(user_message)

        if plan == "kb_lookup":
            return self._execute_profile_lookup()

        if plan == "github_ingest":
            return self._execute_github_ingest(user_message)

        # Default: RAG chat
        return self._execute_rag_chat(user_message)

    def _execute_job_analysis(self, jd_text: str) -> AgentResponse:
        """Run full job matching workflow."""
        if self._agent_service is None:
            from career_agent.service.agent_run import AgentRunRequest, AgentRunService
            self._agent_service = AgentRunService()

        result = self._agent_service.run(
            AgentRunRequest(user_message=jd_text, raw_jd=jd_text, mode="analyze_job"),
        )
        match_pct = f"{result.match_score:.0%}" if result.match_score else "N/A"
        return AgentResponse(
            message=f"**匹配度：{match_pct}**",
            data={"result": result},
            perception_summary=f"识别到 JD 文本（{len(jd_text)} 字符），意图：岗位分析",
            plan_summary="规划路径：LangGraph Job Match Workflow（解析→检索→重排→评分→分析→生成→验证）",
            action_summary=f"已完成：匹配度 {match_pct}，检索 {len(result.evidence_sources)} 条证据",
        )

    def _execute_message_generation(self, _: str) -> AgentResponse:
        svc = self._agent_service
        if svc is None:
            from career_agent.service.agent_run import AgentRunService
            svc = AgentRunService()
        msg_result = svc.generate_message(job_title="目标岗位")
        return AgentResponse(
            message=msg_result.communication_script or "已生成沟通话术",
            data={"message": msg_result.communication_script},
            perception_summary="识别到沟通话术需求",
            plan_summary="规划路径：MessageAgent → 生成 Boss 直聘话术",
            action_summary="已完成：生成个性化沟通话术",
        )

    def _execute_profile_lookup(self) -> AgentResponse:
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        kb = self._kb_service
        summary = kb.get_summary()
        profile_text = kb.get_profile_text()
        return AgentResponse(
            message=f"知识库已索引 **{summary['chunk_count']}** 条片段，"
                    f"来自 **{summary['source_count']}** 个来源。",
            data={"summary": summary, "profile_preview": profile_text[:500]},
            perception_summary="识别到用户询问个人画像",
            plan_summary="规划路径：KnowledgeBaseService → get_summary + get_profile_text",
            action_summary=f"已查询：{summary['chunk_count']} 片段 / {summary['source_count']} 来源",
        )

    def _execute_github_ingest(self, text: str) -> AgentResponse:
        import re
        match = re.search(r"github\.com/([^/\s]+/[^/\s]+)", text)
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        kb = self._kb_service
        if match:
            repo = match.group(1).rstrip("/")
            try:
                r = kb.ingest_github_repo(repo)
                return AgentResponse(
                    message=f"已拉取 **{repo}**：索引了 {r.chunk_count} 条片段。",
                    perception_summary=f"识别到 GitHub 仓库链接：{repo}",
                    plan_summary="规划路径：GitHubRepoReader → TextChunker → JSONL",
                    action_summary=f"已完成：拉取 {repo}，索引 {r.chunk_count} 条",
                )
            except Exception:
                return AgentResponse(
                    message=f"无法拉取 {repo}，请确认仓库是公开的。",
                    perception_summary=f"尝试拉取 {repo} 失败",
                )
        return AgentResponse(message="请提供完整的 GitHub 链接。")

    def _execute_rag_chat(self, user_message: str) -> AgentResponse:
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        kb = self._kb_service

        evidence = kb.search(user_message, top_k=5)
        snippets = "\n".join(
            f"[{e.source_path}] {e.content[:200]}" for e in evidence
        ) if evidence else "（知识库中暂无相关内容）"

        # Add memory context
        mem_ctx = self.memory.context_text(n=5)

        # Call LLM for natural chat
        answer = ""
        try:
            from career_agent.infrastructure.llm.qwen_provider import QwenProvider
            llm = QwenProvider()
            if llm.is_available:
                prompt = (
                    f"你是求职顾问。以下是对话历史和知识库检索结果。\n\n"
                    f"对话历史：\n{mem_ctx}\n\n"
                    f"知识库检索结果：\n{snippets}\n\n"
                    f"用户问题：{user_message}\n\n"
                    f"规则：基于检索结果回答，引用来源。证据不足时诚实告知。不编造经历。"
                )
                answer = llm.generate(prompt, system_prompt="你是专业的求职顾问助手。")
        except Exception:
            pass

        return AgentResponse(
            message=answer or f"已检索知识库。{snippets[:300]}",
            data={"evidence_count": len(evidence)},
            perception_summary=f"识别为通用对话（{len(user_message)} 字符）",
            plan_summary="规划路径：BM25 检索 → Memory 召回 → LLM 生成",
            action_summary=f"已检索 {len(evidence)} 条证据 + {len(mem_ctx)} 条历史",
        )
