"""Tests for SQLite-backed Cache with TTL."""

import time

import pytest

from hirekit.core.cache import Cache


@pytest.fixture
def cache(tmp_path):
    """Cache instance using a temp directory."""
    return Cache(db_path=tmp_path / "test_cache.db", ttl_hours=1)


class TestCacheSetGet:
    def test_set_and_get_string_value(self, cache):
        cache.set("key1", "hello")
        assert cache.get("key1") == "hello"

    def test_set_and_get_dict_value(self, cache):
        cache.set("key2", {"company": "카카오", "score": 85})
        result = cache.get("key2")
        assert result["company"] == "카카오"
        assert result["score"] == 85

    def test_set_and_get_list_value(self, cache):
        cache.set("key3", [1, 2, 3])
        assert cache.get("key3") == [1, 2, 3]

    def test_missing_key_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_overwrite_existing_key(self, cache):
        cache.set("k", "old")
        cache.set("k", "new")
        assert cache.get("k") == "new"


class TestCacheTTL:
    def test_expired_entry_returns_none(self, tmp_path):
        """TTL=0 means anything older than 0 seconds is expired."""
        # Use 1/3600 hours (1 second) so we can simulate expiry
        cache = Cache(db_path=tmp_path / "ttl.db", ttl_hours=0)
        cache.set("stale", "value")
        # With ttl=0 hours (0 seconds), entry expires immediately
        assert cache.get("stale") is None

    def test_fresh_entry_not_expired(self, cache):
        cache.set("fresh", "value")
        assert cache.get("fresh") == "value"


class TestCacheDelete:
    def test_delete_removes_entry(self, cache):
        cache.set("to_delete", "value")
        cache.delete("to_delete")
        assert cache.get("to_delete") is None

    def test_delete_nonexistent_key_no_error(self, cache):
        cache.delete("never_existed")  # should not raise


class TestCacheClearExpired:
    def test_clear_expired_removes_stale_entries(self, tmp_path):
        cache = Cache(db_path=tmp_path / "expire.db", ttl_hours=0)
        cache.set("a", 1)
        cache.set("b", 2)
        removed = cache.clear_expired()
        assert removed == 2

    def test_clear_expired_keeps_fresh_entries(self, cache):
        cache.set("fresh1", 1)
        cache.set("fresh2", 2)
        removed = cache.clear_expired()
        assert removed == 0
        assert cache.get("fresh1") == 1

    def test_clear_expired_returns_count(self, tmp_path):
        cache = Cache(db_path=tmp_path / "count.db", ttl_hours=0)
        cache.set("x", 1)
        count = cache.clear_expired()
        assert isinstance(count, int)
        assert count >= 1


class TestCacheUnicode:
    def test_korean_key_and_value(self, cache):
        cache.set("회사:카카오", {"이름": "카카오", "점수": 95})
        result = cache.get("회사:카카오")
        assert result["이름"] == "카카오"

    def test_nested_unicode_structure(self, cache):
        # JSON round-trips turn int dict keys to strings — use string keys
        data = {"sections": {"1": {"ceo": "홍길동", "news": ["뉴스1", "뉴스2"]}}}
        cache.set("nested", data)
        assert cache.get("nested")["sections"]["1"]["ceo"] == "홍길동"
