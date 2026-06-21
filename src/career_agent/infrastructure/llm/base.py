"""Abstract LLM provider interface — pluggable backend for text generation."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Minimal, industrial-grade LLM backend interface.

    Implementations handle API details; callers only depend on this ABC.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Return a generated text string for the given prompt."""

    def generate_structured(
        self,
        prompt: str,
        *,
        schema: dict | None = None,
        system_prompt: str | None = None,
    ) -> dict:
        """Return a structured dict — default asks LLM for JSON, subclasses may override."""
        import json as _json

        sys = (system_prompt or "") + (
            "\n\n你必须严格以 JSON 格式返回结果，不要加任何解释或 markdown 标记。"
        )
        raw = self.generate(prompt, system_prompt=sys)
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.rstrip().endswith("```"):
                text = text.rstrip()[: -3]
        try:
            return _json.loads(text)
        except _json.JSONDecodeError:
            return {"_raw": raw}

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """True if this provider is configured and ready to call."""
