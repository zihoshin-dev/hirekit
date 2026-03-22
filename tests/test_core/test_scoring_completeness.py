"""Tests for report_completeness quality metric."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hirekit.core.scoring import report_completeness
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.scorer import ScoreDimension, Scorecard, create_default_scorecard
from hirekit.sources.base import SourceResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fresh_result(source_name: str, section: str = "overview") -> SourceResult:
    return SourceResult(
        source_name=source_name,
        section=section,
        collected_at=datetime.now(UTC).isoformat(),
    )


def make_stale_result(source_name: str, section: str = "overview") -> SourceResult:
    stale_ts = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    return SourceResult(
        source_name=source_name,
        section=section,
        collected_at=stale_ts,
    )


def make_report(
    sections: dict | None = None,
    source_results: list[SourceResult] | None = None,
    score: float = 3.0,
    evidence: str = "매출 성장률 +20%",
) -> AnalysisReport:
    scorecard = create_default_scorecard("테스트")
    for dim in scorecard.dimensions:
        dim.score = score
        dim.evidence = evidence
    return AnalysisReport(
        company="테스트",
        region="kr",
        tier=1,
        sections=sections or {},
        source_results=source_results or [],
        scorecard=scorecard,
    )


# ---------------------------------------------------------------------------
# Return range
# ---------------------------------------------------------------------------

class TestReportCompletenessRange:
    def test_returns_float(self):
        report = make_report()
        result = report_completeness(report)
        assert isinstance(result, float)

    def test_score_between_0_and_1(self):
        report = make_report()
        assert 0.0 <= report_completeness(report) <= 1.0

    def test_empty_report_gives_low_score(self):
        report = AnalysisReport(company="빈회사", region="kr", tier=1)
        score = report_completeness(report)
        assert score < 0.3

    def test_fully_populated_report_gives_high_score(self):
        # All 12 sections filled, 14 sources, good evidence
        sections = {i: {"data": f"섹션{i} 내용"} for i in range(1, 13)}
        sources = [
            make_fresh_result(f"source_{i}", "overview") for i in range(14)
        ]
        report = make_report(sections=sections, source_results=sources)
        score = report_completeness(report)
        assert score >= 0.7

    def test_invalid_type_raises_type_error(self):
        with pytest.raises(TypeError):
            report_completeness("not a report")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# sections_filled component (weight 0.30)
# ---------------------------------------------------------------------------

class TestSectionsFilled:
    def test_no_sections_gives_zero_component(self):
        report = make_report(sections={})
        score = report_completeness(report)
        # sections_filled = 0, other components may still contribute
        assert score < 0.5

    def test_more_sections_gives_higher_score(self):
        report_few = make_report(sections={1: {"a": "b"}})
        report_many = make_report(
            sections={i: {"a": "b"} for i in range(1, 7)}
        )
        assert report_completeness(report_few) < report_completeness(report_many)

    def test_12_sections_maxes_sections_component(self):
        sections_full = {i: {"x": "y"} for i in range(1, 13)}
        sections_half = {i: {"x": "y"} for i in range(1, 7)}
        report_full = make_report(sections=sections_full)
        report_half = make_report(sections=sections_half)
        assert report_completeness(report_full) > report_completeness(report_half)


# ---------------------------------------------------------------------------
# evidence_quality component (weight 0.25)
# ---------------------------------------------------------------------------

class TestEvidenceQuality:
    def test_empty_evidence_reduces_score(self):
        report_good = make_report(evidence="매출 성장률 +20%")
        report_bad = make_report(evidence="")
        assert report_completeness(report_good) > report_completeness(report_bad)

    def test_placeholder_evidence_treated_as_missing(self):
        report_placeholder = make_report(evidence="데이터 없음")
        report_real = make_report(evidence="GitHub 기술 성숙도 75/100")
        assert report_completeness(report_real) > report_completeness(report_placeholder)

    def test_no_scorecard_gives_zero_evidence_score(self):
        report = AnalysisReport(company="테스트", region="kr", tier=1)
        # scorecard is None → evidence_quality = 0
        score = report_completeness(report)
        assert score < 0.5


# ---------------------------------------------------------------------------
# source_diversity component (weight 0.20)
# ---------------------------------------------------------------------------

class TestSourceDiversity:
    def test_more_unique_sources_gives_higher_score(self):
        report_few = make_report(source_results=[make_fresh_result("dart")])
        report_many = make_report(source_results=[
            make_fresh_result(f"src_{i}") for i in range(10)
        ])
        assert report_completeness(report_few) < report_completeness(report_many)

    def test_duplicate_source_names_counted_once(self):
        # Same source_name repeated — unique count is 1
        report_dupes = make_report(source_results=[
            make_fresh_result("dart"),
            make_fresh_result("dart"),
            make_fresh_result("dart"),
        ])
        report_unique = make_report(source_results=[
            make_fresh_result("dart"),
            make_fresh_result("github"),
            make_fresh_result("naver_news"),
        ])
        assert report_completeness(report_dupes) < report_completeness(report_unique)


# ---------------------------------------------------------------------------
# data_freshness component (weight 0.15)
# ---------------------------------------------------------------------------

class TestDataFreshness:
    def test_all_fresh_beats_all_stale(self):
        report_fresh = make_report(source_results=[
            make_fresh_result("dart"),
            make_fresh_result("github"),
        ])
        report_stale = make_report(source_results=[
            make_stale_result("dart"),
            make_stale_result("github"),
        ])
        assert report_completeness(report_fresh) > report_completeness(report_stale)

    def test_no_sources_freshness_zero(self):
        report = make_report(source_results=[])
        # freshness component = 0 — score still bounded in [0, 1]
        score = report_completeness(report)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# no_placeholder component (weight 0.10)
# ---------------------------------------------------------------------------

class TestNoPlaceholder:
    def test_placeholder_text_reduces_score(self):
        report_clean = make_report(sections={1: {"info": "매출 1조원"}})
        report_dirty = make_report(sections={1: {"info": "—"}})
        assert report_completeness(report_clean) > report_completeness(report_dirty)

    def test_multiple_placeholders_penalised(self):
        report_many_placeholders = make_report(sections={
            1: {"a": "—", "b": "데이터 없음"},
        })
        report_clean = make_report(sections={
            1: {"a": "정보1", "b": "정보2"},
        })
        assert report_completeness(report_clean) > report_completeness(report_many_placeholders)
