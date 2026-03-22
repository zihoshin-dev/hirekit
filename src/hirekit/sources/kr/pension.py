"""국민연금 가입자 수 데이터 소스 — 미리 수집된 JSON에서 로드."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "demo" / "data" / "pension_data.json"


@SourceRegistry.register
class PensionSource(BaseSource):
    """국민연금 가입자 수 데이터 (직원 수 추정 지표)."""

    name = "pension"
    region = "kr"
    sections = ["overview"]
    requires_api_key = False

    def is_available(self) -> bool:
        return _DATA_PATH.exists()

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        try:
            data: dict[str, Any] = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("pension: failed to load data: %s", exc)
            return []

        entry = data.get(company)
        if entry is None:
            return []

        members = entry.get("pension_members")
        date = entry.get("pension_date", "")
        source = entry.get("pension_source", "")

        raw_lines = [f"[국민연금 가입자 수] {company}"]
        if members:
            raw_lines.append(f"  가입자 수: {members:,}명")
        if date:
            raw_lines.append(f"  기준일: {date}")
        if source:
            raw_lines.append(f"  출처: {source}")

        return [
            SourceResult(
                source_name=self.name,
                section="overview",
                data=entry,
                raw="\n".join(raw_lines),
            )
        ]
