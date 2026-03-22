"""채용공고 데이터 소스 — 미리 수집된 JSON에서 로드."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "demo" / "data" / "job_postings.json"


@SourceRegistry.register
class JobPostingsSource(BaseSource):
    """채용공고 현황 데이터 (사람인 기반 미리 수집)."""

    name = "job_postings"
    region = "kr"
    sections = ["role"]
    requires_api_key = False

    def is_available(self) -> bool:
        return _DATA_PATH.exists()

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        try:
            data: dict[str, Any] = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("job_postings: failed to load data: %s", exc)
            return []

        entry = data.get(company)
        if entry is None:
            return []

        active = entry.get("active_job_postings", 0)
        positions: list[str] = entry.get("hiring_positions", [])
        source = entry.get("source", "")

        raw_lines = [f"[채용공고 현황] {company}"]
        raw_lines.append(f"  활성 공고 수: {active}건")
        if positions:
            raw_lines.append("  주요 포지션:")
            for pos in positions[:5]:
                raw_lines.append(f"    - {pos}")
        if source:
            raw_lines.append(f"  출처: {source}")

        return [
            SourceResult(
                source_name=self.name,
                section="role",
                data=entry,
                raw="\n".join(raw_lines),
            )
        ]
