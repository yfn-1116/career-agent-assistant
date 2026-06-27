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
        # === Always use PPAM — autonomous mode disabled until Qwen ReAct improves ===
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

        has_github = "github.com" in t
        has_jd = len(text) > 100 and any(kw in text for kw in [
            "岗位要求", "岗位职责", "任职要求", "职位描述", "薪资", "招聘", "岗位", "实习", "JD",
        ])
        # JD + GitHub combo → analyze_job (not github_ingest)
        if has_jd and has_github:
            return ("analyze_job", keywords)
        if has_jd:
            return ("analyze_job", keywords)
        if any(kw in text for kw in ["简历", "bullet", "项目描述"]):
            return ("tailor_resume", keywords)
        if any(kw in text for kw in ["话术", "沟通", "HR"]):
            return ("generate_message", keywords)
        if any(kw in t for kw in ["知道我", "我的资料", "知识库", "了解我", "个人画像"]):
            return ("show_profile", keywords)
        if has_github:
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
        # Search KB for relevant evidence
        kb_evidence = ""
        if self._kb_service:
            results = self._kb_service.search(jd_text, top_k=10)
            if results:
                kb_evidence = "\n---\n".join([
                    f"[{r.source_path}]\n{r.content[:800]}" for r in results
                ])

        # Always use LLM for analysis — no rule-based fallback
        if self._llm_provider and self._llm_provider.is_available:
            prompt = f"""你是专业求职顾问。根据以下JD和候选人的GitHub项目/简历，做岗位匹配分析。

=== 岗位JD ===
{jd_text[:2000]}

=== 候选人经历 ===
{kb_evidence[:4000] or '（知识库中暂无数据，请基于JD本身给出通用建议）'}

请输出：
1. **匹配度**：估计百分比（如 70%）
2. **强项**：JD中哪些要求被候选人的项目覆盖了？具体说明哪个项目覆盖了哪个要求。
3. **弱项**：JD中哪些要求候选人没有对应经历？
4. **简历要点**：基于真实项目经历，用 STAR 法则写 3 条可以直接写进简历的描述（每条标注证据来源）
5. **HR沟通话术**：一段 100 字以内的打招呼文本

规则：必须基于提供的证据，不得编造。如果某技能候选人确实没有，诚实说"建议补充"。用中文输出。"""
            try:
                reply = self._llm_provider.generate(prompt, system_prompt="你是专业求职顾问。基于真实证据分析，不编造。")
                return AgentResponse(message=reply[:2500], memory_used=True)
            except Exception as e:
                return AgentResponse(message=f"LLM 分析失败: {e}")

        return AgentResponse(message="LLM 不可用，请检查 API 配置。")

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
        from career_agent.tools.mcp_github_tool import MCPGitHubTool
        gh = MCPGitHubTool()
        m = re.search(r"github\.com/([a-zA-Z0-9._-]+)(?:/([a-zA-Z0-9._-]+))?", text)
        if not m:
            return AgentResponse(message="请提供 GitHub 链接")
        username = m.group(1)
        repo = m.group(2)
        # Specific repo → always works (raw.githubusercontent.com, no auth needed)
        if repo:
            result = gh.run(action="read_repo", repo=f"{username}/{repo}")
            if result.success:
                return AgentResponse(message=f"## {username}/{repo}\n\n{result.summary[:1500]}")
            # Fallback: search cached KB
            if self._kb_service:
                kb_results = self._kb_service.search(f"github:{username}/{repo}", top_k=3)
                if kb_results:
                    return AgentResponse(message="\n\n".join(r.content[:500] for r in kb_results))
            return AgentResponse(message=f"无法读取 {username}/{repo}。请确认仓库名正确。")
        # Username → search KB cache + try API
        lines = [f"## {username} 的 GitHub 仓库（本地缓存）", ""]
        found = False
        if self._kb_service:
            kb_results = self._kb_service.search(f"github:yfn-1116", top_k=15)
            seen = set()
            for r in kb_results:
                for rn in ["career-agent-assistant","chem-auto-titration","polyu-internship-project",
                          "opencode","machine-learning-labs","cnn-mnist-homework","mlp-mnist-homework","LeetCode"]:
                    if rn in r.content and rn not in seen:
                        seen.add(rn)
                        lines.append(f"- **{rn}**: {r.content[:120].strip()}...")
                        found = True
        if found:
            lines.append(f"\n共 {len(seen)} 个仓库。粘贴具体链接查看详情，例如 https://github.com/{username}/career-agent-assistant")
            return AgentResponse(message="\n".join(lines))
        # Last resort: try API
        result = gh.run(action="list_user_repos", username=username)
        if result.success:
            return AgentResponse(message=f"## {username} 的公开仓库\n\n{result.summary}")
        return AgentResponse(message=f"请粘贴具体仓库链接，例如 https://github.com/{username}/项目名")

    def _execute_rag_chat(self, user_message: str) -> AgentResponse:
        # GitHub query? → use the github tool
        if "github.com/" in user_message.lower() or "github" in user_message.lower():
            return self._handle_github_query(user_message)

        # Search KB for relevant context
        kb_context = ""
        results = []
        if self._kb_service:
            results = self._kb_service.search(user_message, top_k=3)
            if results:
                kb_context = "\n".join([f"- {r.title}: {r.content[:300]}" for r in results])

        # Try LLM for chat reply
        if self._llm_provider and self._llm_provider.is_available:
            prompt = f"""你是求职助手。基于以下知识库内容回答用户问题。
知识库内容：
{kb_context or '（知识库中暂无直接相关内容）'}

用户问题：{user_message}

用中文简洁回答（100字以内）。如果知识库有相关内容就引用，没有就诚实说不知道。"""
            try:
                reply = self._llm_provider.generate(prompt, system_prompt="你是求职顾问，回答简洁、诚实。")
                return AgentResponse(message=reply[:500], memory_used=True)
            except Exception:
                pass

        count = len(results)
        return AgentResponse(message=f"知识库中找到 {count} 条相关内容。" if count else "请提供更多信息。")

    def _handle_github_query(self, user_message: str) -> AgentResponse:
        """Use MCPGitHubTool to fetch real GitHub data."""
        import re
        from career_agent.tools.mcp_github_tool import MCPGitHubTool
        gh = MCPGitHubTool()

        # Extract username or repo from message
        username = None
        repo = None
        # Pattern: github.com/username
        m = re.search(r'github\.com/([^/\s]+)(?:/([^/\s]+))?', user_message)
        if m:
            username = m.group(1)
            repo = m.group(2) if m.group(2) else None

        if repo:
            # Specific repo → read it
            full_repo = f"{username}/{repo}"
            result = gh.run(action="read_repo", repo=full_repo)
            if result.success:
                return AgentResponse(
                    message=f"## 📂 {full_repo}\n\n{result.summary[:1500]}",
                    data={"repo": full_repo}
                )
            return AgentResponse(message=f"无法读取 {full_repo}: {result.error}")

        if username:
            # Just username → list repos
            result = gh.run(action="list_user_repos", username=username)
            if result.success:
                return AgentResponse(
                    message=f"## 📂 {username} 的公开仓库\n\n{result.summary}",
                    data={"username": username}
                )
            return AgentResponse(message=f"无法获取 {username} 的仓库: {result.error}")

        return AgentResponse(message="请提供 GitHub 用户名或仓库链接。")
        if self._kb_service is None:
            from career_agent.service.knowledge_base import KnowledgeBaseService
            self._kb_service = KnowledgeBaseService()
        evidence = self._kb_service.search(user_message, top_k=5)
        return AgentResponse(
            message=f"检索到 {len(evidence)} 条证据",
            data={"evidence_count": len(evidence)},
        )
