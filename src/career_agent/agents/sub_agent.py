"""Sub-Agent — spawned by main Agent for isolated parallel tasks.

Reference: OpenCode agent-tool.go (Agent as a Tool pattern).

The SubAgentTool is registered in ToolRegistry as "task_agent".
When the main LLM decides to spawn a sub-agent:
  1. LLM calls task_agent(prompt="详细任务描述", tools=["parse_jd","web_search"])
  2. SubAgent creates an isolated conversation
  3. SubAgent autonomously executes the task with ONLY the specified tools
  4. SubAgent returns a single consolidated result
  5. Main Agent receives the result without seeing sub-agent's intermediate steps
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.memory import ConversationMemory


@dataclass
class SubAgentResult:
    """Result from a sub-agent execution."""
    success: bool = True
    answer: str = ""
    tools_called: list[str] = field(default_factory=list)
    error: str = ""


class SubAgent:
    """Isolated worker agent with a limited tool set.

    Parameters
    ----------
    llm : LLMProvider
        LLM backend for autonomous operation.
    tool_registry : ToolRegistry
        Full tool registry; sub-agent only accesses the whitelisted subset.
    max_steps : int
        Maximum tool-calling steps (default 8).
    """

    def __init__(
        self,
        llm: Any = None,
        tool_registry: Any = None,
        max_steps: int = 8,
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_steps = max_steps

    def execute(
        self,
        task: str,
        allowed_tools: list[str] | None = None,
    ) -> SubAgentResult:
        """Execute a task with restricted tool access.

        Parameters
        ----------
        task : str
            Detailed task description (the "prompt" from the main Agent).
        allowed_tools : list[str], optional
            Whitelist of tool names. If None, uses read-only defaults.

        Returns
        -------
        SubAgentResult with consolidated answer.
        """
        if self.llm is None:
            return SubAgentResult(success=False, error="No LLM provider available")

        if self.tool_registry is None:
            return SubAgentResult(success=False, error="No ToolRegistry available")

        # Default: read-only tools (like OpenCode's TaskAgentTools)
        if allowed_tools is None:
            allowed_tools = [
                "parse_jd", "retrieve_profile", "web_search",
                "github_repo", "select_evidence", "grade_retrieval",
            ]

        # Build tool descriptions for the sub-agent
        tool_desc_lines = []
        for name in allowed_tools:
            try:
                tool = self.tool_registry.get(name)
                tool_desc_lines.append(f"- **{name}**: {tool.description}")
            except Exception:
                pass

        tool_desc = "\n".join(tool_desc_lines) if tool_desc_lines else "（无可用工具）"

        system = (
            "你是一个子任务执行 Agent。你的主 Agent 分配了一个任务给你。\n\n"
            "规则：\n"
            "1. 只做任务描述里要求的事情，不要做额外的事。\n"
            "2. 你只能使用被分配的工具，不要在工具列表之外调用工具。\n"
            "3. 执行完毕后，返回一条简洁的汇总结果。\n"
            "4. 用中文回复。\n\n"
            f"你可用的工具：\n{tool_desc}\n\n"
            "当你需要调用工具时，输出 JSON：\n"
            '{"tool_call": {"name": "工具名", "input": {}}}\n\n'
            "当你完成任务时，直接输出最终汇总结果。"
        )

        import json as _json

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"任务：{task}\n\n请执行这个任务并返回汇总结果。"},
        ]

        tools_called: list[str] = []
        final_answer = ""

        for _step in range(self.max_steps):
            prompt = "\n\n".join(
                f"[{m['role']}]: {str(m.get('content', ''))[:800]}"
                for m in messages
            )

            raw = self.llm.generate(prompt, system_prompt="")

            # Try parse tool_call
            tool_call = None
            try:
                text = raw.strip()
                if text.startswith("{"):
                    data = _json.loads(text)
                    if "tool_call" in data:
                        tool_call = data["tool_call"]
            except Exception:
                pass

            if tool_call is None:
                final_answer = raw.strip()
                break

            tool_name = tool_call.get("name", "")
            if tool_name not in allowed_tools:
                messages.append({"role": "tool", "content": f"[拒绝] 工具 '{tool_name}' 不在允许列表中"})
                continue

            tool_input = tool_call.get("input", {})
            try:
                result = self.tool_registry.invoke(tool_name, **tool_input)
                tools_called.append(tool_name)
                tool_output = result.summary if result.success else f"[错误] {result.error}"
            except Exception as e:
                tool_output = f"[异常] {type(e).__name__}: {e}"

            messages.append({"role": "assistant", "content": raw[:200]})
            messages.append({"role": "tool", "content": str(tool_output)[:500]})
        else:
            final_answer = f"已完成 {len(tools_called)} 步工具调用。"

        return SubAgentResult(
            success=True,
            answer=final_answer,
            tools_called=tools_called,
        )
