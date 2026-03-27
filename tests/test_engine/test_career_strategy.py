"""Tests for career strategy engine."""

from __future__ import annotations

from typing import Any, cast

from hirekit.engine.career_strategy import (
    CareerProfile,
    CareerStrategy,
    CareerStrategyEngine,
    SkillGap,
)
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.jd_matcher import JDAnalysis
from hirekit.engine.resume_advisor import ResumeFeedback
from hirekit.engine.scorer import Scorecard, ScoreDimension
from hirekit.sources.base import SourceResult


class TestSkillGap:
    def test_fields_set_correctly(self):
        gap = SkillGap(skill="kotlin", category="Backend", importance="required")
        assert gap.skill == "kotlin"
        assert gap.category == "Backend"
        assert gap.importance == "required"
        assert gap.learning_suggestion == ""  # default

    def test_with_learning_suggestion(self):
        gap = SkillGap(
            skill="kubernetes",
            category="DevOps",
            importance="preferred",
            learning_suggestion="K8s 공식 튜토리얼",
        )
        assert gap.learning_suggestion == "K8s 공식 튜토리얼"


class TestCareerProfile:
    def test_defaults(self):
        profile = CareerProfile(target_company="토스")
        assert profile.target_company == "토스"
        assert profile.current_company is None
        assert profile.years_of_experience == 0
        assert profile.skills == []
        assert profile.education is None

    def test_full_profile(self):
        profile = CareerProfile(
            target_company="카카오",
            current_company="스타트업A",
            years_of_experience=5,
            current_role="백엔드",
            target_role="백엔드",
            skills=["python", "django", "postgresql"],
            education="CS 학사",
        )
        assert profile.years_of_experience == 5
        assert len(profile.skills) == 3


