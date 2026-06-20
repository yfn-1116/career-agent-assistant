"""Abstract model provider interface."""

from abc import ABC, abstractmethod


class ModelProvider(ABC):
    """Minimal interface for pluggable LLM backends.

    Implementations should handle their own API details; callers only
    depend on this interface.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Return a generated text string for the given prompt."""
        ...
