"""Tests for AutonomousAgent."""
import pytest
from career_agent.agents.autonomous_agent import AutonomousAgent, AgentStep, AutonomousResult
from career_agent.infrastructure.llm.mock_provider import MockLLMProvider
from career_agent.agents.memory import ConversationMemory


class TestToolCallParsing:
    def test_parse_direct_json(self):
        text = '{"tool_call": {"name": "parse_jd", "input": {"raw_jd": "test"}}}'
        result = AutonomousAgent._parse_tool_call(text)
        assert result == {"name": "parse_jd", "input": {"raw_jd": "test"}}

    def test_parse_code_fence(self):
        text = '```json\n{"tool_call": {"name": "github_repo", "input": {"repo_name": "a/b"}}}\n```'
        result = AutonomousAgent._parse_tool_call(text)
        assert result == {"name": "github_repo", "input": {"repo_name": "a/b"}}

    def test_no_tool_call_returns_none(self):
        assert AutonomousAgent._parse_tool_call("你好，这是普通回答") is None

    def test_empty_returns_none(self):
        assert AutonomousAgent._parse_tool_call("") is None


class TestAutonomousAgent:
    def test_simple_answer_no_tools(self):
        """LLM directly answers without calling tools."""
        llm = MockLLMProvider(fixed_response="你好，有什么可以帮助你的？")
        agent = AutonomousAgent(llm=llm)
        result = agent.run("你好")
        assert isinstance(result, AutonomousResult)
        assert "你好" in result.answer
        assert result.total_tools_called == 0

    def test_single_tool_call(self):
        """LLM calls one tool, gets result, then answers."""
        responses = [
            '{"tool_call": {"name": "web_search", "input": {"query": "test"}}}',
            "根据搜索结果，找到以下信息...",
        ]
        call_count = [0]

        class SequentialMock(MockLLMProvider):
            def generate(self, prompt, *, system_prompt=None):
                idx = call_count[0]
                call_count[0] += 1
                return responses[min(idx, len(responses) - 1)]

        llm = SequentialMock()
        agent = AutonomousAgent(llm=llm)
        result = agent.run("搜索 test")
        assert result.total_tools_called >= 1
        assert len(result.steps) >= 1

    def test_multi_step_tool_calls(self):
        """LLM calls multiple tools in sequence."""
        responses = [
            '{"tool_call": {"name": "parse_jd", "input": {"raw_jd": "JD text"}}}',
            '{"tool_call": {"name": "retrieve_profile", "input": {"queries": ["Python"]}}}',
            "匹配度 74%，建议投递。",
        ]
        call_count = [0]

        class SequentialMock(MockLLMProvider):
            def generate(self, prompt, *, system_prompt=None):
                idx = call_count[0]
                call_count[0] += 1
                return responses[min(idx, len(responses) - 1)]

        llm = SequentialMock()
        agent = AutonomousAgent(llm=llm)
        result = agent.run("分析这个 JD")
        assert result.total_tools_called >= 2
        assert len(result.steps) >= 2
        assert result.steps[0].tool_called == "parse_jd"
        assert result.steps[1].tool_called == "retrieve_profile"

    def test_max_steps_limit(self):
        """Agent terminates at max_steps even if LLM keeps calling tools."""
        responses = ['{"tool_call": {"name": "web_search", "input": {"query": "x"}}}'] * 20
        call_count = [0]

        class InfiniteMock(MockLLMProvider):
            def generate(self, prompt, *, system_prompt=None):
                idx = call_count[0]
                call_count[0] += 1
                return responses[min(idx, len(responses) - 1)]

        llm = InfiniteMock()
        agent = AutonomousAgent(llm=llm, max_steps=3)
        result = agent.run("test")
        assert result.total_tools_called <= 3
        assert len(result.steps) <= 3

    def test_memory_recorded(self):
        llm = MockLLMProvider(fixed_response="好的，已帮你完成。")
        memory = ConversationMemory()
        agent = AutonomousAgent(llm=llm, memory=memory)
        agent.run("帮我看看")
        ctx = memory.get_context(n=5)
        assert len(ctx) == 2  # user + assistant
        assert ctx[0].role == "user"


class TestAgentStep:
    def test_step_fields(self):
        step = AgentStep(step=1, tool_called="parse_jd", tool_input='{}',
                         tool_output="ok", duration_ms=12.5)
        assert step.step == 1
        assert step.tool_called == "parse_jd"
        assert step.success is True
