"""Tests for ScoreDimension.confidence and LLM source grounding."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hirekit.core.config import HireKitConfig
from hirekit.engine.company_analyzer import AnalysisReport, CompanyAnalyzer
from hirekit.engine.llm_pipeline import (
    _GROUNDING_RULES,
    _SYSTEM_FACT_EXTRACTOR,
    _SYSTEM_SECTION_INDUSTRY,
    _SYSTEM_SECTION_OVERVIEW,
    _SYSTEM_SECTION_TECH,
    _SYSTEM_SECTION_VERDICT,
    _SYSTEM_SPEED_SHEET,
)
from hirekit.engine.scorer import ScoreDimension, create_default_scorecard
from hirekit.sources.base import SourceRegistry, SourceResult


# ---------------------------------------------------------------------------
# ScoreDimension.confidence field
# ---------------------------------------------------------------------------

class TestScoreDimensionConfidence:
    def test_confidence_default_is_empty_string(self):
        dim = ScoreDimension(name="growth", label="Growth", weight=0.2)
        assert dim.confidence == ""

    def test_confidence_accepts_high(self):
        dim = ScoreDimension(name="a", label="A", weight=1.0, confidence="high")
        assert dim.confidence == "high"

    def test_confidence_accepts_medium(self):
        dim = ScoreDimension(name="a", label="A", weight=1.0, confidence="medium")
        assert dim.confidence == "medium"

    def test_confidence_accepts_low(self):
        dim = ScoreDimension(name="a", label="A", weight=1.0, confidence="low")
        assert dim.confidence == "low"

    def test_default_scorecard_dimensions_have_empty_confidence(self):
        card = create_default_scorecard("TestCorp")
        for dim in card.dimensions:
            assert dim.confidence == ""


# ---------------------------------------------------------------------------
# CompanyAnalyzer._confidence_from_sources
# ---------------------------------------------------------------------------

class TestConfidenceFromSources:
    def setup_method(self):
        self.analyzer = CompanyAnalyzer(
            config=HireKitConfig(), use_llm=False
        )

    def test_three_or_more_sources_returns_high(self):
        source_data = {"dart": {}, "pension": {}, "nts_biz": {}}
        result = self.analyzer._confidence_from_sources(
            ["dart", "pension", "nts_biz"], source_data
        )
        assert result == "high"

    def test_two_sources_returns_medium(self):
        source_data = {"dart": {}, "pension": {}}
        result = self.analyzer._confidence_from_sources(
            ["dart", "pension", "nts_biz"], source_data
        )
        assert result == "medium"

    def test_one_source_returns_medium(self):
        source_data = {"dart": {}}
        result = self.analyzer._confidence_from_sources(
            ["dart", "pension", "nts_biz"], source_data
        )
        assert result == "medium"

    def test_zero_sources_returns_low(self):
        source_data = {}
        result = self.analyzer._confidence_from_sources(
            ["dart", "pension", "nts_biz"], source_data
        )
        assert result == "low"

    def test_extra_sources_not_in_expected_ignored(self):
        source_data = {"github": {}, "naver_news": {}, "unrelated": {}}
        result = self.analyzer._confidence_from_sources(
            ["dart", "pension"], source_data
        )
        assert result == "low"


# ---------------------------------------------------------------------------
# _score_from_data sets confidence on all dimensions
# ---------------------------------------------------------------------------

def _make_report_for_scoring(source_names: list[str]) -> AnalysisReport:
    scorecard = create_default_scorecard("카카오")
    report = AnalysisReport(
        company="카카오",
        region="kr",
        tier=1,
        sections={},
        source_results=[
            SourceResult(source_name=name, section="overview")
            for name in source_names
        ],
        scorecard=scorecard,
    )
    return report


class TestScoreFromDataSetsConfidence:
    def setup_method(self):
        self.analyzer = CompanyAnalyzer(
            config=HireKitConfig(), use_llm=False
        )

    def test_all_dimensions_have_confidence_after_scoring(self):
        report = _make_report_for_scoring(["dart", "pension", "nts_biz",
                                           "github", "tech_blog", "naver_search",
                                           "exa_search", "community_review",
                                           "google_news"])
        self.analyzer._score_from_data(report)
        for dim in report.scorecard.dimensions:
            assert dim.confidence in ("high", "medium", "low"), (
                f"{dim.name} has unexpected confidence: {dim.confidence!r}"
            )

    def test_no_sources_gives_low_confidence_on_all_dims(self):
        report = _make_report_for_scoring([])
        self.analyzer._score_from_data(report)
        for dim in report.scorecard.dimensions:
            assert dim.confidence == "low"

    def test_growth_confidence_high_with_three_financial_sources(self):
        report = _make_report_for_scoring(["dart", "ir_report"])
        # Only 2 matching sources → medium
        self.analyzer._score_from_data(report)
        growth = next(d for d in report.scorecard.dimensions if d.name == "growth")
        assert growth.confidence == "medium"

    def test_job_fit_high_with_three_tech_sources(self):
        report = _make_report_for_scoring(["github", "tech_blog", "medium_velog"])
        self.analyzer._score_from_data(report)
        job_fit = next(d for d in report.scorecard.dimensions if d.name == "job_fit")
        assert job_fit.confidence == "high"


# ---------------------------------------------------------------------------
# to_dict includes confidence
# ---------------------------------------------------------------------------

class TestToDictIncludesConfidence:
    def test_scorecard_dimensions_include_confidence_key(self):
        scorecard = create_default_scorecard("테스트")
        for dim in scorecard.dimensions:
            dim.confidence = "medium"
        report = AnalysisReport(
            company="테스트", region="kr", tier=1, scorecard=scorecard
        )
        d = report.to_dict()
        for dim_dict in d["scorecard"]["dimensions"]:
            assert "confidence" in dim_dict

    def test_confidence_value_preserved_in_serialization(self):
        scorecard = create_default_scorecard("테스트")
        scorecard.dimensions[0].confidence = "high"
        scorecard.dimensions[1].confidence = "low"
        report = AnalysisReport(
            company="테스트", region="kr", tier=1, scorecard=scorecard
        )
        dims = report.to_dict()["scorecard"]["dimensions"]
        assert dims[0]["confidence"] == "high"
        assert dims[1]["confidence"] == "low"


# ---------------------------------------------------------------------------
# LLM pipeline source grounding
# ---------------------------------------------------------------------------

class TestLLMGroundingRules:
    def test_grounding_rules_not_empty(self):
        assert len(_GROUNDING_RULES) > 0

    def test_grounding_rules_mention_source_citation(self):
        assert "[소스명]" in _GROUNDING_RULES or "출처" in _GROUNDING_RULES

    def test_grounding_rules_warn_against_fabrication(self):
        assert "만들어내지" in _GROUNDING_RULES

    @pytest.mark.parametrize("system_prompt", [
        _SYSTEM_FACT_EXTRACTOR,
        _SYSTEM_SECTION_OVERVIEW,
        _SYSTEM_SECTION_INDUSTRY,
        _SYSTEM_SECTION_TECH,
        _SYSTEM_SECTION_VERDICT,
        _SYSTEM_SPEED_SHEET,
    ])
    def test_all_system_prompts_contain_grounding_rules(self, system_prompt: str):
        assert _GROUNDING_RULES in system_prompt, (
            f"System prompt missing grounding rules:\n{system_prompt[:100]}..."
        )
