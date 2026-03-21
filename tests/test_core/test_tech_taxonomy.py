"""Tests for tech taxonomy module."""

from hirekit.core.tech_taxonomy import (
    normalize_tech,
    get_category,
    techs_are_similar,
    get_similar_group,
    classify_experience,
    parse_experience_requirement,
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
        min_y, max_y = parse_experience_requirement("5년")
        assert min_y == 5

    def test_english_years(self):
        min_y, max_y = parse_experience_requirement("3+ years of experience")
        assert min_y == 3
        assert max_y is None

    def test_empty_string(self):
        min_y, max_y = parse_experience_requirement("")
        assert min_y == 0
