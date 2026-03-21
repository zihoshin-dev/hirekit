"""Tests for hirekit.core.security — SSRF prevention and input sanitization."""

from __future__ import annotations

import pytest

from hirekit.core.security import sanitize_company_name, sanitize_region, validate_url


# ---------------------------------------------------------------------------
# validate_url — SSRF prevention
# ---------------------------------------------------------------------------

class TestValidateUrl:
    def test_public_https_url_passes(self):
        url = "https://opendart.fss.or.kr/api/company.json"
        assert validate_url(url) == url

    def test_public_http_url_passes(self):
        url = "http://example.com/data"
        assert validate_url(url) == url

    def test_localhost_blocked(self):
        with pytest.raises(ValueError, match="reserved hostname"):
            validate_url("http://localhost/admin")

    def test_loopback_ip_blocked(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("http://127.0.0.1/secret")

    def test_loopback_ip_blocked_https(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("https://127.0.0.1:8080/api")

    def test_private_10_network_blocked(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("http://10.0.0.1/internal")

    def test_private_172_network_blocked(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("http://172.16.0.1/secret")

    def test_private_192_168_blocked(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("http://192.168.1.100/admin")

    def test_ipv6_loopback_blocked(self):
        with pytest.raises(ValueError, match="private/internal"):
            validate_url("http://[::1]/admin")

    def test_file_scheme_blocked(self):
        with pytest.raises(ValueError, match="scheme"):
            validate_url("file:///etc/passwd")

    def test_empty_url_raises(self):
        with pytest.raises(ValueError):
            validate_url("")

    def test_no_hostname_raises(self):
        with pytest.raises(ValueError):
            validate_url("https://")

    def test_returns_url_unchanged(self):
        url = "https://api.github.com/orgs/kakao/repos"
        assert validate_url(url) == url


# ---------------------------------------------------------------------------
# sanitize_company_name
# ---------------------------------------------------------------------------

class TestSanitizeCompanyName:
    def test_normal_name_unchanged(self):
        assert sanitize_company_name("카카오") == "카카오"

    def test_strips_whitespace(self):
        assert sanitize_company_name("  토스  ") == "토스"

    def test_removes_forward_slash(self):
        assert sanitize_company_name("../../../etc/passwd") == "etcpasswd"

    def test_removes_backslash(self):
        assert sanitize_company_name("company\\name") == "companyname"

    def test_removes_dotdot(self):
        assert sanitize_company_name("..secret") == "secret"

    def test_empty_string_returns_empty(self):
        assert sanitize_company_name("") == ""

    def test_english_name_unchanged(self):
        assert sanitize_company_name("Kakao") == "Kakao"

    def test_name_with_spaces_preserved(self):
        assert sanitize_company_name("우아한 형제들") == "우아한 형제들"


# ---------------------------------------------------------------------------
# sanitize_region
# ---------------------------------------------------------------------------

class TestSanitizeRegion:
    def test_kr_passes(self):
        assert sanitize_region("kr") == "kr"

    def test_us_passes(self):
        assert sanitize_region("us") == "us"

    def test_global_passes(self):
        assert sanitize_region("global") == "global"

    def test_slash_in_region_raises(self):
        with pytest.raises(ValueError):
            sanitize_region("../etc")

    def test_special_chars_raise(self):
        with pytest.raises(ValueError):
            sanitize_region("kr; DROP TABLE")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            sanitize_region("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            sanitize_region("a" * 17)
