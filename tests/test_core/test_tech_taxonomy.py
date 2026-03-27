"""Tests for tech taxonomy module."""

from hirekit.core.tech_taxonomy import (
    build_stack_reality,
    classify_experience,
    extract_work_signals,
    get_category,
    get_similar_group,
    normalize_tech,
    parse_experience_requirement,
    techs_are_similar,
)


class TestNormalizeTech:
    def test_canonical_passthrough(self):
        assert normalize_tech("python") == "python"

    def test_alias_resolves_to_canonical(self):
        assert normalize_tech("react.js") == "react"
        assert normalize_tech("ReactJS") == "react"
        assert normalize_tech("golang") == "go"
        assert normalize_tech("postgres") == "postgresql"

    def test_unknown_tech_passthrough(self):
        assert normalize_tech("some-obscure-tool") == "some-obscure-tool"

    def test_case_insensitive(self):
        assert normalize_tech("PYTHON") == "python"
        assert normalize_tech("TypeScript") == "typescript"


class TestGetCategory:
    def test_frontend(self):
        assert get_category("react") == "Frontend"
        assert get_category("vue") == "Frontend"
        assert get_category("typescript") == "Frontend"

    def test_backend(self):
        assert get_category("django") == "Backend"
        assert get_category("spring") == "Backend"

    def test_devops(self):
        assert get_category("docker") == "DevOps"
        assert get_category("kubernetes") == "DevOps"

    def test_database(self):
        assert get_category("postgresql") == "Database"
        assert get_category("mongodb") == "Database"

    def test_unknown_returns_none(self):
        assert get_category("nonexistent-framework") is None

    def test_alias_resolves_category(self):
        # "react.js" alias → "react" → "Frontend"
        assert get_category("react.js") == "Frontend"


class TestStackReality:
    def test_confirmed_stack_overlap_normalizes_with_boundaries(self):
        result = build_stack_reality(
            [
                {
                    "tech": "Python",
                    "source_name": "github",
                    "source_authority": "company_operated",
                    "confidence": 0.82,
                    "evidence": "Primary repo language: Python",
                    "signal_type": "repo_language",
                },
                {
                    "tech": "python 3",
                    "source_name": "tech_blog",
                    "source_authority": "company_operated",
                    "confidence": 0.76,
                    "evidence": "Python 3 비동기 서버 최적화",
                    "signal_type": "post_title",
                },
                {
                    "tech": "Kafka",
                    "source_name": "github",
                    "source_authority": "company_operated",
                    "confidence": 0.68,
                    "evidence": "Kafka event processing pipeline",
                    "signal_type": "repo_topic",
                },
                {
                    "tech": "GitHub Actions",
                    "source_name": "tech_blog",
                    "source_authority": "company_operated",
                    "confidence": 0.58,
                    "evidence": "GitHub Actions CI/CD 개선기",
                    "signal_type": "tooling",
                },
            ]
        )

        assert [item["tech"] for item in result["confirmed"]] == ["python"]
        assert result["confirmed"][0]["trust_label"] == "verified"
        assert result["confirmed"][0]["source_count"] == 2
        assert [item["tech"] for item in result["likely"]] == ["kafka"]
        assert [item["tech"] for item in result["adjacent"]] == ["github actions"]


class TestActualWorkSignals:
    def test_extract_work_signals_keeps_operational_evidence_grounded(self):
        result = extract_work_signals(
            [
                "Kafka 기반 실시간 데이터 파이프라인 운영 경험 공유",
                "Kubernetes 플랫폼 운영 자동화와 배포 안정화",
            ],
            source_name="tech_blog",
            source_authority="company_operated",
        )

        assert [item["pattern"] for item in result] == ["data_platform", "platform_infrastructure"]
        assert all(item["trust_label"] == "supporting" for item in result)
        assert all(item["source_name"] == "tech_blog" for item in result)


class TestTechsSimilar:
    def test_same_tech(self):
        assert techs_are_similar("python", "python") is True

    def test_alias_similar(self):
        assert techs_are_similar("react.js", "react") is True
        assert techs_are_similar("golang", "go") is True

    def test_different_techs_not_similar(self):
        assert techs_are_similar("python", "java") is False
        assert techs_are_similar("react", "django") is False


class TestGetSimilarGroup:
    def test_react_group(self):
        group = get_similar_group("react")
        assert "react" in group
        assert "react.js" in group

    def test_unknown_returns_self(self):
        group = get_similar_group("some-unknown-tech")
        assert group == ["some-unknown-tech"]


class TestClassifyExperience:
    def test_junior(self):
        level = classify_experience(1)
        assert level.name == "junior"

    def test_mid(self):
        level = classify_experience(4)
        assert level.name == "mid"

    def test_senior(self):
        level = classify_experience(8)
        assert level.name == "senior"

    def test_boundary_mid(self):
        level = classify_experience(3)
        assert level.name == "mid"

    def test_boundary_senior(self):
        level = classify_experience(7)
        assert level.name == "senior"


class TestParseExperienceRequirement:
    def test_min_korean(self):
        min_y, max_y = parse_experience_requirement("3년 이상")
        assert min_y == 3
        assert max_y is None

    def test_range_korean(self):
        min_y, max_y = parse_experience_requirement("3~5년")
        assert min_y == 3
        assert max_y == 5

    def test_range_dash(self):
        min_y, max_y = parse_experience_requirement("3-5년")
        assert min_y == 3
        assert max_y == 5

    def test_plain_years(self):
        min_y, _ = parse_experience_requirement("5년")
        assert min_y == 5

    def test_english_years(self):
        min_y, max_y = parse_experience_requirement("3+ years of experience")
        assert min_y == 3
        assert max_y is None

    def test_empty_string(self):
        min_y, _ = parse_experience_requirement("")
        assert min_y == 0
