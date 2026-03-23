"""Tests for hirekit.engine.data_reviewer — DataReviewer 품질 게이트."""

from __future__ import annotations

from hirekit.engine.data_reviewer import DataReviewer, ReviewResult
from hirekit.sources.base import SourceResult


def make_result(section: str, raw: str = "data", confidence: float = 1.0) -> SourceResult:
    return SourceResult(source_name="mock", section=section, raw=raw, confidence=confidence)


class TestReviewResultDefaults:
    def test_review_result_fields(self):
        r = ReviewResult(completeness_score=0.8)
        assert r.completeness_score == 0.8
        assert r.missing_dimensions == []
        assert r.low_confidence_warnings == []
        assert r.recommendation == "proceed"


class TestDataReviewerProceed:
    def test_all_required_dimensions_covered_returns_proceed(self):
        reviewer = DataReviewer()
        results = [
            make_result("overview"),
            make_result("financials"),
            make_result("culture"),
            make_result("tech"),
            make_result("role"),
        ]
        result = reviewer.review(results)
        assert result.recommendation == "proceed"
        assert result.completeness_score == 1.0
        assert result.missing_dimensions == []

    def test_completeness_score_is_float_between_0_and_1(self):
        reviewer = DataReviewer()
        result = reviewer.review([make_result("overview")])
        assert 0.0 <= result.completeness_score <= 1.0


class TestDataReviewerInsufficient:
    def test_empty_results_is_insufficient(self):
        reviewer = DataReviewer()
        result = reviewer.review([])
        assert result.recommendation == "insufficient"
        assert result.completeness_score == 0.0

    def test_one_dimension_is_insufficient(self):
        reviewer = DataReviewer()
        result = reviewer.review([make_result("overview")])
        assert result.recommendation == "insufficient"

    def test_all_missing_dimensions_listed(self):
        reviewer = DataReviewer()
        result = reviewer.review([])
        assert set(result.missing_dimensions) == {"overview", "financials", "culture", "tech", "role"}


class TestDataReviewerWarn:
    def test_partial_coverage_returns_warn(self):
        reviewer = DataReviewer()
        results = [
            make_result("overview"),
            make_result("financials"),
            make_result("culture"),
        ]
        result = reviewer.review(results)
        assert result.recommendation == "warn"
        assert "tech" in result.missing_dimensions
        assert "role" in result.missing_dimensions

    def test_low_confidence_triggers_warn(self):
        reviewer = DataReviewer()
        # All required dimensions present but one has low confidence
        results = [
            make_result("overview", confidence=0.2),
            make_result("financials"),
            make_result("culture"),
            make_result("tech"),
            make_result("role"),
        ]
        result = reviewer.review(results)
        assert result.recommendation == "warn"
        assert any("overview" in w for w in result.low_confidence_warnings)


class TestDataReviewerMissingDimensions:
    def test_results_without_raw_not_counted(self):
        reviewer = DataReviewer()
        results = [
            SourceResult(source_name="mock", section="overview", raw=""),  # empty raw
            make_result("financials"),
            make_result("culture"),
            make_result("tech"),
            make_result("role"),
        ]
        result = reviewer.review(results)
        assert "overview" in result.missing_dimensions

    def test_extra_dimensions_do_not_affect_required_coverage(self):
        reviewer = DataReviewer()
        results = [
            make_result("overview"),
            make_result("financials"),
            make_result("culture"),
            make_result("tech"),
            make_result("role"),
            make_result("leadership"),  # extra, not in required
        ]
        result = reviewer.review(results)
        assert result.completeness_score == 1.0
        assert result.recommendation == "proceed"


class TestDataReviewerLowConfidence:
    def test_confidence_above_threshold_no_warnings(self):
        reviewer = DataReviewer()
        results = [make_result("overview", confidence=0.9)]
        result = reviewer.review(results)
        assert result.low_confidence_warnings == []

    def test_confidence_below_threshold_warning_included(self):
        reviewer = DataReviewer()
        results = [make_result("tech", confidence=0.3)]
        result = reviewer.review(results)
        assert any("tech" in w for w in result.low_confidence_warnings)

    def test_multiple_results_same_section_averaged(self):
        reviewer = DataReviewer()
        # Two results for "overview": 0.1 and 0.9 → avg 0.5, not < 0.5
        results = [
            make_result("overview", confidence=0.1),
            make_result("overview", confidence=0.9),
        ]
        result = reviewer.review(results)
        assert not any("overview" in w for w in result.low_confidence_warnings)
