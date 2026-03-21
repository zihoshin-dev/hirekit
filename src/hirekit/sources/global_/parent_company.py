"""Parent company data source for foreign subsidiaries in Korea.

외국계 한국 지사 감지 시 본사 글로벌 재무·개요 데이터를 하드코딩된
공개 정보로 반환한다. 외부 API 호출 없이 동작하며 데모·분석 목적으로
활용한다.

sections: ["overview", "financials"]
"""

from __future__ import annotations

import logging
from typing import Any

from hirekit.core.company_resolver import resolve_company
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 본사 공개 정보 — 외부 API 없이 하드코딩된 공개 IR 데이터
# 출처: 각사 연간보고서(10-K/Annual Report), 공정위 공시, 언론 보도
# ---------------------------------------------------------------------------
_PARENT_DATA: dict[str, dict[str, Any]] = {
    "GOOGL": {
        "company": "Alphabet Inc.",
        "ticker": "GOOGL",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 348.2,
        "operating_income_usd_bn": 112.4,
        "net_income_usd_bn": 100.1,
        "market_cap_usd_bn": 2100.0,
        "employees_global": 181269,
        "hq": "Mountain View, CA, USA",
        "key_segments": ["Google Services", "Google Cloud", "Other Bets"],
        "ai_highlights": (
            "Gemini 모델 시리즈 출시, Google Cloud AI 매출 급성장, "
            "TPU v5 자체 AI 칩 운용"
        ),
        "source_note": "Alphabet 2024 Annual Report (10-K), Google IR",
    },
    "AAPL": {
        "company": "Apple Inc.",
        "ticker": "AAPL",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 391.1,
        "operating_income_usd_bn": 123.2,
        "net_income_usd_bn": 93.7,
        "market_cap_usd_bn": 3300.0,
        "employees_global": 150000,
        "hq": "Cupertino, CA, USA",
        "key_segments": ["iPhone", "Mac", "iPad", "Wearables", "Services"],
        "ai_highlights": (
            "Apple Intelligence(온디바이스 AI) 출시, "
            "Siri 고도화, App Store AI 에코시스템 확대"
        ),
        "source_note": "Apple FY2024 Annual Report (10-K)",
    },
    "META": {
        "company": "Meta Platforms Inc.",
        "ticker": "META",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 164.8,
        "operating_income_usd_bn": 68.6,
        "net_income_usd_bn": 62.4,
        "market_cap_usd_bn": 1500.0,
        "employees_global": 72404,
        "hq": "Menlo Park, CA, USA",
        "key_segments": ["Family of Apps", "Reality Labs"],
        "ai_highlights": (
            "Llama 3 오픈소스 공개, Meta AI 어시스턴트 글로벌 출시, "
            "광고 AI 최적화로 매출 성장"
        ),
        "source_note": "Meta Platforms 2024 Annual Report (10-K)",
    },
    "NVDA": {
        "company": "NVIDIA Corporation",
        "ticker": "NVDA",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2025",
        "revenue_usd_bn": 130.3,
        "operating_income_usd_bn": 81.5,
        "net_income_usd_bn": 72.9,
        "market_cap_usd_bn": 3400.0,
        "employees_global": 36000,
        "hq": "Santa Clara, CA, USA",
        "key_segments": ["Data Center", "Gaming", "Professional Visualization", "Automotive"],
        "ai_highlights": (
            "H100/H200/B200 GPU 수요 폭발, NIM 마이크로서비스 플랫폼, "
            "CUDA 생태계 독점적 지위"
        ),
        "source_note": "NVIDIA FY2025 Annual Report (10-K)",
    },
    "TSLA": {
        "company": "Tesla Inc.",
        "ticker": "TSLA",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 97.7,
        "operating_income_usd_bn": 7.1,
        "net_income_usd_bn": 7.3,
        "market_cap_usd_bn": 1000.0,
        "employees_global": 121000,
        "hq": "Austin, TX, USA",
        "key_segments": ["Automotive", "Energy Generation & Storage", "Services"],
        "ai_highlights": (
            "FSD(완전자율주행) v12 출시, Dojo 슈퍼컴퓨터, "
            "Optimus 로봇 양산 준비"
        ),
        "source_note": "Tesla 2024 Annual Report (10-K)",
    },
    "CRM": {
        "company": "Salesforce Inc.",
        "ticker": "CRM",
        "exchange": "NYSE",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 34.7,
        "operating_income_usd_bn": 5.0,
        "net_income_usd_bn": 4.1,
        "market_cap_usd_bn": 280.0,
        "employees_global": 72682,
        "hq": "San Francisco, CA, USA",
        "key_segments": ["Sales Cloud", "Service Cloud", "Marketing Cloud", "Platform"],
        "ai_highlights": (
            "Einstein AI 플랫폼 전면 확대, Agentforce(AI 에이전트) 출시, "
            "Data Cloud 통합"
        ),
        "source_note": "Salesforce FY2024 Annual Report (10-K)",
    },
    "MSFT": {
        "company": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 245.4,
        "operating_income_usd_bn": 109.4,
        "net_income_usd_bn": 88.1,
        "market_cap_usd_bn": 3100.0,
        "employees_global": 228000,
        "hq": "Redmond, WA, USA",
        "key_segments": ["Intelligent Cloud", "Productivity & Business Processes", "Personal Computing"],
        "ai_highlights": (
            "Copilot(GPT-4 기반) 전 제품 통합, Azure OpenAI Service, "
            "GitHub Copilot 유료 구독 성장"
        ),
        "source_note": "Microsoft FY2024 Annual Report (10-K)",
    },
    "AMZN": {
        "company": "Amazon.com Inc.",
        "ticker": "AMZN",
        "exchange": "NASDAQ",
        "fiscal_year": "FY2024",
        "revenue_usd_bn": 638.0,
        "operating_income_usd_bn": 68.6,
        "net_income_usd_bn": 59.2,
        "market_cap_usd_bn": 2200.0,
        "employees_global": 1550000,
        "hq": "Seattle, WA, USA",
        "key_segments": ["AWS", "North America Retail", "International Retail", "Advertising"],
        "ai_highlights": (
            "AWS Bedrock(멀티모달 AI), Amazon Q(기업용 AI), "
            "Trainium2/Inferentia2 자체 AI 칩, Anthropic 투자"
        ),
        "source_note": "Amazon 2024 Annual Report (10-K)",
    },
    # 비상장사 — 공개된 언론 보도 및 펀딩 라운드 기준
    "Anthropic": {
        "company": "Anthropic PBC",
        "ticker": "",
        "exchange": "비상장",
        "fiscal_year": "2024",
        "revenue_usd_bn": None,
        "operating_income_usd_bn": None,
        "net_income_usd_bn": None,
        "market_cap_usd_bn": 61.5,  # 2024년 시리즈E 기준 기업가치
        "employees_global": 1000,
        "hq": "San Francisco, CA, USA",
        "key_segments": ["Claude API", "Claude.ai", "Enterprise"],
        "ai_highlights": (
            "Claude 3.5 Sonnet/Haiku 출시, Constitutional AI 연구, "
            "Amazon·Google 전략적 투자"
        ),
        "source_note": "Anthropic 공개 블로그, TechCrunch 펀딩 보도 (2024)",
    },
    "OpenAI": {
        "company": "OpenAI LLC",
        "ticker": "",
        "exchange": "비상장",
        "fiscal_year": "2024",
        "revenue_usd_bn": 3.7,
        "operating_income_usd_bn": None,
        "net_income_usd_bn": None,
        "market_cap_usd_bn": 157.0,  # 2024년 10월 펀딩 기준
        "employees_global": 3000,
        "hq": "San Francisco, CA, USA",
        "key_segments": ["ChatGPT", "GPT-4o API", "Enterprise", "Sora"],
        "ai_highlights": (
            "GPT-4o·o1 출시, ChatGPT 유료 구독 2억 명+, "
            "Sora 동영상 생성 AI 공개"
        ),
        "source_note": "OpenAI 공개 발표, The Information 보도 (2024)",
    },
    "xAI": {
        "company": "xAI Corp",
        "ticker": "",
        "exchange": "비상장",
        "fiscal_year": "2024",
        "revenue_usd_bn": None,
        "operating_income_usd_bn": None,
        "net_income_usd_bn": None,
        "market_cap_usd_bn": 50.0,  # 2024년 시리즈B 기준
        "employees_global": 2000,
        "hq": "Palo Alto, CA, USA",
        "key_segments": ["Grok AI", "X(Twitter) AI 통합"],
        "ai_highlights": (
            "Grok-2 출시, X(Twitter) 플랫폼 AI 통합, "
            "Colossus 슈퍼컴퓨터(100k H100) 구축"
        ),
        "source_note": "xAI 공개 발표, Bloomberg 보도 (2024)",
    },
}

