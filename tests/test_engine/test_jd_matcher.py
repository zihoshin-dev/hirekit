"""Tests for JD matcher engine."""

from pathlib import Path

from hirekit.engine.jd_matcher import JDAnalysis, JDMatcher, SkillMatch

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "hero-flow"


class TestJDAnalysis:
    def test_match_grade_s(self):
        analysis = JDAnalysis()
        analysis.match_score = 85
        assert analysis.match_grade == "S"

    def test_match_grade_d(self):
        analysis = JDAnalysis()
        analysis.match_score = 20
        assert analysis.match_grade == "D"

    def test_to_markdown_includes_title(self):
        analysis = JDAnalysis(title="Senior PM", company="TestCorp")
        analysis.match_score = 75
        md = analysis.to_markdown()
        assert "Senior PM" in md
        assert "TestCorp" in md
        assert "75" in md

    def test_skill_matches_in_markdown(self):
        analysis = JDAnalysis(title="Test")
        analysis.match_score = 50
        analysis.skill_matches = [
            SkillMatch(skill="Python", required=True, matched=True),
            SkillMatch(skill="Java", required=True, matched=False),
        ]
        md = analysis.to_markdown()
        assert "Python" in md
        assert "Java" in md


class TestJDMatcher:
    def test_extract_requirements_from_text(self):
        jd_text = """
        자격요건
        - Python 3년 이상 경험
        - SQL 사용 경험
        - 데이터 분석 경험

        우대사항
        - ML/DL 경험
        - AWS 경험

        담당업무
        - 데이터 파이프라인 구축
        - 분석 리포트 작성
        """
        matcher = JDMatcher()
        analysis = matcher.analyze(jd_source=jd_text)

        assert len(analysis.required_skills) >= 2
        assert len(analysis.preferred_skills) >= 1
        assert len(analysis.responsibilities) >= 1

    def test_match_profile(self):
        jd_text = """
        자격요건
        - Python 경험
        - SQL 경험
        - 데이터 분석
        """
        profile = {
            "skills": {
                "technical": ["Python", "SQL", "R"],
                "domain": ["Data Analysis"],
                "soft": [],
            },
            "career_assets": [],
        }
        matcher = JDMatcher()
        analysis = matcher.analyze(jd_source=jd_text, profile=profile)

        assert analysis.match_score > 0
        assert len(analysis.strengths) > 0

    def test_no_profile_still_works(self):
        matcher = JDMatcher()
        analysis = matcher.analyze(jd_source="자격요건\n- Python\n- SQL")
        assert analysis.match_score == 0  # No profile = no match
        assert len(analysis.required_skills) >= 1

    def test_experience_extraction(self):
        matcher = JDMatcher()
        analysis = matcher.analyze(jd_source="자격요건\n- 3년 이상 경력")
        assert "3년" in analysis.experience_years

    def test_high_signal_fixture_with_matching_profile_scores_positive(self):
        matcher = JDMatcher()
        jd_text = (FIXTURE_ROOT / "jd-high-signal.txt").read_text(encoding="utf-8")
        profile = {
            "skills": {
                "technical": ["Python", "PostgreSQL", "Docker", "Kubernetes", "Kafka"],
                "domain": ["Data Pipeline"],
                "soft": [],
            },
            "career_assets": [],
        }
        analysis = matcher.analyze(jd_source=jd_text, profile=profile)
        assert analysis.match_score > 0
        assert analysis.strengths

    def test_low_signal_fixture_stays_conservative(self):
        matcher = JDMatcher()
        jd_text = (FIXTURE_ROOT / "jd-low-signal.txt").read_text(encoding="utf-8")
        profile = {
            "skills": {
                "technical": ["Python", "PostgreSQL"],
                "domain": [],
                "soft": [],
            },
            "career_assets": [],
        }
        analysis = matcher.analyze(jd_source=jd_text, profile=profile)
        assert analysis.match_score < 50
        assert not analysis.required_skills

    def test_explainable_alignment_against_role_context(self):
        matcher = JDMatcher()
        jd_text = """
        자격요건
        - Python 3년 이상 경험
        - PostgreSQL, Redis 사용 경험

        담당업무
        - 데이터 파이프라인 구축
        - 백엔드 API 설계 및 개발
        """
        analysis = matcher.analyze(
            jd_source=jd_text,
            role_context={
                "expectations": ["Python 3년 이상 경험", "백엔드 API 설계 및 개발"],
                "actual_work": ["데이터 파이프라인 구축"],
                "stack": ["python", "postgresql", "redis"],
            },
        )

        assert analysis.hard_alignment
        assert "백엔드 API 설계 및 개발" in analysis.soft_alignment
        assert not analysis.role_reality_mismatches

    def test_aspirational_jd_guardrail_marks_mismatch(self):
        matcher = JDMatcher()
        jd_text = """
        자격요건
        - Kubernetes 환경 경험
        - Kafka 운영 경험

        담당업무
        - 데이터 분석 지원
        """
        analysis = matcher.analyze(
            jd_source=jd_text,
            role_context={
                "expectations": ["Python 기반 분석 업무"],
                "actual_work": ["데이터 분석 지원"],
                "stack": ["python", "postgresql"],
            },
        )

        assert analysis.role_reality_mismatches
        assert any("kubernetes" in item.lower() for item in analysis.role_reality_mismatches)
        assert analysis.ambiguous_expectations
