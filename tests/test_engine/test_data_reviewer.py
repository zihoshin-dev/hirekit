"""Tests for hirekit.engine.data_reviewer — DataReviewer 품질 게이트."""

from __future__ import annotations

from typing import Any

from hirekit.core.trust_contract import SourceAuthority, TrustLabel
from hirekit.engine.data_reviewer import DataReviewer, ReviewResult
from hirekit.sources.base import SourceResult


def make_result(
    section: str,
    raw: str = "data",
    confidence: float = 1.0,
    *,
    source_name: str = "mock",
    data: dict[str, Any] | None = None,
    trust_label: TrustLabel = "verified",
    source_authority: SourceAuthority | None = None,
    url: str = "",
) -> SourceResult:
    return SourceResult(
        source_name=source_name,
        section=section,
        raw=raw,
        confidence=confidence,
        data=data or {},
        trust_label=trust_label,
        source_authority=source_authority,
        url=url,
    )


class TestReviewResultDefaults:
    def test_review_result_fields(self):
        r = ReviewResult(completeness_score=0.8)
        assert r.completeness_score == 0.8
        assert r.missing_dimensions == []
        assert r.low_confidence_warnings == []
        assert r.recommendation == "proceed"
        assert set(r.intelligence_layer) == {
            "leadership",
            "org_health",
            "strategic_direction",
        }


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


class TestDataReviewerOrgHealthTraceability:
    def test_org_health_traceability_keeps_layers_separate_and_traceable(self):
        reviewer = DataReviewer()
        results = [
            make_result(
                "strategy",
                source_name="ir_report",
                source_authority="official",
                data={
                    "leadership_evidence": [
                        {
                            "claim_key": "leadership_stability",
                            "summary": "사업보고서에 현 경영진 체계가 유지된다고 공시됨",
                            "status": "stable",
                            "trust_label": "verified",
                            "evidence_id": "ir_report:leadership:stability",
                        }
                    ],
                    "org_health_evidence": [
                        {
                            "claim_key": "governance_health",
                            "summary": "지배구조와 주요 주주 현황이 공식 공시에 포함됨",
                            "status": "stable",
                            "trust_label": "verified",
                            "evidence_id": "ir_report:org_health:governance",
                        }
                    ],
                    "strategic_direction_evidence": [
                        {
                            "claim_key": "ai_expansion",
                            "summary": "사업보고서에 AI 인프라 투자 방향이 명시됨",
                            "status": "declared",
                            "trust_label": "verified",
                            "evidence_id": "ir_report:strategy:ai_expansion",
                        }
                    ],
                },
            ),
            make_result(
                "strategy",
                source_name="credible_news",
                source_authority="credible_reporting",
                trust_label="supporting",
                data={
                    "leadership_evidence": [
                        {
                            "claim_key": "leadership_stability",
                            "summary": "Reuters가 경영진 교체 가능성을 보도함",
                            "status": "transition",
                            "trust_label": "supporting",
                            "evidence_id": "credible_news:leadership:transition",
                        }
                    ],
                    "org_health_evidence": [
                        {
                            "claim_key": "governance_health",
                            "summary": "Reuters가 구조조정과 조직 불안 신호를 보도함",
                            "status": "concern",
                            "trust_label": "supporting",
                            "evidence_id": "credible_news:org_health:concern",
                        }
                    ],
                },
                url="https://example.com/reuters-story",
            ),
            make_result(
                "culture",
                source_name="community_review",
                source_authority="community",
                trust_label="supporting",
                data={
                    "org_health_evidence": [
                        {
                            "claim_key": "attrition_signal",
                            "summary": "커뮤니티 후기에서 최근 퇴사 압박 이야기가 반복됨",
                            "status": "concern",
                            "trust_label": "supporting",
                            "evidence_id": "community_review:org_health:attrition",
                        }
                    ]
                },
            ),
        ]

        result = reviewer.review(results)

        leadership = result.intelligence_layer["leadership"]
        org_health = result.intelligence_layer["org_health"]
        strategic_direction = result.intelligence_layer["strategic_direction"]

        assert leadership["state"] == "contradictory"
        assert [item["source_name"] for item in leadership["verified_facts"]] == ["ir_report"]
        assert [item["source_name"] for item in leadership["supporting_signals"]] == ["credible_news"]
        assert leadership["contradictions"][0]["claim_key"] == "leadership_stability"

        assert org_health["state"] == "contradictory"
        assert [item["source_name"] for item in org_health["verified_facts"]] == ["ir_report"]
        assert [item["source_name"] for item in org_health["supporting_signals"]] == [
            "credible_news",
            "community_review",
        ]

        assert strategic_direction["state"] == "verified"
        assert [item["source_name"] for item in strategic_direction["verified_facts"]] == ["ir_report"]
        assert strategic_direction["supporting_signals"] == []
        assert strategic_direction["contradictions"] == []

    def test_community_only_guardrail_keeps_org_health_unknown(self):
        reviewer = DataReviewer()
        result = reviewer.review(
            [
                make_result(
                    "culture",
                    source_name="community_review",
                    source_authority="community",
                    trust_label="verified",
                    data={
                        "org_health_evidence": [
                            {
                                "claim_key": "attrition_signal",
                                "summary": "커뮤니티에서 퇴사율이 높다는 이야기가 반복됨",
                                "status": "concern",
                                "trust_label": "verified",
                                "evidence_id": "community_review:org_health:attrition",
                            }
                        ]
                    },
                )
            ]
        )

        org_health = result.intelligence_layer["org_health"]
        assert org_health["state"] == "unknown"
        assert org_health["verified_facts"] == []
        assert [item["trust_label"] for item in org_health["supporting_signals"]] == ["supporting"]
        assert org_health["unknowns"] == ["official_or_credible_backbone_missing"]