# 티커 → _PARENT_DATA 키 매핑 (비상장사는 회사명 직접 사용)
_TICKER_TO_KEY: dict[str, str] = {
    "GOOGL": "GOOGL",
    "AAPL": "AAPL",
    "META": "META",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "CRM": "CRM",
    "MSFT": "MSFT",
    "AMZN": "AMZN",
}
_UNLISTED_TO_KEY: dict[str, str] = {
    "Anthropic PBC": "Anthropic",
    "OpenAI LLC": "OpenAI",
    "xAI Corp": "xAI",
    "Alphabet Inc. (Google DeepMind)": "GOOGL",
}


@SourceRegistry.register
class ParentCompanySource(BaseSource):
    """외국계 한국 지사의 본사 글로벌 재무·개요 데이터를 반환한다.

    - 외부 API 호출 없음 (하드코딩된 공개 정보)
    - is_foreign=True인 CompanyInfo에서만 유효한 데이터 반환
    - sections: overview(본사 개요), financials(글로벌 재무)
    """

    name = "parent_company"
    region = "global"
    sections = ["overview", "financials"]
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        info = resolve_company(company)
        if info is None or not info.is_foreign:
            return []

        parent_data = self._lookup_parent(info)
        if parent_data is None:
            logger.debug("parent_company: no data for '%s' (parent=%s)", company, info.parent_company)
            return []

        results: list[SourceResult] = []

        # overview 섹션
        overview_data = self._build_overview(info, parent_data)
        results.append(SourceResult(
            source_name=self.name,
            section="overview",
            data=overview_data,
            confidence=0.9,
            url=self._ir_url(parent_data),
            raw=self._format_overview_raw(company, info, parent_data),
        ))

        # financials 섹션
        fin_data = self._build_financials(info, parent_data)
        results.append(SourceResult(
            source_name=self.name,
            section="financials",
            data=fin_data,
            confidence=0.85,
            url=self._ir_url(parent_data),
            raw=self._format_financials_raw(company, info, parent_data),
        ))

        return results

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _lookup_parent(self, info: Any) -> dict[str, Any] | None:
        """티커 또는 본사명으로 _PARENT_DATA 조회."""
        if info.parent_ticker and info.parent_ticker in _TICKER_TO_KEY:
            return _PARENT_DATA[_TICKER_TO_KEY[info.parent_ticker]]
        if info.parent_company in _UNLISTED_TO_KEY:
            key = _UNLISTED_TO_KEY[info.parent_company]
            return _PARENT_DATA.get(key)
        # 회사명 직접 매핑 시도
        for key, data in _PARENT_DATA.items():
            if data["company"] == info.parent_company:
                return data
        return None

    @staticmethod
    def _ir_url(parent_data: dict[str, Any]) -> str:
        ticker = parent_data.get("ticker", "")
        if ticker:
            return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=10-K"
        return ""

    @staticmethod
    def _build_overview(info: Any, pd: dict[str, Any]) -> dict[str, Any]:
        return {
            "is_foreign_subsidiary": True,
            "kr_entity": info.corp_name or info.name,
            "parent_company": pd["company"],
            "parent_ticker": pd.get("ticker", ""),
            "parent_exchange": pd.get("exchange", ""),
            "parent_hq": pd.get("hq", ""),
            "parent_employees_global": pd.get("employees_global"),
            "parent_key_segments": pd.get("key_segments", []),
            "parent_ai_highlights": pd.get("ai_highlights", ""),
            "kr_revenue_summary": info.kr_revenue or "공개 정보 없음",
            "data_note": (
                "외국계 한국 지사는 DART 공시 의무가 없어 본사 글로벌 데이터를 제공해요. "
                f"출처: {pd.get('source_note', '')}"
            ),
        }

    @staticmethod
    def _build_financials(info: Any, pd: dict[str, Any]) -> dict[str, Any]:
        fy = pd.get("fiscal_year", "")
        rev = pd.get("revenue_usd_bn")
        op = pd.get("operating_income_usd_bn")
        ni = pd.get("net_income_usd_bn")
        mc = pd.get("market_cap_usd_bn")

        items: list[dict[str, str]] = []
        if rev is not None:
            items.append({"account": f"글로벌 매출 ({fy})", "value_usd_bn": str(rev), "display": f"${rev:,.1f}B"})
        if op is not None:
            items.append({"account": f"영업이익 ({fy})", "value_usd_bn": str(op), "display": f"${op:,.1f}B"})
        if ni is not None:
            items.append({"account": f"순이익 ({fy})", "value_usd_bn": str(ni), "display": f"${ni:,.1f}B"})
        if mc is not None:
            items.append({"account": "시가총액 (추정)", "value_usd_bn": str(mc), "display": f"${mc:,.0f}B"})
        if info.kr_revenue:
            items.append({"account": "한국 매출 (추정)", "value_usd_bn": "", "display": info.kr_revenue})

        return {
            "is_foreign_subsidiary": True,
            "parent_company": pd["company"],
            "fiscal_year": fy,
            "listed": bool(pd.get("ticker")),
            "exchange": pd.get("exchange", ""),
            "financials": items,
            "source_note": pd.get("source_note", ""),
            "dart_note": (
                "외국계 한국 지사는 DART 공시 의무가 없어 본사 글로벌 데이터를 제공해요."
            ),
        }

    @staticmethod
    def _format_overview_raw(company: str, info: Any, pd: dict[str, Any]) -> str:
        lines = [
            f"[{company} — 외국계 한국 지사]",
            f"한국 법인명: {info.corp_name or info.name}",
            f"본사: {pd['company']} ({pd.get('exchange', '비상장')}:{pd.get('ticker', '-')})",
            f"본사 소재지: {pd.get('hq', '')}",
            f"글로벌 임직원: {pd.get('employees_global', 0):,}명",
            f"주요 사업부문: {', '.join(pd.get('key_segments', []))}",
            f"AI 전략: {pd.get('ai_highlights', '')}",
            f"한국 매출: {info.kr_revenue or '공개 정보 없음'}",
            f"※ {pd.get('source_note', '')}",
            "※ 외국계 한국 지사는 DART 공시 의무가 없어 본사 글로벌 데이터를 제공해요.",
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_financials_raw(company: str, info: Any, pd: dict[str, Any]) -> str:
        fy = pd.get("fiscal_year", "")
        lines = [f"[{company} 본사 글로벌 재무 — {fy}]"]
        if pd.get("revenue_usd_bn") is not None:
            lines.append(f"글로벌 매출: ${pd['revenue_usd_bn']:,.1f}B")
        if pd.get("operating_income_usd_bn") is not None:
            lines.append(f"영업이익: ${pd['operating_income_usd_bn']:,.1f}B")
        if pd.get("net_income_usd_bn") is not None:
            lines.append(f"순이익: ${pd['net_income_usd_bn']:,.1f}B")
        if pd.get("market_cap_usd_bn") is not None:
            lines.append(f"시가총액: ${pd['market_cap_usd_bn']:,.0f}B")
        if info.kr_revenue:
            lines.append(f"한국 매출(추정): {info.kr_revenue}")
        lines.append(f"※ {pd.get('source_note', '')}")
        lines.append("※ 외국계 한국 지사는 DART 공시 의무가 없어 본사 글로벌 데이터를 제공해요.")
        return "\n".join(lines)
