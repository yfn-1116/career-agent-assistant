"""Autonomous Agent Loop — LLM-driven tool calling.

Replaces the fixed LangGraph DAG with a dynamic LLM-in-the-loop pattern:
LLM sees conversation history + available tools → decides which tool to call
→ tool executes → result appended to history → loop until LLM says "done".

Reference: OpenCode agent.go:276-310 (processGeneration loop).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.memory import ConversationMemory
from career_agent.infrastructure.llm.base import LLMProvider


@dataclass
class AgentStep:
    """Record of one step in the agent loop."""
    step: int = 0
    tool_called: str = ""
    tool_input: str = ""
    tool_output: str = ""
    duration_ms: float = 0.0
    success: bool = True


@dataclass
class AutonomousResult:
    """Final result from the autonomous agent loop."""
    answer: str = ""
    steps: list[AgentStep] = field(default_factory=list)
    total_steps: int = 0
    total_tools_called: int = 0


class AutonomousAgent:
    """LLM-driven autonomous agent with tool calling.

    Parameters
    ----------
    llm : LLMProvider
        The LLM backend (Qwen, DeepSeek, etc.).
    tool_registry : ToolRegistry
        Registered tools the LLM can call.
    memory : ConversationMemory
        Short-term + long-term conversation memory.
    max_steps : int
        Maximum tool-calling steps per request (safety limit, default 10).
    """

    def __init__(
        self,
        llm: LLMProvider,
        tool_registry: Any = None,
        memory: ConversationMemory | None = None,
        max_steps: int = 10,
    ) -> None:
        self.llm = llm
        self.tool_registry = tool_registry
        self.memory = memory or ConversationMemory()
        self.max_steps = max_steps

    def run(self, user_message: str) -> AutonomousResult:
        """Execute the autonomous agent loop.

        Parameters
        ----------
        user_message : str
            The user's input message.

        Returns
        -------
        AutonomousResult with final answer and execution trace.
        """
        import time as _time

        # Build tool descriptions for system prompt
        tool_desc = self._build_tool_prompt()
        system = (
            "你是一个智能求职助手 Agent。你可以调用工具来完成用户的请求。\n\n"
            "规则：\n"
            "1. 分析用户需求，自主决定需要调用哪些工具。\n"
            "2. 如果用户提供了 JD 文本，先解析 JD，再检索经历，再做匹配分析。\n"
            "3. 如果用户提供了 GitHub 链接，先拉取项目信息。\n"
            "4. 所有生成内容必须基于检索到的 evidence，不得编造经历。\n"
            "5. 如果不确定答案，诚实告知用户。\n"
            "6. 用中文回复。\n\n"
            f"可用工具列表：\n{tool_desc}\n\n"
            "当你需要调用工具时，严格按以下 JSON 格式输出，不要加任何其他文字：\n"
            '{"tool_call": {"name": "工具名", "input": {"参数名": "参数值"}}}\n\n'
            "当你已经完成所有需要的工具调用，准备给用户最终答案时，直接输出你的回复。\n"
            "不要输出 JSON，直接输出回答文本。"
        )

        messages: list[dict] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

        steps: list[AgentStep] = []
        final_answer = ""

        for step_idx in range(self.max_steps):
            # Call LLM with current conversation
            prompt = self._format_messages(messages)
            t0 = _time.perf_counter()
            raw_response = self.llm.generate(prompt, system_prompt="")
            elapsed = (_time.perf_counter() - t0) * 1000

            # Try to parse as tool_call
            tool_call = self._parse_tool_call(raw_response)

            if tool_call is None:
                # No tool call → LLM is giving final answer
                final_answer = raw_response.strip()
                break

            # Execute tool
            tool_name = tool_call["name"]
            tool_input = tool_call.get("input", {})
            tool_result = self._execute_tool(tool_name, tool_input)

            step = AgentStep(
                step=step_idx + 1,
                tool_called=tool_name,
                tool_input=json.dumps(tool_input, ensure_ascii=False),
                tool_output=str(tool_result)[:300],
                duration_ms=round(elapsed, 2),
                success=bool(tool_result),
            )
            steps.append(step)

            # Append tool result to conversation
            messages.append({"role": "assistant", "content": raw_response[:300]})
            messages.append({"role": "tool", "content": str(tool_result)[:500]})

        else:
            # Loop exhausted (hit max_steps)
            final_answer = (
                f"已完成 {len(steps)} 步工具调用。"
                f"以下是当前状态：{json.dumps([s.tool_called for s in steps], ensure_ascii=False)}"
            )

        # Store in memory
        self.memory.user_says(user_message)
        self.memory.assistant_says(final_answer[:300])

        return AutonomousResult(
            answer=final_answer,
            steps=steps,
            total_steps=step_idx + 1 if steps else 1,
            total_tools_called=len(steps),
        )

    # -- tool description builder --------------------------------------------

    def _build_tool_prompt(self) -> str:
        """Generate tool descriptions for the system prompt."""
        if self.tool_registry is None:
            return "（无可用工具）"

        lines = []
        for name in sorted(self.tool_registry.list_tools()):
            try:
                tool = self.tool_registry.get(name)
                lines.append(f"- **{name}**: {tool.description}")
            except Exception:
                pass

        if not lines:
            return "（无可用工具）"

        return "\n".join(lines)

    # -- message formatting --------------------------------------------------

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        """Format conversation history into a single prompt string."""
        parts = []
        for msg in messages:
            role = msg["role"]
            content = str(msg.get("content", ""))[:1000]
            label = {"system": "系统", "user": "用户", "assistant": "助手", "tool": "工具结果"}.get(role, role)
            parts.append(f"[{label}]: {content}")
        return "\n\n".join(parts)

    # -- tool call parsing ---------------------------------------------------

    @staticmethod
    def _parse_tool_call(text: str) -> dict | None:
        """Attempt to parse a tool_call JSON from LLM output.

        Returns None if the text is not a tool call.
        """
        text = text.strip()

        # Try direct JSON parse
        try:
            data = json.loads(text)
            if "tool_call" in data:
                return data["tool_call"]
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting JSON block from markdown code fences
        if "```" in text:
            import re
            blocks = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            for block in blocks:
                try:
                    data = json.loads(block)
                    if "tool_call" in data:
                        return data["tool_call"]
                except (json.JSONDecodeError, TypeError):
                    pass

        # Try finding JSON object with tool_call key
        import re
        matches = re.findall(r'\{[^{}]*"tool_call"[^{}]*\}', text)
        for match in matches:
            try:
                data = json.loads(match)
                if "tool_call" in data:
                    return data["tool_call"]
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    # -- tool execution ------------------------------------------------------

    def _execute_tool(self, name: str, inputs: dict) -> str:
        """Execute a registered tool by name with given inputs."""
        if self.tool_registry is None:
            return "[错误] ToolRegistry 未初始化"

        try:
            result = self.tool_registry.invoke(name, **inputs)
            if result.success:
                return result.summary
            return f"[错误] {result.error}"
        except Exception as e:
            return f"[异常] {type(e).__name__}: {e}"
