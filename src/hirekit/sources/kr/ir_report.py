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

        dart = DartSource()
        corp_code = kwargs.get("corp_code") or dart._resolve_corp_code(company, api_key)
        if not corp_code:
            logger.warning("IRReportSource: could not find DART corp_code for '%s'", company)
            return []

        results: list[SourceResult] = []

        shareholders = self._get_major_shareholders(corp_code, api_key)
        if shareholders:
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="overview",
                    data={
                        "major_shareholders": shareholders,
                        "leadership_evidence": self._build_shareholder_leadership_evidence(shareholders),
                        "org_health_evidence": self._build_shareholder_org_health_evidence(shareholders),
                    },
                    url=f"https://dart.fss.or.kr/corp/summary.ax?cmpCd={corp_code}",
                    raw=self._format_shareholders(shareholders),
                    confidence=0.95,
                    trust_label="verified",
                    source_authority="official",
                )
            )

        report_data = self._get_business_report_data(corp_code, api_key)
        if report_data:
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="strategy",
                    data={
                        **report_data,
                        "strategic_direction_evidence": self._build_report_strategy_evidence(company, report_data),
                    },
                    url=f"https://dart.fss.or.kr/corp/summary.ax?cmpCd={corp_code}",
                    raw=self._format_report_data(company, report_data),
                    confidence=0.95,
                    trust_label="verified",
                    source_authority="official",
                )
            )

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

    @staticmethod
    def _build_shareholder_leadership_evidence(shareholders: list[dict[str, Any]]) -> list[dict[str, str]]:
        evidence: list[dict[str, str]] = []
        for index, shareholder in enumerate(shareholders[:3], start=1):
            name = str(shareholder.get("name", "")).strip()
            relation = str(shareholder.get("relation", "")).strip()
            ratio = str(shareholder.get("ownership_ratio", "")).strip()
            if not name:
                continue

            relation_label = f" {relation}" if relation else ""
            ratio_label = f" 지분 {ratio}%" if ratio else ""
            evidence.append(
                {
                    "claim_key": "leadership_governance_backbone",
                    "summary": f"공식 공시에 {name}{relation_label}{ratio_label} 정보가 확인됨",
                    "status": "stable",
                    "source_name": "ir_report",
                    "source_authority": "official",
                    "trust_label": "verified",
                    "evidence_id": f"ir_report:leadership:shareholder:{index}",
                }
            )

        return evidence

    @staticmethod
    def _build_shareholder_org_health_evidence(shareholders: list[dict[str, Any]]) -> list[dict[str, str]]:
        evidence: list[dict[str, str]] = []
        for index, shareholder in enumerate(shareholders[:3], start=1):
            name = str(shareholder.get("name", "")).strip()
            ratio = str(shareholder.get("ownership_ratio", "")).strip()
            if not name:
                continue

            ratio_label = f" ({ratio}%)" if ratio else ""
            evidence.append(
                {
                    "claim_key": "governance_health",
                    "summary": f"주요 주주 구조 공시: {name}{ratio_label}",
                    "status": "stable",
                    "source_name": "ir_report",
                    "source_authority": "official",
                    "trust_label": "verified",
                    "evidence_id": f"ir_report:org_health:shareholder:{index}",
                }
            )

        return evidence

    @staticmethod
    def _build_report_strategy_evidence(company: str, report_data: dict[str, Any]) -> list[dict[str, str]]:
        report_name = str(report_data.get("annual_report_name", "")).strip()
        filing_date = str(report_data.get("filing_date", "")).strip()
        report_url = str(report_data.get("report_url", "")).strip()
        if not report_name:
            return []

        filing_label = f" ({filing_date})" if filing_date else ""
        return [
            {
                "claim_key": "official_strategy_backbone",
                "summary": f"{company} {report_name}{filing_label}",
                "status": "declared",
                "source_name": "ir_report",
                "source_authority": "official",
                "trust_label": "verified",
                "evidence_id": "ir_report:strategic_direction:annual_report",
                "url": report_url,
            }
        ]

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
