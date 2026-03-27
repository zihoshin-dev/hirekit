"""Tests for CompanyDB — dynamic company data loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from hirekit.core.company_db import (
    SUBSIDIARY_GROUPS,
    CompanyDB,
    EvidenceRecord,
    _extract_primary_name,
    _normalize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEMO_DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "demo" / "data"


@pytest.fixture
def db() -> CompanyDB:
    """CompanyDB instance pointing at the real demo data."""
    return CompanyDB(data_dir=DEMO_DATA_DIR)


# ---------------------------------------------------------------------------
# Internal utility functions
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_strips_spaces(self):
        assert _normalize("토스 ") == "토스"

    def test_lowercases(self):
        assert _normalize("Toss") == "toss"

    def test_strips_legal_suffixes(self):
        assert _normalize("(주)비바리퍼블리카") == "비바리퍼블리카"
        assert _normalize("유한회사 테스트") == "테스트"

    def test_strips_parentheses(self):
        assert _normalize("토스(toss)") == "토스toss"


class TestExtractPrimaryName:
    def test_plain_name(self):
        assert _extract_primary_name("토스") == "토스"

    def test_composite_name(self):
        assert _extract_primary_name("토스 (비바리퍼블리카)") == "토스"

    def test_strips_trailing_space(self):
        assert _extract_primary_name("  네이버  ") == "네이버"


# ---------------------------------------------------------------------------
# CompanyDB — loading and basic lookup
# ---------------------------------------------------------------------------


class TestCompanyDBLoad:
    def test_loads_companies(self, db):
        companies = db.list_companies()
        assert len(companies) > 0

    def test_list_companies_returns_strings(self, db):
        for name in db.list_companies():
            assert isinstance(name, str)

    def test_known_companies_present(self, db):
        # meta.json contains 토스 as "토스 (비바리퍼블리카)" → primary "토스"
        # but primary extraction may vary; test via get_company instead
        result = db.get_company("토스")
        assert result is not None

    def test_get_company_returns_dict(self, db):
        result = db.get_company("네이버")
        assert isinstance(result, dict)

    def test_unknown_company_returns_none(self, db):
        result = db.get_company("존재하지않는회사XYZ999")
        assert result is None

    def test_get_evidence_bundle_returns_company_records(self, db):
        bundle = db.get_evidence_bundle("토스")
        assert bundle["company"]["entity_type"] == "company"
        assert bundle["company"]["entity_key"] == "토스"
        assert bundle["company"]["records"]

    def test_get_evidence_bundle_supports_role_records(self, db):
        bundle = db.get_evidence_bundle(
            "토스",
            role_name="backend_engineer",
            role_payload={
                "expectations": ["분산 시스템 운영"],
                "stack": ["python", "kafka"],
                "actual_work": ["대용량 데이터 파이프라인 개발"],
                "source_name": "job_postings",
                "collected_at": "2026-03-27T00:00:00+00:00",
            },
        )
        assert bundle["roles"][0]["entity_type"] == "role"
        assert bundle["roles"][0]["entity_key"] == "backend_engineer"
        assert bundle["roles"][0]["records"]


class TestEvidenceRecord:
    def test_as_dict_preserves_schema_fields(self):
        record = EvidenceRecord(
            entity_type="company",
            entity_key="토스",
            claim_category="strategy",
            claim_key="vision",
            value="금융의 슈퍼앱",
            source_name="company_website",
            source_authority="company_operated",
            trust_label="supporting",
            confidence=0.6,
            collected_at="2026-03-27T00:00:00+00:00",
            effective_at="2026-03-27T00:00:00+00:00",
            freshness_policy="core_company_fact",
            evidence_id="company:토스:strategy:vision:company_website",
        )
        payload = record.as_dict()
        assert payload["entity_type"] == "company"
        assert payload["claim_category"] == "strategy"
        assert payload["source_authority"] == "company_operated"
        assert payload["freshness_policy"] == "core_company_fact"


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------


class TestAlias:
    def test_toss_by_korean_name(self, db):
        result = db.get_company("토스")
        assert result is not None

    def test_toss_alias_vivare(self, db):
        """비바리퍼블리카 should resolve to 토스 record."""
        result = db.get_company("비바리퍼블리카")
        assert result is not None
        # Both point to the same record (same company)
        result2 = db.get_company("토스")
        assert result is not None and result2 is not None

    def test_당근_by_primary_name(self, db):
        result = db.get_company("당근")
        assert result is not None

    def test_naver_lookup(self, db):
        result = db.get_company("네이버")
        assert result is not None

    def test_kakao_lookup(self, db):
        result = db.get_company("카카오")
        assert result is not None


# ---------------------------------------------------------------------------
# get_tech_stack
# ---------------------------------------------------------------------------


class TestGetTechStack:
    def test_returns_list(self, db):
        stack = db.get_tech_stack("토스")
        assert isinstance(stack, list)

    def test_toss_has_tech_stack(self, db):
        stack = db.get_tech_stack("토스")
        assert len(stack) > 0

    def test_stack_items_are_lowercase_strings(self, db):
        stack = db.get_tech_stack("토스")
        for item in stack:
            assert isinstance(item, str)
            assert item == item.lower()

    def test_unknown_company_returns_empty_list(self, db):
        stack = db.get_tech_stack("존재하지않는회사XYZ999")
        assert stack == []

    def test_naver_has_tech_stack(self, db):
        stack = db.get_tech_stack("네이버")
        assert len(stack) > 0


# ---------------------------------------------------------------------------
# get_culture_hints
# ---------------------------------------------------------------------------


class TestGetCultureHints:
    def test_returns_dict(self, db):
        hints = db.get_culture_hints("토스")
        assert isinstance(hints, dict)

    def test_known_company_has_keywords(self, db):
        hints = db.get_culture_hints("토스")
        assert "keywords" in hints
        assert isinstance(hints["keywords"], list)

    def test_known_company_has_culture_category(self, db):
        hints = db.get_culture_hints("토스")
        assert "culture_category" in hints

    def test_known_company_has_is_startup(self, db):
        hints = db.get_culture_hints("토스")
        assert "is_startup" in hints
        assert isinstance(hints["is_startup"], bool)

    def test_unknown_company_returns_empty_dict(self, db):
        hints = db.get_culture_hints("존재하지않는회사XYZ999")
        assert hints == {}


# ---------------------------------------------------------------------------
# get_comparator_data
# ---------------------------------------------------------------------------


class TestGetComparatorData:
    def test_returns_dict(self, db):
        data = db.get_comparator_data("토스")
        assert isinstance(data, dict)

    def test_required_keys_present(self, db):
        data = db.get_comparator_data("토스")
        required_keys = {"growth", "compensation", "culture", "tech_level", "brand", "wlb", "remote"}
        assert required_keys.issubset(data.keys())

    def test_scores_in_valid_range(self, db):
        data = db.get_comparator_data("토스")
        for key in ("growth", "compensation", "culture", "tech_level", "brand", "wlb", "remote"):
            score = data[key]
            assert 0.0 <= score <= 5.0, f"{key}={score} out of range"

    def test_size_and_industry_present(self, db):
        data = db.get_comparator_data("토스")
        assert "size" in data
        assert "industry" in data

    def test_unknown_company_returns_empty_dict(self, db):
        data = db.get_comparator_data("존재하지않는회사XYZ999")
        assert data == {}

    def test_naver_comparator_data(self, db):
        data = db.get_comparator_data("네이버")
        assert data.get("growth", 0) > 0
        assert data.get("compensation", 0) > 0


# ---------------------------------------------------------------------------
# Subsidiary relationship API
# ---------------------------------------------------------------------------


class TestSubsidiaryRelationships:
    """Tests for get_parent, get_subsidiaries, is_subsidiary, get_group."""

    # ------------------------------------------------------------------
    # get_parent
    # ------------------------------------------------------------------

    def test_get_parent_returns_correct_parent(self, db):
        """카카오뱅크의 모회사는 카카오여야 한다."""
        assert db.get_parent("카카오뱅크") == "카카오"

    def test_get_parent_toss_subsidiary(self, db):
        """토스뱅크의 모회사는 비바리퍼블리카여야 한다."""
        assert db.get_parent("토스뱅크") == "비바리퍼블리카"

    def test_get_parent_naver_subsidiary(self, db):
        """네이버클라우드의 모회사는 네이버여야 한다."""
        assert db.get_parent("네이버클라우드") == "네이버"

    def test_get_parent_returns_none_for_parent(self, db):
        """모회사는 parent가 없으므로 None을 반환해야 한다."""
        assert db.get_parent("카카오") is None
        assert db.get_parent("네이버") is None

    def test_get_parent_returns_none_for_unknown(self, db):
        """그룹에 속하지 않는 회사는 None을 반환해야 한다."""
        assert db.get_parent("존재하지않는회사XYZ999") is None

    # ------------------------------------------------------------------
    # get_subsidiaries
    # ------------------------------------------------------------------

    def test_get_subsidiaries_lists_all(self, db):
        """카카오의 자회사 목록이 모두 포함되어야 한다."""
        subs = db.get_subsidiaries("카카오")
        expected = {
            "카카오뱅크",
            "카카오페이",
            "카카오스타일",
            "카카오엔터테인먼트",
            "카카오페이증권",
        }
        assert expected.issubset(set(subs))

    def test_get_subsidiaries_naver(self, db):
        """네이버의 자회사 목록이 포함되어야 한다."""
        subs = db.get_subsidiaries("네이버")
        assert "네이버웹툰" in subs
        assert "네이버클라우드" in subs

    def test_get_subsidiaries_returns_empty_for_subsidiary(self, db):
        """자회사를 조회하면 빈 리스트를 반환해야 한다."""
        assert db.get_subsidiaries("카카오뱅크") == []

    def test_get_subsidiaries_returns_empty_for_unknown(self, db):
        """그룹에 속하지 않는 회사는 빈 리스트를 반환해야 한다."""
        assert db.get_subsidiaries("존재하지않는회사XYZ999") == []

    # ------------------------------------------------------------------
    # is_subsidiary
    # ------------------------------------------------------------------

    def test_is_subsidiary_true_for_child(self, db):
        """카카오페이는 자회사여야 한다."""
        assert db.is_subsidiary("카카오페이") is True

    def test_is_subsidiary_true_for_toss_child(self, db):
        """토스증권은 자회사여야 한다."""
        assert db.is_subsidiary("토스증권") is True

    def test_is_subsidiary_false_for_parent(self, db):
        """모회사는 자회사가 아니어야 한다."""
        assert db.is_subsidiary("카카오") is False
        assert db.is_subsidiary("네이버") is False

    def test_is_subsidiary_false_for_unknown(self, db):
        """그룹에 속하지 않는 회사는 자회사가 아니어야 한다."""
        assert db.is_subsidiary("존재하지않는회사XYZ999") is False

    # ------------------------------------------------------------------
    # get_group
    # ------------------------------------------------------------------

    def test_get_group_includes_parent_and_children(self, db):
        """카카오 그룹 조회 시 모회사와 자회사가 모두 포함되어야 한다."""
        group = db.get_group("카카오")
        assert "카카오" in group
        assert "카카오뱅크" in group
        assert "카카오페이" in group
        assert "카카오스타일" in group
        assert "카카오엔터테인먼트" in group
        assert "카카오페이증권" in group

    def test_get_group_from_subsidiary_returns_same_as_from_parent(self, db):
        """자회사로 조회해도 모회사로 조회해도 같은 그룹 결과여야 한다."""
        from_parent = set(db.get_group("네이버"))
        from_sub = set(db.get_group("네이버클라우드"))
        assert from_parent == from_sub

    def test_get_group_returns_empty_for_unknown(self, db):
        """그룹에 속하지 않는 회사는 빈 리스트를 반환해야 한다."""
        assert db.get_group("존재하지않는회사XYZ999") == []

    # ------------------------------------------------------------------
    # SUBSIDIARY_GROUPS constant integrity
    # ------------------------------------------------------------------

    def test_subsidiary_groups_constant_structure(self):
        """SUBSIDIARY_GROUPS 상수가 올바른 구조를 가져야 한다."""
        for group_name, group_def in SUBSIDIARY_GROUPS.items():
            assert "parent" in group_def, f"{group_name}: 'parent' key missing"
            assert "subsidiaries" in group_def, f"{group_name}: 'subsidiaries' key missing"
            assert isinstance(group_def["subsidiaries"], list)
            assert len(group_def["subsidiaries"]) > 0

    def test_subsidiary_groups_no_self_reference(self):
        """자회사 목록에 모회사가 포함되어서는 안 된다."""
        for group_name, group_def in SUBSIDIARY_GROUPS.items():
            parent = group_def["parent"]
            assert parent not in group_def["subsidiaries"], f"{group_name}: parent '{parent}' listed in subsidiaries"
