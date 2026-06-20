"""Evaluation data structures for lightweight output quality assessment."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationItem:
    """A single evaluation check result."""

    name: str = ""
    passed: bool = False
    score: float = 0.0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Aggregated evaluation report for one workflow run."""

    case_id: str = ""
    job_file: str = ""
    total_score: float = 0.0
    items: list[EvaluationItem] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
