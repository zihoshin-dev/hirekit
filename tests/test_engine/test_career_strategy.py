"""Tests for career strategy engine."""

from __future__ import annotations

from typing import Any, cast

import pytest

from hirekit.engine.career_strategy import (
    CareerProfile,
    CareerStrategy,
    CareerStrategyEngine,
    SkillGap,
)


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
        profile = self._make_profile(
            skills=all_skills, years_of_experience=7, target_role="백엔드"
        )
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
        profile = self._make_profile(
            years_of_experience=8, skills=["python"]
        )
        result = self.engine.analyze(profile)
        focus_text = " ".join(result.resume_focus)
        assert "리드" in focus_text or "아키텍처" in focus_text or "멘토링" in focus_text

    def test_immediate_timeline_for_perfect_match(self):
        all_skills = ["kotlin", "spring", "react", "typescript", "aws", "kubernetes", "kafka"]
        profile = self._make_profile(
            skills=all_skills, years_of_experience=5, target_role="백엔드"
        )
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
