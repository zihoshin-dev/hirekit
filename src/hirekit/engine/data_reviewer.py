"""DataReviewer — 수집 데이터 품질 사전 검토 게이트 (GPT Researcher 패턴)."""

from __future__ import annotations

from dataclasses import dataclass, field

from hirekit.sources.base import SourceResult

# Dimensions considered complete when at least one source covers them
_REQUIRED_DIMENSIONS = [
    "overview",
    "financials",
    "culture",
    "tech",
    "role",
]

# Completeness thresholds
_THRESHOLD_INSUFFICIENT = 0.4
_THRESHOLD_WARN = 0.7


@dataclass
class ReviewResult:
    """Output of DataReviewer.review()."""

    completeness_score: float  # 0.0–1.0
    missing_dimensions: list[str] = field(default_factory=list)
    low_confidence_warnings: list[str] = field(default_factory=list)
    recommendation: str = "proceed"  # "proceed" | "warn" | "insufficient"


class DataReviewer:
    """수집된 데이터의 품질을 사전 검토."""

    def review(self, source_results: list[SourceResult]) -> ReviewResult:
        """Evaluate completeness and confidence of collected source data.

        Parameters
        ----------
        source_results:
            List of :class:`~hirekit.sources.base.SourceResult` gathered by sources.

        Returns
        -------
        ReviewResult
            - ``completeness_score``: fraction of required dimensions covered (0.0–1.0)
            - ``missing_dimensions``: required dimensions with no data
            - ``low_confidence_warnings``: dimensions where average confidence < 0.5
            - ``recommendation``: ``"proceed"`` / ``"warn"`` / ``"insufficient"``
        """
        # Track which dimensions are covered and their confidence values
        covered: dict[str, list[float]] = {}
        for result in source_results:
            if result.raw:
                covered.setdefault(result.section, []).append(result.confidence)

        missing = [dim for dim in _REQUIRED_DIMENSIONS if dim not in covered]
        completeness = 1.0 - len(missing) / len(_REQUIRED_DIMENSIONS)

        low_confidence_warnings: list[str] = []
        for dim, confidences in covered.items():
            avg = sum(confidences) / len(confidences)
            if avg < 0.5:
                low_confidence_warnings.append(
                    f"{dim} (avg confidence: {avg:.2f})"
                )

        if completeness < _THRESHOLD_INSUFFICIENT:
            recommendation = "insufficient"
        elif completeness < _THRESHOLD_WARN or low_confidence_warnings:
            recommendation = "warn"
        else:
            recommendation = "proceed"

        return ReviewResult(
            completeness_score=round(completeness, 4),
            missing_dimensions=missing,
            low_confidence_warnings=low_confidence_warnings,
            recommendation=recommendation,
        )
