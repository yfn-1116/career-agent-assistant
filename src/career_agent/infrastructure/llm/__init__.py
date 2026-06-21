"""LLM provider abstraction — pluggable backends with unified interface."""

from __future__ import annotations

from career_agent.infrastructure.llm.base import LLMProvider
from career_agent.infrastructure.llm.mock_provider import MockLLMProvider


def create_llm_provider(
    provider: str = "mock",
    **kwargs,
) -> LLMProvider:
    """Factory: return an ``LLMProvider`` instance by name.

    Parameters
    ----------
    provider : str
        ``"mock"``, ``"qwen"``, or ``"deepseek"``.
    **kwargs
        Passed to the provider constructor.

    Returns
    -------
    LLMProvider
        A concrete provider instance.  Falls back to ``MockLLMProvider``
        for unknown provider names.
    """
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
