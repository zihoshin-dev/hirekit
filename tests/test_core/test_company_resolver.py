"""Tests for company_resolver — company name disambiguation."""

from hirekit.core.company_resolver import (
    DEFAULT_ORG_MAP,
    KNOWN_CORPS,
    CompanyInfo,
    resolve_company,
)


class TestCompanyInfo:
    def test_dataclass_fields(self):
        info = CompanyInfo(name="테스트", dart_code="12345678", github_orgs=["testorg"])
        assert info.name == "테스트"
        assert info.dart_code == "12345678"
        assert info.github_orgs == ["testorg"]

    def test_defaults(self):
        info = CompanyInfo(name="테스트")
        assert info.dart_code == ""
        assert info.github_orgs == []
        assert info.region == "kr"
        assert info.aliases == []


class TestResolveCompany:
    def test_exact_canonical_name(self):
        info = resolve_company("카카오")
        assert info is not None
        assert info.name == "카카오"
        assert info.dart_code == "00258801"
        assert "kakao" in info.github_orgs

    def test_canonical_name_with_suffix(self):
        info = resolve_company("카카오페이")
        assert info is not None
        assert info.dart_code == "01445295"

    def test_alias_resolution(self):
        # "비바리퍼블리카" is an alias for 토스
        info = resolve_company("비바리퍼블리카")
        assert info is not None
        assert info.dart_code == "00783965"

    def test_english_alias(self):
        info = resolve_company("toss")
        assert info is not None
        assert info.dart_code == "00783965"

    def test_name_with_juja_stripped(self):
        info = resolve_company("(주)카카오")
        assert info is not None
        assert info.dart_code == "00258801"

    def test_name_with_spaces_stripped(self):
        info = resolve_company("카카오 페이")
        # "카카오페이" should match via substring
        assert info is not None

    def test_unknown_company_returns_none(self):
        info = resolve_company("존재하지않는회사XYZ")
        assert info is None

    def test_naver_github_orgs(self):
        info = resolve_company("네이버")
        assert info is not None
        assert "naver" in info.github_orgs
        assert "navercorp" in info.github_orgs

    def test_당근_and_당근마켓_same_dart_code(self):
        info1 = resolve_company("당근")
        info2 = resolve_company("당근마켓")
        assert info1 is not None
        assert info2 is not None
        assert info1.dart_code == info2.dart_code

    def test_case_insensitive_english(self):
        info = resolve_company("KAKAO")
        assert info is not None
        assert info.dart_code == "00258801"

    def test_라인_and_라인플러스_same_dart_code(self):
        info1 = resolve_company("라인")
        info2 = resolve_company("라인플러스")
        assert info1 is not None
        assert info2 is not None
        assert info1.dart_code == info2.dart_code


class TestBackwardsCompatExports:
    def test_known_corps_has_kakao(self):
        assert "카카오" in KNOWN_CORPS
        assert KNOWN_CORPS["카카오"] == "00258801"

    def test_known_corps_has_naver(self):
        assert "네이버" in KNOWN_CORPS
        assert KNOWN_CORPS["네이버"] == "00266961"

    def test_known_corps_all_values_are_strings(self):
        for name, code in KNOWN_CORPS.items():
            assert isinstance(code, str), f"{name} code is not str"
            assert len(code) == 8, f"{name} code '{code}' should be 8 digits"

    def test_default_org_map_has_kakao(self):
        assert "카카오" in DEFAULT_ORG_MAP
        assert "kakao" in DEFAULT_ORG_MAP["카카오"]

    def test_default_org_map_values_are_lists(self):
        for name, orgs in DEFAULT_ORG_MAP.items():
            assert isinstance(orgs, list), f"{name} orgs is not list"
            assert len(orgs) > 0, f"{name} has empty org list"

    def test_default_org_map_has_naver_with_multiple_orgs(self):
        assert "네이버" in DEFAULT_ORG_MAP
        assert len(DEFAULT_ORG_MAP["네이버"]) >= 2
