"""LLM provider abstraction — pluggable backends with unified interface."""

from __future__ import annotations

from career_agent.infrastructure.llm.base import LLMProvider
from career_agent.infrastructure.llm.mock_provider import MockLLMProvider
from career_agent.core.settings import Settings


def create_llm_provider(
    provider: str = "mock",
    **kwargs,
) -> LLMProvider:
    """Factory: return an ``LLMProvider`` instance.

    Reads defaults from ``Settings.llm``; explicit kwargs override.

    Parameters
    ----------
    provider : str
        ``"mock"``, ``"qwen"``, or ``"deepseek"``.  If empty/unknown,
        falls back to the value of ``LLM_PROVIDER`` env var, then mock.
    **kwargs
        Passed to the provider constructor (api_key, model, etc.).
    """
    # Resolve provider name from Settings if not explicitly given
    if provider == "mock":
        s = Settings()
        if s.llm.provider != "mock":
            provider = s.llm.provider

    if provider == "qwen":
        from career_agent.infrastructure.llm.qwen_provider import QwenProvider
        return QwenProvider(**kwargs)
    if provider == "deepseek":
        from career_agent.infrastructure.llm.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider(**kwargs)
    return MockLLMProvider(**kwargs)


__all__ = [
    "LLMProvider",
    "MockLLMProvider",
    "create_llm_provider",
]
