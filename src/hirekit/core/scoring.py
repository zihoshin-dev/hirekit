"""Shared scoring utilities — deduplicated grade calculation."""

from __future__ import annotations

import datetime


def score_to_grade(score: float, thresholds: tuple[float, ...] = (80, 65, 50, 35)) -> str:
    """Convert a numeric score to letter grade.

    Default thresholds: S >= 80, A >= 65, B >= 50, C >= 35, D < 35.
    """
    grades = ("S", "A", "B", "C", "D")
    for threshold, grade in zip(thresholds, grades):
        if score >= threshold:
            return grade
    return grades[-1]


def current_year() -> int:
    """Get current year (avoids hardcoded year strings)."""
    return datetime.date.today().year
