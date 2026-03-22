"""국세청 사업자 상태 데이터 소스."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import unquote

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

NTS_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"


@SourceRegistry.register
class NTSBusinessSource(BaseSource):
    """국세청 사업자등록 상태 API — 계속/휴업/폐업, 과세유형."""

    name = "nts_business"
    region = "kr"
    sections = ["overview"]
    requires_api_key = True
    api_key_env = "DATA_GO_KR_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env, "")
        if not api_key:
            return []

        bizr_no = kwargs.get("bizr_no", "")
        if not bizr_no:
            logger.warning("nts_business: bizr_no(사업자번호) required for '%s'", company)
            return []

        data = self._fetch(bizr_no, api_key)
        if not data:
            return []

        return [
            SourceResult(
                source_name=self.name,
                section="overview",
                data=data,
                url=NTS_URL,
                raw=self._format(data),
            )
        ]

    def _fetch(self, bizr_no: str, api_key: str) -> dict[str, Any]:
        # 하이픈 제거
        b_no = bizr_no.replace("-", "").strip()
        try:
            resp = httpx.post(
                NTS_URL,
                params={"serviceKey": unquote(api_key)},
                headers={
                    "Authorization": f"Infuser {unquote(api_key)}",
                    "Content-Type": "application/json",
                },
                json={"b_no": [b_no]},
                timeout=15,
            )
            body = resp.json()
            data_list = body.get("data", [])
            if not data_list:
                return {}
            item = data_list[0]
            return {
                "biz_status": item.get("b_stt", ""),
                "tax_type": item.get("tax_type", ""),
            }
        except Exception as e:
            logger.warning("nts_business fetch failed for bizr_no=%s: %s", bizr_no, e)
            return {}

    @staticmethod
    def _format(data: dict[str, Any]) -> str:
        return (
            f"사업자 상태: {data.get('biz_status', '')}\n"
            f"과세유형: {data.get('tax_type', '')}"
        )
