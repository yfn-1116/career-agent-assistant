"""Shared score validation — extracted so domain and grading share the same rules."""

from __future__ import annotations

import math

MIN_SCORE = 0.0
MAX_SCORE = 1.0


def validate_score(value: object, name: str = "score") -> float:
    """Validate and normalise a score value.

    Returns the value as a ``float`` if it is a finite number in
    [``MIN_SCORE``, ``MAX_SCORE``].  Raises ``ValueError`` otherwise.

    **Rejected**: ``bool``, ``None``, ``str``, ``NaN``, ``inf``, ``-inf``,
    values outside [0.0, 1.0].
    """
    if isinstance(value, bool):
        raise ValueError(f"{name} must be float, got bool")
    if not isinstance(value, (int, float)):
        raise ValueError(
            f"{name} must be float, got {type(value).__name__}"
        )
    if value is None:
        raise ValueError(f"{name} must be float, got None")

    score = float(value)
    if not math.isfinite(score):
        raise ValueError(f"{name} must be finite, got {score}")
    if score < MIN_SCORE or score > MAX_SCORE:
        raise ValueError(
            f"{name} must be in [{MIN_SCORE}, {MAX_SCORE}], got {score}"
        )
    return score
