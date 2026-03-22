"""병역특례 데이터 소스 — 미리 수집된 JSON에서 로드."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "docs" / "demo" / "data" / "military_service.json"


@SourceRegistry.register
class MilitaryServiceSource(BaseSource):
    """병역특례(산업기능요원/전문연구요원) 지정 현황 데이터."""

    name = "military_service"
    region = "kr"
    sections = ["overview"]
    requires_api_key = False

    def is_available(self) -> bool:
        return _DATA_PATH.exists()

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        try:
            data: dict[str, Any] = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("military_service: failed to load data: %s", exc)
            return []

        entry = data.get(company)
        if entry is None:
            return []

        available = entry.get("military_service_available", False)
        svc_type = entry.get("military_service_type") or "해당없음"
        quota = entry.get("military_service_quota")
        note = entry.get("military_service_note", "")

        raw_lines = [f"[병역특례 현황] {company}"]
        raw_lines.append(f"  병역특례 지정: {'O' if available else 'X'}")
        if available:
            raw_lines.append(f"  유형: {svc_type}")
            if quota:
                raw_lines.append(f"  배정 인원: {quota}명")
        if note:
            raw_lines.append(f"  비고: {note}")

        return [
            SourceResult(
                source_name=self.name,
                section="overview",
                data=entry,
                raw="\n".join(raw_lines),
            )
        ]
