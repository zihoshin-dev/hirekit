"""DART (전자공시시스템) data source — financial statements, employee data."""

from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
import httpx

from hirekit.core.company_resolver import KNOWN_CORPS  # re-exported for backwards compat
from hirekit.core.config import DEFAULT_CONFIG_DIR
from hirekit.core.security import validate_url
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

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

        # 1. Resolve company name to corp_code
        corp_code = kwargs.get("corp_code") or self._resolve_corp_code(company, api_key)
        if not corp_code:
            logger.warning("Could not find DART corp_code for '%s'", company)
            return []

        logger.info("DART corp_code for '%s': %s", company, corp_code)

        # 2. Get company overview
        overview = self._get_overview(corp_code, api_key)
        if overview:
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="overview",
                    data=overview,
                    url=f"https://dart.fss.or.kr/corp/summary.ax?cmpCd={corp_code}",
                    raw=self._format_overview(overview),
                    source_authority="official",
                    trust_label="verified",
                    freshness_policy="core_company_fact",
                )
            )

        # 3. Get employee info (headcount, avg salary, avg tenure)
        emp_data = self._get_employee_info(corp_code, api_key)
        if emp_data:
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="overview",
                    data={"employees": emp_data},
                    raw=self._format_employees(emp_data),
                    source_authority="official",
                    trust_label="verified",
                    freshness_policy="core_company_fact",
                )
            )
            compensation_growth_reality = self._build_compensation_growth_reality(emp_data)
            if compensation_growth_reality:
                results.append(
                    SourceResult(
                        source_name=self.name,
                        section="financials",
                        data={"compensation_growth_reality": compensation_growth_reality},
                        raw=self._format_compensation_growth_reality(compensation_growth_reality),
                        source_authority="official",
                        trust_label="derived",
                        freshness_policy="core_company_fact",
                    )
                )

        # 4. Get financial highlights
        financials = self._get_financials(corp_code, api_key)
        if financials:
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="financials",
                    data={"financials": financials},
                    raw=self._format_financials(financials),
                    source_authority="official",
                    trust_label="verified",
                    freshness_policy="core_company_fact",
                )
            )
            growth_reality = self._build_growth_reality(financials)
            if growth_reality:
                results.append(
                    SourceResult(
                        source_name=self.name,
                        section="financials",
                        data={"growth_reality": growth_reality},
                        raw=self._format_growth_reality(growth_reality),
                        source_authority="official",
                        trust_label="derived",
                        freshness_policy="core_company_fact",
                    )
                )

        return results

    def _resolve_corp_code(self, company: str, api_key: str) -> str | None:
        """Resolve company name to DART corp_code.

        Strategy: known map -> corpCode.xml fuzzy search (cached locally).
        """
        # 1. Check known mappings first
        normalized = company.strip().replace("(주)", "").replace(" ", "")
        for known_name, code in KNOWN_CORPS.items():
            if normalized in known_name or known_name in normalized:
                return code

        # 2. Search via corpCode.xml (download once, cache locally)
        return self._search_corp_xml(company, api_key)

    def _search_corp_xml(self, company: str, api_key: str) -> str | None:
        """Download and search DART's full company code XML."""
        cache_path = DEFAULT_CONFIG_DIR / "dart_corps.xml"

        # Use cached XML if less than 7 days old
        if cache_path.exists():
            import time

            age_days = (time.time() - cache_path.stat().st_mtime) / 86400
            if age_days < 7:
                return self._parse_corp_xml(cache_path, company)

        # Download fresh corpCode.xml
        try:
            url = validate_url(f"{DART_BASE_URL}/corpCode.xml")
            resp = httpx.get(
                url,
                params={"crtfc_key": api_key},
                timeout=30,
            )
            if resp.status_code != 200:
                return None

            z = zipfile.ZipFile(io.BytesIO(resp.content))
            xml_data = z.read("CORPCODE.xml")

            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(xml_data)
            return self._parse_corp_xml(cache_path, company)
        except Exception as e:
            logger.warning("Failed to download DART corpCode.xml: %s", e)
            return None

    def _parse_corp_xml(self, xml_path: Path, company: str) -> str | None:
        """Search corpCode.xml for a company name. Prefer listed (stock_code) companies."""
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            return None
        if root is None:
            return None

        normalized = company.strip().replace("(주)", "").replace(" ", "")
        candidates: list[tuple[str, str, str]] = []

        for corp in root.findall("list"):
            name = corp.findtext("corp_name", "").replace("(주)", "").replace(" ", "")
            code = corp.findtext("corp_code", "")
            stock = corp.findtext("stock_code", "").strip()

            if normalized in name or name in normalized:
                candidates.append((name, code, stock))

        if not candidates:
            return None

        # Prefer listed companies (have stock_code)
        listed = [(n, c, s) for n, c, s in candidates if s]
        if listed:
            # Prefer exact match
            for n, c, s in listed:
                if n == normalized:
                    return c
            return listed[0][1]

        # Exact match among unlisted
        for n, c, s in candidates:
            if n == normalized:
                return c
        return candidates[0][1]

    def _get_overview(self, corp_code: str, api_key: str) -> dict[str, Any]:
        """Get company overview."""
        try:
            url = validate_url(f"{DART_BASE_URL}/company.json")
            resp = httpx.get(
                url,
                params={"crtfc_key": api_key, "corp_code": corp_code},
                timeout=10,
            )
            data = resp.json()
            if data.get("status") == "000":
                return {
                    "company_name": data.get("corp_name", ""),
                    "company_name_eng": data.get("corp_name_eng", ""),
                    "stock_name": data.get("stock_name", ""),
                    "ceo": data.get("ceo_nm", ""),
                    "address": data.get("adres", ""),
                    "industry_code": data.get("induty_code", ""),
                    "established": data.get("est_dt", ""),
                    "homepage": data.get("hm_url", ""),
                    "ir_url": data.get("ir_url", ""),
                    "stock_code": data.get("stock_code", ""),
                    "corp_class": data.get("corp_cls", ""),
                }
        except Exception as e:
            logger.warning("DART overview failed: %s", e)
        return {}

    def _get_employee_info(self, corp_code: str, api_key: str) -> list[dict[str, Any]]:
        """Get employee headcount, average salary."""
        import datetime

        year = str(datetime.date.today().year - 1)
        try:
            url = validate_url(f"{DART_BASE_URL}/empSttus.json")
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
                        "position": item.get("fo_bbm", ""),
                        "gender": item.get("sexdstn", ""),
                        "headcount": item.get("rgllbr_co", ""),
                        "contract_workers": item.get("cnttk_co", ""),
                        "total": item.get("sm", ""),
                        "avg_tenure_year": item.get("avrg_cnwk_sdytrn", ""),
                        "total_salary": item.get("jan_salary_am", ""),
                        "avg_salary": item.get("sm_a", ""),
                    }
                    for item in data["list"]
                ]
        except Exception as e:
            logger.warning("DART employee info failed: %s", e)
        return []

    def _get_financials(self, corp_code: str, api_key: str) -> list[dict[str, Any]]:
        """Get key financial statements."""
        import datetime

        year = str(datetime.date.today().year - 1)
        try:
            url = validate_url(f"{DART_BASE_URL}/fnlttSinglAcntAll.json")
            resp = httpx.get(
                url,
                params={
                    "crtfc_key": api_key,
                    "corp_code": corp_code,
                    "bsns_year": year,
                    "reprt_code": "11011",
                    "fs_div": "OFS",
                },
                timeout=15,
            )
            data = resp.json()
            if data.get("status") == "000" and data.get("list"):
                key_accounts = {
                    "매출액",
                    "영업이익",
                    "당기순이익",
                    "자산총계",
                    "부채총계",
                    "자본총계",
                }
                return [
                    {
                        "account": item.get("account_nm", ""),
                        "current_amount": item.get("thstrm_amount", ""),
                        "previous_amount": item.get("frmtrm_amount", ""),
                        "two_years_ago": item.get("bfefrmtrm_amount", ""),
                    }
                    for item in data["list"]
                    if item.get("account_nm") in key_accounts
                ]
        except Exception as e:
            logger.warning("DART financials failed: %s", e)
        return []

    # --- Formatting helpers for raw text (LLM consumption) ---

    @staticmethod
    def _format_overview(data: dict[str, Any]) -> str:
        return (
            f"회사명: {data.get('company_name', '')} ({data.get('company_name_eng', '')})\n"
            f"대표이사: {data.get('ceo', '')}\n"
            f"설립일: {data.get('established', '')}\n"
            f"주소: {data.get('address', '')}\n"
            f"홈페이지: {data.get('homepage', '')}\n"
            f"종목코드: {data.get('stock_code', '')}\n"
            f"업종코드: {data.get('industry_code', '')}"
        )

    @staticmethod
    def _format_employees(emp_list: list[dict[str, Any]]) -> str:
        lines = ["[직원 현황]"]
        for e in emp_list:
            lines.append(
                f"  {e.get('position', '')} {e.get('gender', '')}: "
                f"정규직 {e.get('headcount', '')}명, "
                f"평균근속 {e.get('avg_tenure_year', '')}년, "
                f"총급여 {e.get('total_salary', '')}백만원"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_financials(fin_list: list[dict[str, Any]]) -> str:
        lines = ["[주요 재무지표]"]
        for f in fin_list:
            lines.append(
                f"  {f.get('account', '')}: "
                f"당기 {f.get('current_amount', '')} / "
                f"전기 {f.get('previous_amount', '')} / "
                f"전전기 {f.get('two_years_ago', '')}"
            )
        return "\n".join(lines)

    @staticmethod
    def _to_number(value: str) -> int:
        try:
            return int(str(value).replace(",", "").strip() or "0")
        except ValueError:
            return 0

    @classmethod
    def _build_growth_reality(cls, fin_list: list[dict[str, Any]]) -> dict[str, Any]:
        revenue = next((item for item in fin_list if item.get("account") == "매출액"), None)
        if not revenue:
            return {}

        current = cls._to_number(str(revenue.get("current_amount", "0")))
        previous = cls._to_number(str(revenue.get("previous_amount", "0")))
        if not current and not previous:
            return {}

        growth_rate = 0.0
        if previous > 0:
            growth_rate = round(((current - previous) / previous) * 100, 1)

        direction = "flat"
        if growth_rate > 5:
            direction = "growing"
        elif growth_rate < -5:
            direction = "shrinking"

        return {
            "current_revenue": current,
            "previous_revenue": previous,
            "revenue_growth_rate": growth_rate,
            "revenue_growth_direction": direction,
        }

    @classmethod
    def _build_compensation_growth_reality(cls, emp_list: list[dict[str, Any]]) -> dict[str, Any]:
        if not emp_list:
            return {}

        headcount_total = sum(cls._to_number(str(item.get("headcount", "0"))) for item in emp_list)
        avg_salary_values = [
            cls._to_number(str(item.get("avg_salary", "0")))
            for item in emp_list
            if cls._to_number(str(item.get("avg_salary", "0"))) > 0
        ]
        avg_tenure_values = [
            float(str(item.get("avg_tenure_year", "0") or "0"))
            for item in emp_list
            if str(item.get("avg_tenure_year", "")).strip()
        ]

        return {
            "headcount_total": headcount_total,
            "salary_data_available": bool(avg_salary_values),
            "max_avg_salary": max(avg_salary_values) if avg_salary_values else 0,
            "avg_tenure_years": round(max(avg_tenure_values), 1) if avg_tenure_values else 0.0,
        }

    @staticmethod
    def _format_growth_reality(growth_reality: dict[str, Any]) -> str:
        return (
            "[성장 현실]\n"
            f"  당기 매출: {growth_reality.get('current_revenue', 0)}\n"
            f"  전기 매출: {growth_reality.get('previous_revenue', 0)}\n"
            f"  매출 성장률: {growth_reality.get('revenue_growth_rate', 0.0)}%\n"
            f"  방향: {growth_reality.get('revenue_growth_direction', 'flat')}"
        )

    @staticmethod
    def _format_compensation_growth_reality(summary: dict[str, Any]) -> str:
        return (
            "[보상/성장 현실]\n"
            f"  추정 총 인원: {summary.get('headcount_total', 0)}\n"
            f"  평균 급여 데이터 존재: {summary.get('salary_data_available', False)}\n"
            f"  최대 평균 급여: {summary.get('max_avg_salary', 0)}\n"
            f"  최대 평균 근속: {summary.get('avg_tenure_years', 0.0)}"
        )
