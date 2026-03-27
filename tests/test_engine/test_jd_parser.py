"""Tests for JD parser module."""

from hirekit.engine.jd_parser import JDParser

JD_KR_FULL = """
주요업무
- 백엔드 API 설계 및 개발
- 데이터 파이프라인 구축
- 코드 리뷰 및 기술 문서 작성

자격요건
- Python 3년 이상 경험
- Django 또는 FastAPI 경험
- PostgreSQL, Redis 사용 경험
- Docker, Kubernetes 환경 경험

우대사항
- AWS 경험
- ML 파이프라인 경험
- TypeScript 가능자

기술스택
- Python, Django, FastAPI
- PostgreSQL, Redis
- Docker, Kubernetes, AWS
"""

JD_EN_FULL = """
Responsibilities
- Design and build scalable backend services
- Collaborate with frontend engineers

Requirements
- 5+ years of Python experience
- Experience with Django or FastAPI
- Proficiency in PostgreSQL and Redis
- Docker and Kubernetes experience

Preferred
- AWS experience
- TypeScript knowledge
"""

JD_MINIMAL = """
자격요건
- Python
- SQL
"""


class TestJDParserSections:
    def test_kr_required_qualifications(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert len(jd.required_qualifications) >= 3

    def test_kr_preferred_qualifications(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert len(jd.preferred_qualifications) >= 1

    def test_kr_responsibilities(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert len(jd.responsibilities) >= 2

    def test_en_required_qualifications(self):
        parser = JDParser()
        jd = parser.parse(JD_EN_FULL)
        assert len(jd.required_qualifications) >= 2

    def test_en_preferred_qualifications(self):
        parser = JDParser()
        jd = parser.parse(JD_EN_FULL)
        assert len(jd.preferred_qualifications) >= 1

    def test_empty_text_returns_empty_jd(self):
        parser = JDParser()
        jd = parser.parse("")
        assert jd.required_qualifications == []
        assert jd.preferred_qualifications == []
        assert jd.responsibilities == []


class TestJDParserExperience:
    def test_kr_experience_extraction(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert jd.experience_min_years == 3
        assert jd.experience_years_raw != ""

    def test_en_experience_extraction(self):
        parser = JDParser()
        jd = parser.parse(JD_EN_FULL)
        assert jd.experience_min_years == 5
        assert jd.experience_max_years is None

    def test_no_experience_requirement(self):
        parser = JDParser()
        jd = parser.parse(JD_MINIMAL)
        assert jd.experience_min_years == 0


class TestJDParserTechExtraction:
    def test_kr_required_tech_extracted(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        # python, django, fastapi, postgresql, redis, docker, kubernetes should be found
        assert "python" in jd.required_tech
        assert "docker" in jd.required_tech

    def test_kr_preferred_tech_extracted(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert "aws" in jd.preferred_tech

    def test_alias_normalized(self):
        parser = JDParser()
        jd = parser.parse("자격요건\n- React.js 경험\n- PostgreSQL 사용")
        assert "react" in jd.required_tech
        assert "postgresql" in jd.required_tech

    def test_preferred_tech_not_in_required(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        # preferred techs should not duplicate required techs
        for tech in jd.preferred_tech:
            assert tech not in jd.required_tech

    def test_tech_categories_built(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert len(jd.tech_categories) > 0
        # Docker should be in DevOps category
        assert "docker" in jd.tech_categories.get("DevOps", [])


class TestJDParserMetadata:
    def test_title_and_company_passed_through(self):
        parser = JDParser()
        jd = parser.parse(JD_MINIMAL, title="Backend Engineer", company="TestCorp")
        assert jd.title == "Backend Engineer"
        assert jd.company == "TestCorp"

    def test_all_required_tech_deduplicates(self):
        parser = JDParser()
        jd = parser.parse("자격요건\n- Python\n- Python 3.10\n- SQL")
        techs = jd.all_required_tech()
        # python should appear once after normalization
        assert techs.count("python") == 1


class TestJDParserRoleExpectations:
    def test_builds_must_have_expectations(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert any("Python 3년 이상 경험" in item for item in jd.must_have_expectations)
        assert any(item.startswith("필수 기술:") for item in jd.must_have_expectations)

    def test_builds_inferred_expectations_from_responsibilities(self):
        parser = JDParser()
        jd = parser.parse(JD_KR_FULL)
        assert "백엔드 API 설계 및 개발" in jd.inferred_expectations

    def test_marks_unknown_expectations_when_scope_is_sparse(self):
        parser = JDParser()
        jd = parser.parse(JD_MINIMAL)
        assert "실제 업무 범위 확인 필요" in jd.unknown_expectations
