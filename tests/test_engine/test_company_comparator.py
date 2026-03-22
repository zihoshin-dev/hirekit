"""Tests for company comparator engine."""

from __future__ import annotations

import pytest

from hirekit.engine.company_comparator import (
    CompanyComparator,
    ComparisonResult,
)


class TestComparisonResult:
    def _make_result(self, companies=None) -> ComparisonResult:
        companies = companies or ["토스", "카카오"]
        return ComparisonResult(
            companies=companies,
            dimensions={
                "growth": [4.5, 3.0],
                "compensation": [4.5, 4.0],
                "culture": [4.5, 3.5],
                "tech_level": [5.0, 4.0],
                "brand": [4.0, 5.0],
                "wlb": [3.5, 3.5],
                "remote": [3.0, 3.5],
            },
            winner_by_dimension={"growth": "토스", "brand": "카카오"},
            overall_scores={"토스": 82.0, "카카오": 74.0},
            overall_recommendation="토스 추천",
            comparison_table={},
        )

    def test_winner_property(self):
        result = self._make_result()
        assert result.winner == "토스"

    def test_winner_with_lower_score(self):
        result = self._make_result()
        result.overall_scores = {"토스": 60.0, "카카오": 80.0}
        assert result.winner == "카카오"

    def test_to_markdown_contains_companies(self):
        result = self._make_result()
        md = result.to_markdown()
        assert "토스" in md
        assert "카카오" in md

    def test_to_markdown_contains_dimensions(self):
        result = self._make_result()
        md = result.to_markdown()
        assert "성장성" in md
        assert "보상" in md
        assert "워라밸" in md

    def test_to_markdown_contains_scores(self):
        result = self._make_result()
        md = result.to_markdown()
        assert "82" in md or "74" in md

    def test_to_markdown_three_companies(self):
        result = ComparisonResult(
            companies=["토스", "카카오", "네이버"],
            dimensions={"growth": [4.5, 3.0, 3.5], "compensation": [4.5, 4.0, 4.0],
                        "culture": [4.5, 3.5, 3.5], "tech_level": [5.0, 4.0, 4.5],
                        "brand": [4.0, 5.0, 5.0], "wlb": [3.5, 3.5, 3.5],
                        "remote": [3.0, 3.5, 4.0]},
            winner_by_dimension={},
            overall_scores={"토스": 82.0, "카카오": 74.0, "네이버": 76.0},
            overall_recommendation="토스 추천",
            comparison_table={},
        )
        md = result.to_markdown()
        assert "네이버" in md


class TestCompanyComparator:
    def setup_method(self):
        self.comparator = CompanyComparator()

    def test_compare_returns_result(self):
        result = self.comparator.compare("토스", "카카오")
        assert isinstance(result, ComparisonResult)

    def test_compare_sets_companies(self):
        result = self.comparator.compare("토스", "카카오")
        assert "토스" in result.companies
        assert "카카오" in result.companies

    def test_compare_many_two(self):
        result = self.comparator.compare_many(["토스", "네이버"])
        assert len(result.companies) == 2

    def test_compare_many_three(self):
        result = self.comparator.compare_many(["토스", "카카오", "네이버"])
        assert len(result.companies) == 3

    def test_compare_many_requires_at_least_two(self):
        with pytest.raises(ValueError):
            self.comparator.compare_many(["토스"])

    def test_compare_many_caps_at_five(self):
        result = self.comparator.compare_many(
            ["토스", "카카오", "네이버", "쿠팡", "배달의민족", "당근마켓"]
        )
        assert len(result.companies) <= 5

    def test_overall_scores_all_companies_present(self):
        result = self.comparator.compare("토스", "카카오")
        assert "토스" in result.overall_scores
        assert "카카오" in result.overall_scores

    def test_overall_scores_in_range(self):
        result = self.comparator.compare("토스", "카카오")
        for score in result.overall_scores.values():
            assert 0 <= score <= 100

    def test_winner_by_dimension_populated(self):
        result = self.comparator.compare("토스", "카카오")
        assert len(result.winner_by_dimension) > 0

    def test_dimensions_contain_all_keys(self):
        result = self.comparator.compare("토스", "카카오")
        expected_dims = {"growth", "compensation", "culture", "tech_level", "brand", "wlb", "remote"}
        assert expected_dims.issubset(set(result.dimensions.keys()))

    def test_dimension_scores_length_matches_companies(self):
        result = self.comparator.compare_many(["토스", "카카오", "네이버"])
        for dim, scores in result.dimensions.items():
            assert len(scores) == 3

    def test_overall_recommendation_non_empty(self):
        result = self.comparator.compare("토스", "카카오")
        assert isinstance(result.overall_recommendation, str)
        assert len(result.overall_recommendation) > 0

    def test_comparison_table_has_companies(self):
        result = self.comparator.compare("토스", "카카오")
        assert "companies" in result.comparison_table

    def test_winner_is_one_of_compared(self):
        result = self.comparator.compare("토스", "카카오")
        assert result.winner in result.companies

    def test_unknown_company_no_error(self):
        """Unknown companies use neutral defaults — should not raise."""
        result = self.comparator.compare("알수없는기업xyz", "카카오")
        assert isinstance(result, ComparisonResult)
        assert len(result.companies) == 2

    def test_unknown_company_gets_default_score(self):
        result = self.comparator.compare("미지기업abc", "카카오")
        # Unknown company should have a score in 0-100
        for score in result.overall_scores.values():
            assert 0 <= score <= 100

    def test_english_company_names(self):
        result = self.comparator.compare("toss", "kakao")
        assert isinstance(result, ComparisonResult)
        assert result.overall_scores.get("toss", 0) > 0

    def test_to_markdown_output(self):
        result = self.comparator.compare("토스", "카카오")
        md = result.to_markdown()
        assert "토스" in md
        assert "카카오" in md
        assert "추천" in md

    def test_toss_high_tech_score(self):
        """Toss should have tech_level >= 4.5 in known data."""
        result = self.comparator.compare("토스", "당근마켓")
        toss_idx = result.companies.index("토스")
        toss_tech = result.dimensions["tech_level"][toss_idx]
        assert toss_tech >= 4.5

    def test_google_compensation_highest(self):
        result = self.comparator.compare_many(["google", "토스", "카카오"])
        google_idx = result.companies.index("google")
        google_comp = result.dimensions["compensation"][google_idx]
        assert google_comp >= 4.5

    def test_compare_same_company_twice(self):
        """Comparing a company against itself should not error."""
        result = self.comparator.compare("토스", "토스")
        assert isinstance(result, ComparisonResult)
