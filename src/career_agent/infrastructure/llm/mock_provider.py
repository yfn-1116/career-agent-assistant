"""Mock LLM provider — deterministic, no network, for testing and fallback."""

from __future__ import annotations

from career_agent.infrastructure.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Return fixed or predictable responses — no network calls.

    Parameters
    ----------
    fixed_response : str or None
        If set, ``generate()`` always returns this string.
    fixed_json : dict or None
        If set, ``generate_structured()`` returns this dict.
    """

    def __init__(
        self,
        fixed_response: str | None = None,
        fixed_json: dict | None = None,
    ) -> None:
        self._fixed = fixed_response
        self._fixed_json = fixed_json
        self.last_prompt: str = ""
        self.last_system_prompt: str | None = None
        self.call_count: int = 0

    # -- LLMProvider interface ----------------------------------------------

    @property
    def model_name(self) -> str:
        return "mock"

    @property
    def is_available(self) -> bool:
        return True

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.call_count += 1

        if self._fixed is not None:
            return self._fixed

        return (
            f"[MockLLM] 基于 {len(prompt)} 字符的 prompt 生成。"
            f"system_prompt 长度: {len(system_prompt or '')}。"
        )

    def generate_structured(
        self,
        prompt: str,
        *,
        schema: dict | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.call_count += 1

        if self._fixed_json is not None:
            return dict(self._fixed_json)

        # Default: return a placeholder that matches common schemas
        if schema and "properties" in schema:
            result: dict = {}
            for key, prop in schema["properties"].items():
                ptype = prop.get("type", "string")
                if ptype == "array":
                    result[key] = []
                elif ptype == "number":
                    result[key] = 0.5
                elif ptype == "boolean":
                    result[key] = False
                else:
                    result[key] = f"[mock {key}]"
            return result

        return {"_mock": True, "prompt_length": len(prompt)}
