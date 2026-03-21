"""Disk cache with TTL using sqlite3 (zero external dependencies)."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from hirekit.core.config import DEFAULT_CONFIG_DIR


class Cache:
    """Simple key-value cache backed by SQLite."""

    def __init__(self, db_path: Path | None = None, ttl_hours: int = 168):
        self.db_path = db_path or (DEFAULT_CONFIG_DIR / "cache.db")
        self.ttl_seconds = ttl_hours * 3600
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

    def get(self, key: str) -> Any | None:
        """Get cached value. Returns None if missing or expired."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, created_at FROM cache WHERE key = ?", (key,)
            ).fetchone()

        if row is None:
            return None

        value, created_at = row
        if time.time() - created_at > self.ttl_seconds:
            self.delete(key)
            return None

        return json.loads(value)

    def set(self, key: str, value: Any) -> None:
        """Set a cache entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False), time.time()),
            )

    def delete(self, key: str) -> None:
        """Delete a cache entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        cutoff = time.time() - self.ttl_seconds
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE created_at < ?", (cutoff,))
            return cursor.rowcount
