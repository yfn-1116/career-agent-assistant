"""Mock model provider for testing and default rule-based fallback."""

from career_agent.models.provider import ModelProvider


class MockProvider(ModelProvider):
    """Return fixed or predictable responses — no network calls.

    Useful as the default provider when no real LLM is available, and
    as a test double that exposes the prompts it received.
    """

    def __init__(self, fixed_response: str | None = None) -> None:
        self._fixed = fixed_response
        self.last_prompt: str | None = None
        self.last_system_prompt: str | None = None
        self.last_metadata: dict | None = None
        self.call_count: int = 0

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.last_metadata = metadata or {}
        self.call_count += 1

        if self._fixed is not None:
            return self._fixed

        # Default: return a short indicator that the mock was used.
        return (
            "[MockProvider] 基于 "
            f"{len(prompt)} 字符的 prompt 生成。"
            f"system_prompt 长度: {len(system_prompt or '')}。"
        )
