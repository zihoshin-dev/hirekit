"""Shared scoring utilities — deduplicated grade calculation."""

from __future__ import annotations

import datetime

_PLACEHOLDER_TOKENS = {"—", "데이터 없음", "N/A", "없음", "미확인"}


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


def report_completeness(report: object) -> float:  # type: ignore[type-arg]
    """리포트 품질 점수 0.0-1.0 (HireKit의 val_bpb).

    Parameters
    ----------
    report:
        ``AnalysisReport`` instance (typed as ``object`` to avoid circular import).

    Returns
    -------
    float
        Weighted quality score in [0.0, 1.0].
    """
    # Import here to avoid circular dependency at module level.
    from hirekit.engine.company_analyzer import AnalysisReport  # noqa: PLC0415

    if not isinstance(report, AnalysisReport):
        raise TypeError(f"Expected AnalysisReport, got {type(report)}")

    weights = {
        "sections_filled": 0.30,
        "evidence_quality": 0.25,
        "source_diversity": 0.20,
        "data_freshness": 0.15,
        "no_placeholder": 0.10,
    }

    # 1. sections_filled — 12 canonical sections (1-12)
    total_sections = 12
    filled = len([k for k in report.sections if report.sections[k]])
    sections_score = min(1.0, filled / total_sections)

    # 2. evidence_quality — scorecard dimensions with non-empty evidence
    if report.scorecard and report.scorecard.dimensions:
        dims = report.scorecard.dimensions
        with_evidence = sum(
            1 for d in dims
            if d.evidence and d.evidence not in _PLACEHOLDER_TOKENS
        )
        evidence_score = with_evidence / len(dims)
    else:
        evidence_score = 0.0

    # 3. source_diversity — collected sources / total available source classes
    _TOTAL_AVAILABLE_SOURCES = 14  # built-in source count (kr + global)
    collected = len(set(r.source_name for r in report.source_results))
    source_score = min(1.0, collected / _TOTAL_AVAILABLE_SOURCES)

    # 4. data_freshness — fraction of source_results collected within 90 days
    if report.source_results:
        fresh = sum(1 for r in report.source_results if not r.is_stale)
        freshness_score = fresh / len(report.source_results)
    else:
        freshness_score = 0.0

    # 5. no_placeholder — sections text without placeholder tokens
    all_values: list[str] = []
    for sec_data in report.sections.values():
        if isinstance(sec_data, dict):
            for v in sec_data.values():
                if isinstance(v, str):
                    all_values.append(v)

    if all_values:
        clean = sum(
            1 for v in all_values
            if not any(tok in v for tok in _PLACEHOLDER_TOKENS)
        )
        placeholder_score = clean / len(all_values)
    else:
        placeholder_score = 1.0  # no text ⇒ no placeholders

    scores = {
        "sections_filled": sections_score,
        "evidence_quality": evidence_score,
        "source_diversity": source_score,
        "data_freshness": freshness_score,
        "no_placeholder": placeholder_score,
    }

    return sum(weights[k] * scores[k] for k in weights)
