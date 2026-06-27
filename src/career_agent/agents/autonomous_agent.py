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
        """Execute the autonomous agent loop with full memory integration.

        Memory layers used:
        1. Short-term: last 10 conversation turns from ConversationMemory
        2. Long-term: BM25 recall of relevant past conversations
        3. Knowledge base: queried via retrieve_profile tool during loop

        Parameters
        ----------
        user_message : str
            The user's input message.

        Returns
        -------
        AutonomousResult with final answer and execution trace.
        """
        import time as _time

        # 1. Build tool descriptions for system prompt
        tool_desc = self._build_tool_prompt()
        system = (
            "你是求职助手 Agent。直接高效地完成任务，不要过度解释。\n\n"
            "工作流程（用户提供了 JD 和 GitHub）：\n"
            "1. 同时调用 parse_jd 和 github(action='list_user_repos') — 并行，一步完成\n"
            "2. 拿到仓库列表后，立即调用 github(action='read_repo', repo='owner/最相关的repo名') 读README\n"
            "3. 调用 retrieve_profile 检索知识库中的匹配经历\n"
            "4. 调用 analyze_match 做匹配分析\n"
            "5. 输出最终结果\n\n"
            "规则：\n"
            "- 每步尽量同时调多个工具（一行一个 tool_call），减少轮次\n"
            "- 不要猜测文件路径，read_repo 会自动读 README\n"
            "- 用 github(action='list_user_repos', username='用户名') 列出仓库\n"
            "- 用 github(action='read_repo', repo='owner/repo名') 读仓库\n"
            "- 所有输出基于证据，不编造，用中文回复\n\n"
            f"可用工具：\n{tool_desc}\n\n"
            "调用工具时用: tool名(key='value', key2='value2')"
        )

        # 2. Build message context with multi-layer memory
        messages: list[dict] = [
            {"role": "system", "content": system},
        ]

        # 2a. Short-term memory: recent conversation (last 10 turns)
        short_term = self.memory.get_context(10)
        if short_term:
            messages.append({"role": "system", "content": "以下是最近的对话历史：\n" + "\n".join(
                f"[{'用户' if e.role == 'user' else '助手'}]: {e.content[:300]}" for e in short_term
            )})

        # 2b. Long-term memory: recall relevant past conversations
        recalled = self.memory.recall(user_message, top_k=2)
        if recalled:
            recall_text = "以下是历史相关对话（可能来自之前的会话）：\n" + "\n".join(
                f"[{e.timestamp[:10]} {e.role}]: {e.content[:200]}" for e in recalled
            )
            messages.append({"role": "system", "content": recall_text})

        # 2c. Current user message
        messages.append({"role": "user", "content": user_message})

        # 3. Agent loop
        steps: list[AgentStep] = []
        final_answer = ""

        for step_idx in range(self.max_steps):
            # Call LLM with current conversation
            prompt = self._format_messages(messages)
            t0 = _time.perf_counter()
            raw_response = self.llm.generate(prompt, system_prompt="")
            elapsed = (_time.perf_counter() - t0) * 1000

            # Try to parse tool_call(s) — LLM may output multiple in one response
            tool_calls = self._parse_tool_calls(raw_response)

            if not tool_calls:
                # No tool call → LLM is giving final answer
                final_answer = raw_response.strip()
                break

            # Execute ALL tool calls from this response
            all_results = []
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_input = tc.get("input", {})
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
                all_results.append((tool_name, tool_result))
                step_idx += 1  # count each tool call separately

                # Persist each tool result to memory
                self.memory.remember("assistant", f"[调用工具: {tool_name}] {json.dumps(tool_input, ensure_ascii=False)[:200]}")
                self.memory.remember("tool", str(tool_result)[:300])

            # Append ALL results to conversation
            messages.append({"role": "assistant", "content": raw_response[:300]})
            for tool_name, tool_result in all_results:
                messages.append({"role": "tool", "content": f"[{tool_name}]: {str(tool_result)[:500]}"})

        else:
            # Loop exhausted (hit max_steps)
            final_answer = (
                f"已完成 {len(steps)} 步工具调用。"
                f"步骤: {', '.join(s.tool_called for s in steps)}。"
            )

        # 4. Persist final result
        self.memory.user_says(user_message)
        self.memory.assistant_says(final_answer[:500])

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
    def _extract_json_objects(text: str) -> list[dict]:
        """Extract all JSON objects from text using brace matching."""
        results = []
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        obj = json.loads(text[start:i+1])
                        results.append(obj)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    start = -1
        return results

    @staticmethod
    def _parse_python_style(text: str) -> list[dict]:
        """Parse Python-style tool calls: tool_name(key='value', key2='value2')"""
        import re
        results = []
        # Match: tool_name(param1='val1', param2='val2', ...)
        for match in re.finditer(r'(\w+)\(([^)]+)\)', text):
            name = match.group(1)
            if name in ('http', 'https', 'print', 'def', 'class', 'if', 'for', 'while',
                       'return', 'import', 'from', 'and', 'or', 'not', 'in', 'is'):
                continue
            args_str = match.group(2)
            inputs = {}
            # Match both single and double quoted values: key='val' or key=\"val\"
            for pm in re.finditer(r"""(\w+)\s*=\s*['\"]([^'\"]*)['\"]""", args_str):
                inputs[pm.group(1)] = pm.group(2)
            if inputs:
                results.append({"name": name, "input": inputs})
        return results

    @staticmethod
    def _normalize_tool_call(obj: dict) -> dict | None:
        """Convert various tool call formats to {'name': ..., 'input': ...}."""
        # Format 1: {"tool_call": {"name": ..., "input": ...}}
        if "tool_call" in obj:
            tc = obj["tool_call"]
            if isinstance(tc, dict) and "name" in tc:
                return {"name": tc["name"], "input": tc.get("input", tc.get("arguments", {}))}
        # Format 2: {"tool": ..., "action": ..., "params": ...}
        if "tool" in obj and "action" in obj:
            return {"name": obj["tool"], "input": {"action": obj["action"], **obj.get("params", {}), **obj.get("input", {})}}
        # Format 3: {"name": ..., "arguments": ...} or {"name": ..., "input": ...}
        if "name" in obj:
            return {"name": obj["name"], "input": obj.get("input", obj.get("arguments", {}))}
        # Format 4: {"function": {"name": ..., "arguments": ...}}
        if "function" in obj and isinstance(obj["function"], dict):
            fc = obj["function"]
            if "name" in fc:
                return {"name": fc["name"], "input": fc.get("arguments", fc.get("input", {}))}
        return None

    @staticmethod
    def _parse_tool_calls(text: str) -> list[dict]:
        """Parse ALL tool calls from LLM output. Returns list of {'name':..., 'input':...}."""
        import re
        results = []
        seen = set()

        # Format A: [调用工具: tool_name] optionally followed by JSON or key=value
        for m in re.finditer(r'\[调用工具[：:]\s*(\w+)\]\s*(\{.*?\})?', text):
            tool_name = m.group(1)
            inputs = {}
            json_str = m.group(2)
            if json_str:
                try:
                    obj = json.loads(json_str)
                    inputs = obj.get("input", obj.get("params", obj))
                    if "action" in obj or not inputs:
                        inputs = dict(obj)
                except (json.JSONDecodeError, TypeError):
                    pass
            key = f"{tool_name}:{json.dumps(inputs, sort_keys=True)}"
            if key not in seen:
                seen.add(key)
                results.append({"name": tool_name, "input": inputs})

        # Format B: JSON objects: {"tool": "X", "action": "Y", "params": {...}}
        #           or {"tool_call": {"name": "X", "input": {...}}}
        objects = AutonomousAgent._extract_json_objects(text)
        for obj in objects:
            normalized = AutonomousAgent._normalize_tool_call(obj)
            if normalized:
                key = f"{normalized['name']}:{json.dumps(normalized['input'], sort_keys=True)}"
                if key not in seen:
                    seen.add(key)
                    results.append(normalized)

        # Format C: Python-style: tool_name(key='value', key2='value2')
        python_calls = AutonomousAgent._parse_python_style(text)
        for pc in python_calls:
            key = f"{pc['name']}:{json.dumps(pc['input'], sort_keys=True)}"
            if key not in seen:
                seen.add(key)
                results.append(pc)

        return results

    @staticmethod
    def _parse_tool_call(text: str) -> dict | None:
        """Parse a single tool call. Returns None if text is a final answer."""
        calls = AutonomousAgent._parse_tool_calls(text)
        return calls[0] if calls else None

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
