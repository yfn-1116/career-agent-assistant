"""Tests for LLM provider abstraction."""

import json
import os
from unittest.mock import patch

import pytest

from career_agent.infrastructure.llm.mock_provider import MockLLMProvider
from career_agent.infrastructure.llm.base import LLMProvider


# ---------------------------------------------------------------------------
# MockLLMProvider
# ---------------------------------------------------------------------------


class TestMockLLMProvider:
    def test_generate_returns_string(self):
        p = MockLLMProvider()
        result = p.generate("hello")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_includes_prompt_info(self):
        p = MockLLMProvider(fixed_response="固定回复")
        result = p.generate("test prompt")
        assert result == "固定回复"

    def test_generate_structured_returns_dict(self):
        p = MockLLMProvider()
        result = p.generate_structured(
            "extract skills",
            schema={"type": "object", "properties": {"skills": {"type": "array", "items": {"type": "string"}}}},
        )
        assert isinstance(result, dict)
        assert "skills" in result
        assert isinstance(result["skills"], list)

    def test_generate_structured_with_fixed_json(self):
        p = MockLLMProvider(fixed_json={"name": "test", "score": 0.9})
        result = p.generate_structured("prompt", schema={})
        assert result == {"name": "test", "score": 0.9}

    def test_model_name(self):
        p = MockLLMProvider()
        assert p.model_name == "mock"

    def test_is_available(self):
        p = MockLLMProvider()
        assert p.is_available is True

    def test_exposes_last_prompt(self):
        p = MockLLMProvider()
        p.generate("test prompt", system_prompt="be helpful")
        assert "test prompt" in p.last_prompt
        assert p.last_system_prompt == "be helpful"


# ---------------------------------------------------------------------------
# QwenProvider
# ---------------------------------------------------------------------------


class TestQwenProvider:
    def test_not_available_without_api_key(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": ""}):
            from career_agent.infrastructure.llm.qwen_provider import QwenProvider
            p = QwenProvider()
            assert not p.is_available

    def test_available_with_api_key(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": "sk-test-key"}):
            from career_agent.infrastructure.llm.qwen_provider import QwenProvider
            p = QwenProvider()
            assert p.is_available
            assert p.model_name == "qwen-plus"

    def test_reads_model_from_env(self):
        with patch.dict(os.environ, {
            "QWEN_API_KEY": "sk-test",
            "QWEN_MODEL": "qwen-max",
            "QWEN_BASE_URL": "https://custom.api.com/v1",
            "QWEN_TIMEOUT": "60",
        }):
            from career_agent.infrastructure.llm.qwen_provider import QwenProvider
            p = QwenProvider()
            assert p.model == "qwen-max"
            assert p.base_url == "https://custom.api.com/v1"
            assert p.timeout == 60

    def test_missing_key_raises_on_generate(self):
        with patch.dict(os.environ, {"QWEN_API_KEY": ""}):
            from career_agent.infrastructure.llm.qwen_provider import QwenProvider
            p = QwenProvider()
            with pytest.raises(RuntimeError, match="未设置"):
                p.generate("test")


# ---------------------------------------------------------------------------
# DeepSeekProvider
# ---------------------------------------------------------------------------


class TestDeepSeekProvider:
    def test_not_available_without_api_key(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            from career_agent.infrastructure.llm.deepseek_provider import DeepSeekProvider
            p = DeepSeekProvider()
            assert not p.is_available

    def test_available_with_api_key(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-test-key"}):
            from career_agent.infrastructure.llm.deepseek_provider import DeepSeekProvider
            p = DeepSeekProvider()
            assert p.is_available

    def test_missing_key_raises_on_generate(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}):
            from career_agent.infrastructure.llm.deepseek_provider import DeepSeekProvider
            p = DeepSeekProvider()
            with pytest.raises(RuntimeError, match="未设置"):
                p.generate("test")


# ---------------------------------------------------------------------------
# LLMProvider ABC
# ---------------------------------------------------------------------------


class TestLLMProviderABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_mock_is_instance(self):
        p = MockLLMProvider()
        assert isinstance(p, LLMProvider)


# ---------------------------------------------------------------------------
# LLMProvider factory
# ---------------------------------------------------------------------------


class TestLLMProviderFactory:
    def test_create_mock(self):
        from career_agent.infrastructure.llm import create_llm_provider
        p = create_llm_provider("mock")
        assert isinstance(p, MockLLMProvider)
        assert p.is_available

    def test_create_qwen_no_key(self):
        from career_agent.infrastructure.llm import create_llm_provider
        with patch.dict(os.environ, {"QWEN_API_KEY": ""}):
            p = create_llm_provider("qwen")
            assert not p.is_available

    def test_create_unknown_falls_back_to_mock(self):
        from career_agent.infrastructure.llm import create_llm_provider
        p = create_llm_provider("unknown_provider")
        assert isinstance(p, MockLLMProvider)
