from __future__ import annotations

from hirekit.engine.business_segments import summarize_growth_reality


class TestSummarizeGrowthReality:
    def test_growth_and_pension_signals_are_kept_separate(self):
        summary = summarize_growth_reality(
            {
                "dart": {"growth_reality": {"revenue_growth_rate": 12.5, "revenue_growth_direction": "growing"}},
                "pension": {
                    "employment_growth_reality": {"pension_members": 4321, "signal_quality": "official_headcount_proxy"}
                },
            }
        )

        assert summary["verified_facts"]["growth_reality"]["revenue_growth_direction"] == "growing"
        assert summary["verified_facts"]["employment_growth_reality"]["pension_members"] == 4321
        assert any("국민연금 가입자 수" in item for item in summary["interpretation"])

    def test_growth_direction_interpretation_handles_flat_case(self):
        summary = summarize_growth_reality(
            {
                "dart": {"growth_reality": {"revenue_growth_rate": 1.2, "revenue_growth_direction": "flat"}},
                "pension": {"employment_growth_reality": {}},
            }
        )

        assert summary["interpretation"] == ["매출 흐름이 비교적 안정적이에요."]
