"""Tool abstraction — every capability is a registered Tool."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Structured result from a tool invocation."""

    success: bool = False
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    summary: str = ""
    duration_ms: float = 0.0
    state_changes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": dict(self.output),
            "error": self.error,
            "summary": self.summary,
            "duration_ms": self.duration_ms,
            "state_changes": list(self.state_changes),
        }


class Tool(ABC):
    """Abstract tool — every agent capability is a Tool.

    Subclasses must implement ``name``, ``description``, and ``run()``.
    ``input_schema``, ``output_schema``, and ``safety_notes`` have
    sensible defaults.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable one-line description."""

    @property
    def input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    @property
    def output_schema(self) -> dict[str, Any]:
        return {"type": "object"}

    @property
    def safety_notes(self) -> list[str]:
        return []

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool and return a structured result."""
