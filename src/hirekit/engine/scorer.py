"""Weighted multi-dimensional scoring engine for company evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreDimension:
    """A single scoring dimension with weight and evidence."""

    name: str
    label: str
    weight: float  # 0.0-1.0, sum of all weights = 1.0
    score: float = 0.0  # 1-5 raw score
    evidence: str = ""  # data-backed justification
    source: str = ""  # which data source provided this


@dataclass
class Scorecard:
    """Multi-dimensional company scorecard (100-point scale)."""

    company: str
    dimensions: list[ScoreDimension] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        """Weighted sum normalized to 100."""
        return sum(d.score * d.weight for d in self.dimensions) * 20

    @property
    def grade(self) -> str:
        """Letter grade from total score."""
        from hirekit.core.scoring import score_to_grade
        return score_to_grade(self.total_score)

    def summary(self) -> str:
        """One-line summary for terminal output."""
        return f"{self.company}: {self.total_score:.0f}/100 (Grade {self.grade})"


# Default scoring dimensions — user can override in config.toml
DEFAULT_DIMENSIONS: list[dict[str, str | float]] = [
    {"name": "job_fit", "label": "Job Fit", "weight": 0.30},
    {"name": "career_leverage", "label": "Career Leverage", "weight": 0.20},
    {"name": "growth", "label": "Growth Potential", "weight": 0.20},
    {"name": "compensation", "label": "Compensation & Benefits", "weight": 0.15},
    {"name": "culture_fit", "label": "Culture Fit", "weight": 0.15},
]


def create_default_scorecard(company: str) -> Scorecard:
    """Create a scorecard with default dimensions (scores not yet filled)."""
    dimensions = [
        ScoreDimension(
            name=str(d["name"]),
            label=str(d["label"]),
            weight=float(d["weight"]),
        )
        for d in DEFAULT_DIMENSIONS
    ]
    return Scorecard(company=company, dimensions=dimensions)