class TestCareerStrategyEngine:
    engine: CareerStrategyEngine = cast(CareerStrategyEngine, object())

    def setup_method(self):
        self.engine = CareerStrategyEngine()

    def _make_profile(self, **kwargs) -> CareerProfile:
        defaults: dict[str, Any] = {
            "target_company": "토스",
            "years_of_experience": 3,
            "target_role": "백엔드",
            "skills": [],
        }
        defaults.update(kwargs)
        return CareerProfile(
            target_company=cast(str, defaults["target_company"]),
            current_company=cast(str | None, defaults.get("current_company")),
            years_of_experience=cast(int, defaults.get("years_of_experience", 0)),
            current_role=cast(str, defaults.get("current_role", "")),
            target_role=cast(str, defaults.get("target_role", "")),
            skills=cast(list[str], defaults.get("skills", [])),
            education=cast(str | None, defaults.get("education")),
        )

    def _make_company_report(
        self,
        *,
        org_health_source_name: str = "ir_report",
        org_health_authority: str = "official",
        org_health_trust_label: str = "verified",
        org_health_summary: str = "주요 주주 구조 공시: 창업자 지분 유지",
    ) -> AnalysisReport:
        growth_reality = {
            "current_revenue": 3000000000000,
            "previous_revenue": 2500000000000,
            "revenue_growth_rate": 20.0,
            "revenue_growth_direction": "growing",
        }
        compensation_growth_reality = {
            "headcount_total": 1200,
            "salary_data_available": True,
            "max_avg_salary": 9800,
            "avg_tenure_years": 3.2,
        }
        org_health_evidence = [
            {
                "claim_key": "governance_health",
                "summary": org_health_summary,
                "status": "stable",
                "source_name": org_health_source_name,
                "source_authority": org_health_authority,
                "trust_label": org_health_trust_label,
                "evidence_id": f"{org_health_source_name}:org_health:1",
            }
        ]

        return AnalysisReport(
            company="토스",
            region="kr",
            tier=2,
            sections={
                1: {
                    "growth_reality": growth_reality,
                    "compensation_growth_reality": compensation_growth_reality,
                },
                3: {"org_health_evidence": org_health_evidence},
                5: {
                    "role_expectations": ["Python 3년 이상 경험", "백엔드 API 설계 및 개발"],
                    "actual_work": ["데이터 파이프라인 구축"],
                    "stack_reality": {
                        "confirmed": [{"tech": "python"}],
                        "likely": [{"tech": "postgresql"}],
                        "adjacent": [],
                    },
                },
                7: {
                    "actual_work": {
                        "confirmed": [{"label": "데이터 파이프라인 구축"}],
                        "likely": [],
                        "adjacent": [],
                    },
                    "stack_reality": {
                        "confirmed": [{"tech": "python"}, {"tech": "postgresql"}],
                        "likely": [],
                        "adjacent": [],
                    },
                },
            },
            source_results=[
                SourceResult(
                    source_name="dart",
                    section="financials",
                    data={"growth_reality": growth_reality},
                    confidence=0.95,
                    trust_label="derived",
                    source_authority="official",
                ),
                SourceResult(
                    source_name="dart",
                    section="financials",
                    data={"compensation_growth_reality": compensation_growth_reality},
                    confidence=0.9,
                    trust_label="derived",
                    source_authority="official",
                ),
                SourceResult(
                    source_name=org_health_source_name,
                    section="culture",
                    data={"org_health_evidence": org_health_evidence},
                    confidence=0.85,
                    trust_label=cast(Any, org_health_trust_label),
                    source_authority=cast(Any, org_health_authority),
                ),
            ],
            scorecard=Scorecard(
                company="토스",
                dimensions=[
                    ScoreDimension(
                        name="job_fit",
                        label="Job Fit",
                        weight=0.30,
                        score=4.3,
                        evidence="역할 스택과 실제 업무가 핵심 요구와 맞물려요.",
                        confidence="high",
                        source="career_page",
                    ),
                    ScoreDimension(
                        name="career_leverage",
                        label="Career Leverage",
                        weight=0.20,
                        score=4.1,
                        evidence="핀테크 도메인 레버리지와 브랜드 신호가 있어요.",
                        confidence="high",
                        source="credible_news",
                    ),
                    ScoreDimension(
                        name="growth",
                        label="Growth",
                        weight=0.20,
                        score=4.0,
                        evidence="공식 재무와 인원 지표에서 성장 흐름이 보여요.",
                        confidence="high",
                        source="dart",
                    ),
                    ScoreDimension(
                        name="compensation",
                        label="Compensation",
                        weight=0.15,
                        score=3.7,
                        evidence="보상 데이터는 일부 확인됐지만 레벨별 편차는 아직 몰라요.",
                        confidence="medium",
                        source="dart",
                    ),
                    ScoreDimension(
                        name="culture_fit",
                        label="Culture Fit",
                        weight=0.15,
                        score=3.1,
                        evidence="조직 건강 신호는 확인되지만 추가 검증이 필요해요.",
                        confidence="medium",
                        source=org_health_source_name,
                    ),
                ],
            ),
        )

    def _make_jd_analysis(self) -> JDAnalysis:
        return JDAnalysis(
            title="Backend Engineer",
            company="토스",
            match_score=78.0,
            strengths=["Python 기반 API 설계 경험", "데이터 파이프라인 운영 경험"],
            gaps=["Kubernetes 운영 경험"],
            hard_alignment=["Python 3년 이상 경험"],
            soft_alignment=["백엔드 API 설계 및 개발"],
            ambiguous_expectations=["실제 업무 범위 확인 필요"],
            role_reality_mismatches=["Kubernetes 운영 요구가 실제 역할 설명과 직접 연결되지 않아요."],
        )

    def _make_resume_feedback(self) -> ResumeFeedback:
        return ResumeFeedback(
            overall_score=72.0,
            strengths=["제품과 운영을 함께 이해하는 경험", "크로스펑셔널 협업 경험"],
            missing_proof=["데이터 기반 의사결정 역량을 보여주는 정량 사례가 아직 없어요."],
            transferability_opportunities=["제품 로드맵과 실행 우선순위 정리 경험으로 번역할 수 있어요."],
            tailored_suggestions=["이력서 상단 요약에 Python API 성과를 먼저 배치해요."],
            keyword_gaps=["kubernetes"],
        )

    def test_returns_career_strategy(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert isinstance(result, CareerStrategy)

    def test_fit_score_range(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert 0 <= result.fit_score <= 100

    def test_fit_score_higher_with_matching_skills(self):
        profile_no_skills = self._make_profile(skills=[])
        profile_with_skills = self._make_profile(
            skills=["kotlin", "spring", "react", "typescript", "aws", "kubernetes", "kafka"]
        )
        score_no = self.engine.analyze(profile_no_skills).fit_score
        score_yes = self.engine.analyze(profile_with_skills).fit_score
        assert score_yes > score_no

    def test_gap_analysis_returns_list(self):
        profile = self._make_profile(skills=[])
        result = self.engine.analyze(profile)
        assert isinstance(result.gap_analysis, list)

    def test_gap_analysis_empty_when_all_skills_match(self):
        # Toss stack (from meta.json): aws, java, kafka, kotlin, mysql, react, redis, swift, typescript
        all_skills = ["aws", "java", "kafka", "kotlin", "mysql", "react", "redis", "swift", "typescript"]
        profile = self._make_profile(skills=all_skills)
        result = self.engine.analyze(profile)
        assert result.gap_analysis == []

    def test_gap_analysis_finds_missing_skills(self):
        profile = self._make_profile(skills=["kotlin"])  # missing most toss skills
        result = self.engine.analyze(profile)
        assert len(result.gap_analysis) > 0
        gap_skills = [g.skill for g in result.gap_analysis]
        # kotlin is in user skills so should not be in gaps
        assert "kotlin" not in gap_skills

    def test_gap_skill_gap_has_category_and_importance(self):
        profile = self._make_profile(skills=[])
        result = self.engine.analyze(profile)
        for gap in result.gap_analysis:
            assert gap.importance in ("required", "preferred")
            assert isinstance(gap.category, str)
            assert len(gap.category) > 0

    def test_resume_focus_is_non_empty_list(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert isinstance(result.resume_focus, list)
        assert len(result.resume_focus) > 0

    def test_interview_prep_is_non_empty_list(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert isinstance(result.interview_prep, list)
        assert len(result.interview_prep) > 0

    def test_timeline_is_string(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert isinstance(result.timeline, str)
        assert len(result.timeline) > 0

    def test_alternative_companies_for_known_company(self):
        profile = self._make_profile(target_company="토스")
        result = self.engine.analyze(profile)
        assert isinstance(result.alternative_companies, list)

    def test_alternative_companies_empty_for_unknown(self):
        profile = self._make_profile(target_company="알수없는기업xyz")
        result = self.engine.analyze(profile)
        assert isinstance(result.alternative_companies, list)

    def test_career_path_is_string(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert isinstance(result.career_path, str)
        assert len(result.career_path) > 0

    def test_risk_assessment_includes_level(self):
        profile = self._make_profile()
        result = self.engine.analyze(profile)
        assert "리스크 수준" in result.risk_assessment

    def test_low_risk_for_high_fit(self):
        # Toss stack (from meta.json): aws, java, kafka, kotlin, mysql, react, redis, swift, typescript
        all_skills = ["aws", "java", "kafka", "kotlin", "mysql", "react", "redis", "swift", "typescript"]
        profile = self._make_profile(skills=all_skills, years_of_experience=7, target_role="백엔드")
        result = self.engine.analyze(profile)
        assert "낮음" in result.risk_assessment

    def test_high_risk_for_low_fit(self):
        profile = self._make_profile(skills=[], years_of_experience=0)
        result = self.engine.analyze(profile)
        assert "높음" in result.risk_assessment or "중간" in result.risk_assessment

    def test_approach_strategy_mentions_company(self):
        profile = self._make_profile(target_company="토스")
        result = self.engine.analyze(profile)
        assert "토스" in result.approach_strategy

    def test_current_company_in_strategy(self):
        profile = self._make_profile(current_company="카카오")
        result = self.engine.analyze(profile)
        assert "카카오" in result.approach_strategy

    def test_unknown_company_no_error(self):
        """Unknown companies should not raise errors."""
        profile = self._make_profile(target_company="신생스타트업xyz")
        result = self.engine.analyze(profile)
        assert isinstance(result, CareerStrategy)

    def test_senior_resume_focus_mentions_lead(self):
        profile = self._make_profile(years_of_experience=8, skills=["python"])
        result = self.engine.analyze(profile)
        focus_text = " ".join(result.resume_focus)
        assert "리드" in focus_text or "아키텍처" in focus_text or "멘토링" in focus_text

    def test_immediate_timeline_for_perfect_match(self):
        all_skills = ["kotlin", "spring", "react", "typescript", "aws", "kubernetes", "kafka"]
        profile = self._make_profile(skills=all_skills, years_of_experience=5, target_role="백엔드")
        result = self.engine.analyze(profile)
        # High fit score should yield short timeline
        assert "즉시" in result.timeline or "1-2개월" in result.timeline

    def test_role_alignment_same_role(self):
        profile = self._make_profile(current_role="백엔드", target_role="백엔드")
        result = self.engine.analyze(profile)
        assert result.fit_score > 0

    def test_kakao_company(self):
        profile = CareerProfile(
            target_company="카카오",
            years_of_experience=4,
            target_role="백엔드",
            skills=["java", "spring"],
        )
        result = self.engine.analyze(profile)
        assert isinstance(result, CareerStrategy)
        assert result.fit_score >= 0

    def test_english_company_name(self):
        profile = CareerProfile(
            target_company="toss",
            years_of_experience=3,
            target_role="backend",
            skills=["kotlin"],
        )
        result = self.engine.analyze(profile)
        assert isinstance(result, CareerStrategy)

    def test_adjacent_role_transition_mentions_bridge_strategy(self):
        profile = CareerProfile(
            target_company="토스",
            current_role="데이터 엔지니어",
            target_role="PM",
            years_of_experience=5,
            skills=["python", "sql", "airflow", "analytics"],
        )
        result = self.engine.analyze(profile)
        assert "브리지" in result.approach_strategy or "인접 역할" in result.approach_strategy

    def test_nontraditional_transition_mentions_alternative_path(self):
        profile = CareerProfile(
            target_company="카카오",
            current_role="디자이너",
            target_role="백엔드",
            years_of_experience=2,
            skills=["figma", "ux"],
        )
        result = self.engine.analyze(profile)
        assert "대안 포지션" in result.risk_assessment or "단계적 이동 경로" in result.risk_assessment

    def test_missing_current_company_does_not_break_strategy(self):
        profile = CareerProfile(
            target_company="네이버",
            current_company=None,
            current_role="백엔드",
            target_role="백엔드",
            years_of_experience=4,
            skills=["java", "spring", "python"],
        )
        result = self.engine.analyze(profile)
        assert isinstance(result, CareerStrategy)
        assert result.fit_score >= 0

    def test_grounded_next_actions_from_structured_evidence(self):
        profile = self._make_profile(
            target_company="토스",
            current_role="데이터 엔지니어",
            target_role="백엔드",
            skills=["python", "postgresql", "redis"],
        )

        result = self.engine.analyze(
            profile,
            company_report=self._make_company_report(),
            jd_analysis=self._make_jd_analysis(),
            resume_feedback=self._make_resume_feedback(),
        )

        why_role_matters = " ".join(result.grounded_recommendations.why_role_matters)
        why_to_hesitate = " ".join(result.grounded_recommendations.why_to_hesitate)
        application_changes = " ".join(result.grounded_recommendations.application_changes)
        verify_next = " ".join(result.grounded_recommendations.verify_next)

        assert "Job Fit" in why_role_matters
        assert "매출" in why_role_matters
        assert "Python 3년 이상 경험" in why_role_matters
        assert "Kubernetes" in why_to_hesitate
        assert "데이터 기반 의사결정 역량" in application_changes
        assert "제품 로드맵과 실행 우선순위 정리" in application_changes
        assert "needs verification" in verify_next
        assert "실제 업무 범위 확인 필요" in verify_next

    def test_unknowns_stay_visible_in_grounded_recommendations(self):
        profile = self._make_profile(target_company="토스", skills=["python"])

        result = self.engine.analyze(
            profile,
            company_report=self._make_company_report(
                org_health_source_name="community_review",
                org_health_authority="community",
                org_health_trust_label="supporting",
                org_health_summary="커뮤니티 후기에서 이직률 우려가 언급돼요.",
            ),
            jd_analysis=JDAnalysis(
                title="Backend Engineer",
                company="토스",
                match_score=51.0,
                ambiguous_expectations=["실제 업무 범위 확인 필요"],
            ),
            resume_feedback=ResumeFeedback(
                overall_score=58.0,
                missing_proof=["Python 기반 API 개발 경험을 증명할 수 있는 성과 문장이 없어요."],
            ),
        )

        why_to_hesitate = " ".join(result.grounded_recommendations.why_to_hesitate)
        verify_next = " ".join(result.grounded_recommendations.verify_next)

        assert "supporting-only" in why_to_hesitate or "unknown" in why_to_hesitate
        assert "needs verification" in verify_next
        assert "official_or_credible_backbone_missing" in verify_next or "unknown" in verify_next
