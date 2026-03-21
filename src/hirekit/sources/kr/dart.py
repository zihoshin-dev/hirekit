"""DART (전자공시시스템) data source — financial statements, employee data."""

from __future__ import annotations

import os
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

DART_BASE_URL = "https://opendart.fss.or.kr/api"


@SourceRegistry.register
class DartSource(BaseSource):
    """Collect company data from Korea's DART electronic disclosure system."""

    name = "dart"
    region = "kr"
    sections = ["overview", "financials"]
    requires_api_key = True
    api_key_env_var = "DART_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env_var))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env_var, "")
        if not api_key:
            return []

        results: list[SourceResult] = []

        # 1. Search for company code
        corp_code = self._search_company(company, api_key)
        if not corp_code:
            return []

        # 2. Get company overview
        overview = self._get_overview(corp_code, api_key)
        if overview:
            results.append(SourceResult(
                source_name=self.name,
                section="overview",
                data=overview,
                url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={overview.get('rcept_no', '')}",
                raw=str(overview),
            ))

        # 3. Get employee info (headcount, avg salary, avg tenure)
        emp_data = self._get_employee_info(corp_code, api_key)
        if emp_data:
            results.append(SourceResult(
                source_name=self.name,
                section="overview",
                data={"employees": emp_data},
                raw=str(emp_data),
            ))

        # 4. Get financial highlights
        financials = self._get_financials(corp_code, api_key)
        if financials:
            results.append(SourceResult(
                source_name=self.name,
                section="financials",
                data={"financials": financials},
                raw=str(financials),
            ))

        return results

    def _search_company(self, company: str, api_key: str) -> str | None:
        """Search for corp_code by company name."""
        try:
            resp = httpx.get(
                f"{DART_BASE_URL}/company.json",
                params={"crtfc_key": api_key, "corp_name": company},
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("corp_code"):
                return str(data["corp_code"])
        except Exception:
            pass

        # Fallback: search via corpCode.xml (full list)
        # For MVP, return None if direct search fails
        return None

    def _get_overview(self, corp_code: str, api_key: str) -> dict[str, Any]:
        """Get company overview (name, CEO, address, industry, etc.)."""
        try:
            resp = httpx.get(
                f"{DART_BASE_URL}/company.json",
                params={"crtfc_key": api_key, "corp_code": corp_code},
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000":
                return {
                    "company_name": data.get("corp_name", ""),
                    "ceo": data.get("ceo_nm", ""),
                    "address": data.get("adres", ""),
                    "industry": data.get("induty_code", ""),
                    "established": data.get("est_dt", ""),
                    "homepage": data.get("hm_url", ""),
                    "stock_code": data.get("stock_code", ""),
                    "rcept_no": data.get("rcept_no", ""),
                }
        except Exception:
            pass
        return {}

    def _get_employee_info(self, corp_code: str, api_key: str) -> list[dict[str, Any]]:
        """Get employee headcount, average salary, average tenure."""
        import datetime

        year = str(datetime.date.today().year - 1)  # Previous year's annual report
        try:
            resp = httpx.get(
                f"{DART_BASE_URL}/empSttus.json",
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bsns_year": year,
                    "reprt_code": "11011",  # Annual report
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("list"):
                return [
                    {
                        "category": item.get("fo_bbm", ""),
                        "headcount": item.get("jan_salary_am", ""),
                        "avg_salary": item.get("sm", ""),
                    }
                    for item in data["list"]
                ]
        except Exception:
            pass
        return []

    def _get_financials(self, corp_code: str, api_key: str) -> list[dict[str, Any]]:
        """Get key financial statements (revenue, operating profit)."""
        import datetime

        year = str(datetime.date.today().year - 1)
        try:
            resp = httpx.get(
                f"{DART_BASE_URL}/fnlttSinglAcntAll.json",
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bsns_year": year,
                    "reprt_code": "11011",
                    "fs_div": "OFS",  # Individual financial statements
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("list"):
                key_accounts = ["매출액", "영업이익", "당기순이익", "자산총계", "부채총계"]
                return [
                    {
                        "account": item.get("account_nm", ""),
                        "current_amount": item.get("thstrm_amount", ""),
                        "previous_amount": item.get("frmtrm_amount", ""),
                    }
                    for item in data["list"]
                    if item.get("account_nm") in key_accounts
                ]
        except Exception:
            pass
        return []
