"""Tests for advisory panel synthesis."""

from hirekit.engine.advisory_panel import compose_advisory_panel
from hirekit.engine.career_strategy import CareerStrategy, SkillGap
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.company_comparator import ComparisonResult
from hirekit.engine.hero_verdict import HeroVerdict
from hirekit.engine.scorer import Scorecard, ScoreDimension


def make_report() -> AnalysisReport:
    return AnalysisReport(
        company="카카오",
        region="kr",
        tier=1,
        sections={
            5: {"role_expectations": [{"expectations": ["백엔드 API 설계 및 개발", "Python 3년 이상 경험"]}]},
            7: {
                "actual_work": {"likely": [{"label": "데이터 파이프라인 구축"}]},
                "stack_reality": {"confirmed": [{"tech": "python"}], "likely": [{"tech": "kafka"}], "adjacent": []},
            },
            3: {"org_health_evidence": [{"summary": "리더십 변경 이후 전략 정비 중", "trust_label": "supporting"}]},
            1: {"growth_reality": {"revenue_growth_rate": 12.5, "revenue_growth_direction": "growing"}},
        },
        scorecard=Scorecard(
            company="카카오",
            dimensions=[
                ScoreDimension(
                    name="job_fit",
                    label="Job Fit",
                    weight=0.30,
                    score=4.2,
                    evidence="GitHub와 기술 블로그에서 핵심 스택 확인",
                ),
                ScoreDimension(
                    name="career_leverage",
                    label="Career Leverage",
                    weight=0.20,
                    score=4.0,
                    evidence="브랜드 인지도와 시장 파급력 확인",
                ),
                ScoreDimension(
                    name="growth",
                    label="Growth",
                    weight=0.20,
                    score=3.8,
                    evidence="매출 성장률과 사업 확장 흐름 확인",
                ),
                ScoreDimension(
                    name="compensation",
                    label="Compensation",
                    weight=0.15,
                    score=3.6,
                    evidence="평균 연봉과 직원 규모 확인",
                ),
                ScoreDimension(
                    name="culture_fit",
                    label="Culture Fit",
                    weight=0.15,
                    score=3.4,
                    evidence="리뷰 소스 다변성은 있으나 혼합 신호",
                ),
            ],
        ),
    )


def make_strategy() -> CareerStrategy:
    return CareerStrategy(
        fit_score=76.0,
        gap_analysis=[
            SkillGap(
                skill="kafka",
                category="Backend",
                importance="required",
                learning_suggestion="Kafka 실습 2주",
            )
        ],
        approach_strategy="핵심 갭만 메우고 바로 지원할 수 있어요.",
        resume_focus=["분산 시스템 경험을 강조해요."],
        interview_prep=["Kafka 트레이드오프를 설명할 수 있어야 해요."],
        timeline="1-2개월",
        alternative_companies=["네이버", "당근"],
        career_path="백엔드 성장 경로",
        risk_assessment="중간",
    )


def make_comparison() -> ComparisonResult:
    return ComparisonResult(
        companies=["카카오", "네이버", "당근"],
        dimensions={"tech_level": [4.0, 4.5, 4.3]},
        winner_by_dimension={"tech_level": "네이버"},
        overall_scores={"카카오": 73.0, "네이버": 81.0, "당근": 79.0},
        overall_recommendation="**종합 추천: 네이버**",
        comparison_table={
            "scores": {
                "카카오": {"tech_level": 4.0},
                "네이버": {"tech_level": 4.5},
                "당근": {"tech_level": 4.3},
            }
        },
    )


class TestComposeAdvisoryPanel:
    def test_returns_five_lenses(self):
        panel = compose_advisory_panel(
            report=make_report(),
            hero_verdict=HeroVerdict(
                label="Go",
                combined_score=74.0,
                confidence="medium",
                advisory_note="Advisory only.",
                reasons=["기업 분석 74/100"],
            ),
            strategy_result=make_strategy(),
            comparison_result=make_comparison(),
        )

        assert panel.company == "카카오"
        assert len(panel.lenses) == 5
        assert panel.overall_verdict in {"Go", "Hold", "Pass"}
        assert panel.next_actions

    def test_comparison_winner_adds_parallel_review_action(self):
        panel = compose_advisory_panel(
            report=make_report(),
            hero_verdict=HeroVerdict(
                label="Hold",
                combined_score=58.0,
                confidence="medium",
                advisory_note="Advisory only.",
                reasons=["기업 분석 58/100"],
            ),
            strategy_result=make_strategy(),
            comparison_result=make_comparison(),
        )

        assert any("네이버" in action for action in panel.next_actions)

    def test_markdown_includes_consensus_and_lenses(self):
        panel = compose_advisory_panel(
            report=make_report(),
            hero_verdict=HeroVerdict(
                label="Go",
                combined_score=74.0,
                confidence="high",
                advisory_note="Advisory only.",
                reasons=["기업 분석 74/100"],
            ),
            strategy_result=make_strategy(),
        )

        content = panel.to_markdown()
        assert "# Advisory Panel: 카카오" in content
        assert "## 패널 렌즈" in content
        assert "Career Coach Council" in content

    def test_warroom_panel_evidence_uses_new_categories(self):
        panel = compose_advisory_panel(
            report=make_report(),
            hero_verdict=HeroVerdict(
                label="Go",
                combined_score=74.0,
                confidence="high",
                advisory_note="Advisory only.",
                reasons=["기업 분석 74/100"],
            ),
            strategy_result=make_strategy(),
        )

        engineering = next(lens for lens in panel.lenses if lens.key == "engineering")
        risk = next(lens for lens in panel.lenses if lens.key == "risk")
        assert any("확인 스택" in item or "실제 업무 신호" in item for item in engineering.evidence)
        assert any("조직 건강" in item for item in risk.evidence)
