"""Data filtering utilities for HireKit sources."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any

logger = logging.getLogger(__name__)


def filter_recent(
    items: list[dict[str, Any]],
    months: int = 6,
    date_keys: tuple[str, ...] = ("pub_date", "published", "date", "published_at"),
) -> list[dict[str, Any]]:
    """Return only items published within the last *months* months.

    Items that have no parseable date are kept (benefit of the doubt).

    Args:
        items: List of article/item dicts.
        months: Cutoff in months from now (default 6).
        date_keys: Ordered tuple of dict keys to probe for a date string.

    Returns:
        Filtered list preserving original order.
    """
    cutoff = datetime.now(UTC) - timedelta(days=30 * months)
    result: list[dict[str, Any]] = []

    for item in items:
        date_str = _find_date(item, date_keys)
        if date_str is None:
            # No date field found — keep the item
            result.append(item)
            continue

        parsed = _parse_date(date_str)
        if parsed is None:
            # Unparseable — keep the item
            result.append(item)
            continue

        if parsed >= cutoff:
            result.append(item)
        else:
            logger.debug("Filtered out old item (pub_date=%s): %s", date_str, item.get("title", ""))

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_date(item: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    """Return the first non-empty date string found under any of *keys*."""
    for key in keys:
        val = item.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string from common formats used in RSS/news APIs.

    Supports:
    - RFC 2822 (RSS pubDate): "Mon, 01 Jan 2024 00:00:00 GMT"
    - ISO 8601: "2024-01-01" or "2024-01-01T12:00:00Z"
    """
    # Try RFC 2822 first (Google News RSS format)
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except Exception:
        pass

    # Try ISO 8601 variants
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            continue

    return None
