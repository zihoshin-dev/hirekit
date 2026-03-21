"""Tests for core.filters — date-based filtering of news items."""

from datetime import UTC, datetime, timedelta

import pytest

from hirekit.core.filters import _parse_date, filter_recent


def _days_ago(n: int) -> str:
    """Return an RFC 2822 date string n days in the past."""
    dt = datetime.now(UTC) - timedelta(days=n)
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")


def _iso_days_ago(n: int) -> str:
    """Return an ISO 8601 date string n days in the past."""
    dt = datetime.now(UTC) - timedelta(days=n)
    return dt.strftime("%Y-%m-%d")


class TestParseDateInternal:
    def test_rfc2822_format(self):
        date_str = "Mon, 01 Jan 2024 00:00:00 GMT"
        dt = _parse_date(date_str)
        assert dt is not None
        assert dt.year == 2024

    def test_iso_date_only(self):
        dt = _parse_date("2024-06-15")
        assert dt is not None
        assert dt.month == 6
        assert dt.day == 15

    def test_iso_datetime_z(self):
        dt = _parse_date("2024-03-20T12:00:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 3

    def test_unparseable_returns_none(self):
        dt = _parse_date("not a date at all")
        assert dt is None

    def test_empty_string_returns_none(self):
        dt = _parse_date("")
        assert dt is None

    def test_result_is_timezone_aware(self):
        dt = _parse_date("2024-01-01")
        assert dt is not None
        assert dt.tzinfo is not None


class TestFilterRecent:
    def test_recent_items_kept(self):
        items = [
            {"title": "new", "pub_date": _days_ago(10)},
            {"title": "also new", "pub_date": _days_ago(30)},
        ]
        result = filter_recent(items, months=6)
        assert len(result) == 2

    def test_old_items_removed(self):
        items = [
            {"title": "recent", "pub_date": _days_ago(10)},
            {"title": "old", "pub_date": _days_ago(200)},
        ]
        result = filter_recent(items, months=6)
        assert len(result) == 1
        assert result[0]["title"] == "recent"

    def test_all_old_items_removed(self):
        items = [
            {"title": "very old", "pub_date": _days_ago(400)},
            {"title": "also old", "pub_date": _days_ago(300)},
        ]
        result = filter_recent(items, months=6)
        assert result == []

    def test_items_without_date_kept(self):
        items = [
            {"title": "no date"},
            {"title": "also no date", "source": "test"},
        ]
        result = filter_recent(items, months=6)
        assert len(result) == 2

    def test_items_with_unparseable_date_kept(self):
        items = [{"title": "bad date", "pub_date": "not-a-date"}]
        result = filter_recent(items, months=6)
        assert len(result) == 1

    def test_empty_list_returns_empty(self):
        assert filter_recent([], months=6) == []

    def test_months_parameter_respected(self):
        # Item is 45 days old — inside 3 months but outside 1 month
        items = [{"title": "45 days", "pub_date": _days_ago(45)}]
        assert len(filter_recent(items, months=3)) == 1
        assert len(filter_recent(items, months=1)) == 0

    def test_iso_date_format_supported(self):
        items = [
            {"title": "recent iso", "pub_date": _iso_days_ago(10)},
            {"title": "old iso", "pub_date": _iso_days_ago(250)},
        ]
        result = filter_recent(items, months=6)
        assert len(result) == 1
        assert result[0]["title"] == "recent iso"

    def test_custom_date_keys(self):
        items = [
            {"title": "alt key", "published": _days_ago(5)},
            {"title": "old alt key", "published": _days_ago(250)},
        ]
        result = filter_recent(items, months=6, date_keys=("published",))
        assert len(result) == 1

    def test_preserves_order(self):
        items = [
            {"title": "a", "pub_date": _days_ago(1)},
            {"title": "b", "pub_date": _days_ago(5)},
            {"title": "c", "pub_date": _days_ago(10)},
        ]
        result = filter_recent(items, months=6)
        assert [r["title"] for r in result] == ["a", "b", "c"]

    def test_boundary_item_just_inside_cutoff_kept(self):
        # Item 1 day inside the 6-month window should be kept
        items = [{"title": "boundary", "pub_date": _days_ago(179)}]
        result = filter_recent(items, months=6)
        assert len(result) == 1
