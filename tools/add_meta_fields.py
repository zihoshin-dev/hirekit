#!/usr/bin/env python3
"""각 기업 JSON에 _meta 필드 추가 (기존 데이터 무수정)."""

import json
import os
from datetime import datetime, timezone, timedelta

COMPANIES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "companies"
)

KST = timezone(timedelta(hours=9))


def compute_staleness(mtime_ts: float) -> int:
    """파일 mtime 기준 경과 일수."""
    now = datetime.now(timezone.utc)
    mtime_dt = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
    return (now - mtime_dt).days


def build_meta(fpath: str) -> dict:
    mtime_ts = os.path.getmtime(fpath)
    collected_at = datetime.fromtimestamp(mtime_ts, tz=KST).strftime(
        "%Y-%m-%dT%H:%M:%S+09:00"
    )
    staleness_days = compute_staleness(mtime_ts)
    return {
        "collected_at": collected_at,
        "verified_at": None,
        "confidence": 0.5,
        "staleness_days": staleness_days,
        "cross_validated": False,
        "version": 1,
    }


def add_meta_fields(dry_run: bool = False) -> dict:
    companies_path = os.path.abspath(COMPANIES_DIR)
    json_files = sorted(f for f in os.listdir(companies_path) if f.endswith(".json"))

    added = 0
    skipped = 0
    errors = []

    for fname in json_files:
        fpath = os.path.join(companies_path, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)

            if "_meta" in data:
                skipped += 1
                continue

            data["_meta"] = build_meta(fpath)

            if not dry_run:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.write("\n")

            added += 1
            print(f"  + {fname}")

        except Exception as e:
            errors.append({"file": fname, "error": str(e)})
            print(f"  ERROR {fname}: {e}")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}완료: 추가 {added}개, 스킵(기존 _meta) {skipped}개, 오류 {len(errors)}개")
    return {"added": added, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    add_meta_fields(dry_run=dry_run)
