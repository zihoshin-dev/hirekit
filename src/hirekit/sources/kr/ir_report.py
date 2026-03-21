"""IR/사업보고서 data source — collect business segments, subsidiaries, R&D, global revenue."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from hirekit.core.security import validate_url
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult
from hirekit.sources.kr.dart import DART_BASE_URL, DartSource

logger = logging.getLogger(__name__)


@SourceRegistry.register
class IRReportSource(BaseSource):
    """Collect IR/사업보고서 data from DART: segments, subsidiaries, R&D, global revenue."""

    name = "ir_report"
    region = "kr"
    sections = ["strategy", "overview"]
    requires_api_key = True
    api_key_env_var = "DART_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env_var))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env_var, "")
        if not api_key:
            return []

        # Resolve corp_code via DartSource helper (reuse existing logic)
        dart = DartSource()
        corp_code = kwargs.get("corp_code") or dart._resolve_corp_code(company, api_key)
        if not corp_code:
            logger.warning("IRReportSource: could not find DART corp_code for '%s'", company)
            return []

        results: list[SourceResult] = []

        # 1. Major shareholders (majorstock.json)
        shareholders = self._get_major_shareholders(corp_code, api_key)
        if shareholders:
            results.append(SourceResult(
                source_name=self.name,
                section="overview",
                data={"major_shareholders": shareholders},
                url=f"https://dart.fss.or.kr/corp/summary.ax?cmpCd={corp_code}",
                raw=self._format_shareholders(shareholders),
            ))

        # 2. Business report details: subsidiaries, R&D, global revenue
        report_data = self._get_business_report_data(corp_code, api_key)
        if report_data:
            results.append(SourceResult(
                source_name=self.name,
                section="strategy",
                data=report_data,
                url=f"https://dart.fss.or.kr/corp/summary.ax?cmpCd={corp_code}",
                raw=self._format_report_data(company, report_data),
            ))

        return results

    def _get_major_shareholders(self, corp_code: str, api_key: str) -> list[dict[str, Any]]:
        """Get major shareholders from DART majorstock.json."""
        import datetime
        year = str(datetime.date.today().year - 1)
        try:
            url = validate_url(f"{DART_BASE_URL}/majorstock.json")
            resp = httpx.get(
                url,
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bsns_year": year,
                    "reprt_code": "11011",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("list"):
                return [
                    {
                        "name": item.get("nm", ""),
                        "relation": item.get("relate", ""),
                        "stock_count": item.get("stock_co", ""),
                        "ownership_ratio": item.get("hold_ratio", ""),
                    }
                    for item in data["list"]
                ]
        except Exception as e:
            logger.warning("IRReportSource majorstock failed: %s", e)
        return []

    def _get_business_report_data(self, corp_code: str, api_key: str) -> dict[str, Any]:
        """Search DART for 사업보고서 and extract structured data."""
        import datetime
        year = str(datetime.date.today().year - 1)
        try:
            # Search for 사업보고서 filing
            url = validate_url(f"{DART_BASE_URL}/list.json")
            resp = httpx.get(
                url,
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bgn_de": f"{year}0101",
                    "end_de": f"{year}1231",
                    "pblntf_ty": "A",  # 정기공시
                    "pblntf_detail_ty": "A001",  # 사업보고서
                    "page_count": "5",
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("list"):
                filing = data["list"][0]
                rcept_no = filing.get("rcept_no", "")
                report_nm = filing.get("report_nm", "")
                return {
                    "annual_report_name": report_nm,
                    "rcept_no": rcept_no,
                    "report_year": year,
                    "filing_date": filing.get("rcept_dt", ""),
                    "report_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else "",
                }
        except Exception as e:
            logger.warning("IRReportSource business report search failed: %s", e)
        return {}

    # --- Formatting helpers ---

    @staticmethod
    def _format_shareholders(shareholders: list[dict[str, Any]]) -> str:
        lines = ["[주요 주주 현황]"]
        for s in shareholders:
            lines.append(
                f"  {s.get('name', '')} ({s.get('relation', '')}): "
                f"{s.get('ownership_ratio', '')}% "
                f"({s.get('stock_count', '')}주)"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_report_data(company: str, data: dict[str, Any]) -> str:
        lines = [f"[{company} 사업보고서]"]
        if data.get("annual_report_name"):
            lines.append(f"공시명: {data['annual_report_name']}")
        if data.get("filing_date"):
            lines.append(f"공시일: {data['filing_date']}")
        if data.get("report_url"):
            lines.append(f"URL: {data['report_url']}")
        return "\n".join(lines)
