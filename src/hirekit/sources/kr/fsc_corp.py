"""금융위원회 기업기본정보 데이터 소스."""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import unquote

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

FSC_BASE_URL = "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2"


@SourceRegistry.register
class FSCCorpSource(BaseSource):
    """금융위원회 공공데이터 API — 중소기업 여부, 주요사업, 직원수, 감사인."""

    name = "fsc_corp"
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

        jurir_no = kwargs.get("jurir_no", "")
        if not jurir_no:
            logger.warning("fsc_corp: jurir_no(법인등록번호) required for '%s'", company)
            return []

        data = self._fetch(jurir_no, api_key)
        if not data:
            return []

        return [
            SourceResult(
                source_name=self.name,
                section="overview",
                data=data,
                url=FSC_BASE_URL,
                raw=self._format(data),
            )
        ]

    def _fetch(self, jurir_no: str, api_key: str) -> dict[str, Any]:
        try:
            resp = httpx.get(
                FSC_BASE_URL,
                params={
                    "serviceKey": unquote(api_key),
                    "crno": jurir_no,
                    "numOfRows": "1",
                    "pageNo": "1",
                    "resultType": "json",
                },
                timeout=15,
            )
            body = resp.json()
            items = (
                body.get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )
            if not items:
                return {}
            item = items[0] if isinstance(items, list) else items
            return {
                "is_sme": item.get("smenpYn", ""),
                "main_business": item.get("enpMainBizNm", ""),
                "employee_count_fsc": item.get("enpEmpeCnt", ""),
                "auditor": item.get("actnAudpnNm", ""),
            }
        except Exception as e:
            logger.warning("fsc_corp fetch failed for jurir_no=%s: %s", jurir_no, e)
            return {}

    @staticmethod
    def _format(data: dict[str, Any]) -> str:
        return (
            f"중소기업 여부: {data.get('is_sme', '')}\n"
            f"주요사업: {data.get('main_business', '')}\n"
            f"종업원수(금융위): {data.get('employee_count_fsc', '')}명\n"
            f"감사인: {data.get('auditor', '')}"
        )
