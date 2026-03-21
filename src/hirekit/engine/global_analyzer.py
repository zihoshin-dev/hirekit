"""Global presence analyzer — rule-based extraction of company's global footprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GlobalPresence:
    """Structured representation of a company's global presence."""

    regions: list[str] = field(default_factory=list)
    global_revenue_ratio: float | None = None  # 0.0–1.0
    global_products: list[str] = field(default_factory=list)
    global_offices: list[str] = field(default_factory=list)
    expansion_stage: str = "준비중"  # "준비중", "초기진출", "성장", "성숙"


# Known global signals per company (rule-based seed data)
_GLOBAL_SIGNALS: dict[str, dict[str, Any]] = {
    "카카오": {
        "regions": ["일본", "동남아", "미국"],
        "global_products": ["카카오웹툰", "픽코마"],
        "global_offices": ["일본", "미국"],
        "expansion_stage": "성장",
    },
    "네이버": {
        "regions": ["일본", "유럽", "미국", "동남아"],
        "global_products": ["라인", "LY Corp", "웹툰", "스노우"],
        "global_offices": ["일본", "프랑스", "미국", "싱가포르"],
        "expansion_stage": "성숙",
    },
    "라인": {
        "regions": ["일본", "태국", "대만", "인도네시아"],
        "global_products": ["LINE", "LY Corp"],
        "global_offices": ["일본", "태국", "대만", "인도네시아"],
        "expansion_stage": "성숙",
    },
    "라인플러스": {
        "regions": ["일본", "태국", "대만", "인도네시아"],
        "global_products": ["LINE", "LY Corp"],
        "global_offices": ["일본", "태국", "대만"],
        "expansion_stage": "성숙",
    },
    "쿠팡": {
        "regions": ["미국", "대만"],
        "global_products": ["Coupang Play", "Coupang Eats"],
        "global_offices": ["미국", "대만"],
        "expansion_stage": "성장",
    },
    "토스": {
        "regions": ["동남아"],
        "global_products": ["토스뱅크"],
        "global_offices": [],
        "expansion_stage": "초기진출",
    },
    "야놀자": {
        "regions": ["동남아", "미국", "유럽"],
        "global_products": ["야놀자 클라우드"],
        "global_offices": ["싱가포르", "미국"],
        "expansion_stage": "성장",
    },
    "무신사": {
        "regions": ["일본"],
        "global_products": ["무신사 글로벌"],
        "global_offices": ["일본"],
        "expansion_stage": "초기진출",
    },
}

# Keywords that signal global revenue/presence in text
_REGION_KEYWORDS: dict[str, list[str]] = {
    "미국": ["미국", "US", "North America", "북미", "실리콘밸리"],
    "일본": ["일본", "Japan", "도쿄", "Tokyo"],
    "동남아": ["동남아", "Southeast Asia", "싱가포르", "Singapore", "인도네시아", "베트남", "태국"],
    "유럽": ["유럽", "Europe", "프랑스", "독일", "영국"],
    "중국": ["중국", "China", "베이징", "상하이"],
    "대만": ["대만", "Taiwan"],
    "글로벌": ["글로벌", "global", "worldwide", "해외"],
}

_GLOBAL_REVENUE_KEYWORDS = [
    "해외 매출", "글로벌 매출", "해외매출", "overseas revenue",
    "international revenue", "해외 비중", "글로벌 비중",
]


def analyze_global(company: str, source_data: dict[str, Any]) -> GlobalPresence:
    """Analyze a company's global presence from available source data.

    Parameters
    ----------
    company:
        Company name (Korean canonical form preferred).
    source_data:
        Dict mapping source_name → data dict (from SourceResult.data).

    Returns
    -------
    GlobalPresence
        Rule-based analysis result. No LLM calls.
    """
    # Start with seed signals if known
    normalized = company.strip().replace(" ", "")
    seed: dict[str, Any] = {}
    for known, signals in _GLOBAL_SIGNALS.items():
        if normalized in known.replace(" ", "") or known.replace(" ", "") in normalized:
            seed = signals
            break

    regions: set[str] = set(seed.get("regions", []))
    global_products: list[str] = list(seed.get("global_products", []))
    global_offices: list[str] = list(seed.get("global_offices", []))
    expansion_stage: str = seed.get("expansion_stage", "준비중")
    global_revenue_ratio: float | None = None

    # Extract from ir_report data
    ir_data = source_data.get("ir_report", {})
    _extract_from_text(ir_data.get("annual_report_name", ""), regions)

    # Extract from strategy section text (raw news / naver_news etc.)
    for src_name in ("naver_news", "google_news", "credible_news"):
        news_data = source_data.get(src_name, {})
        for article_list_key in ("articles", "results", "items"):
            articles = news_data.get(article_list_key, [])
            if isinstance(articles, list):
                for article in articles[:10]:
                    text = ""
                    if isinstance(article, dict):
                        text = (
                            article.get("title", "") + " " +
                            article.get("description", "") + " " +
                            article.get("snippet", "")
                        )
                    _extract_from_text(text, regions)

    # Infer global_revenue_ratio from IR data if available
    global_revenue_ratio = _infer_revenue_ratio(ir_data, source_data)

    # Determine expansion_stage from evidence (override seed if richer data found)
    if not seed:
        expansion_stage = _infer_expansion_stage(regions, global_offices, global_revenue_ratio)

    return GlobalPresence(
        regions=sorted(regions),
        global_revenue_ratio=global_revenue_ratio,
        global_products=global_products,
        global_offices=global_offices,
        expansion_stage=expansion_stage,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_from_text(text: str, regions: set[str]) -> None:
    """Detect region mentions in text and add to regions set."""
    if not text:
        return
    for region, keywords in _REGION_KEYWORDS.items():
        if any(kw.lower() in text.lower() for kw in keywords):
            regions.add(region)


def _infer_revenue_ratio(ir_data: dict[str, Any], source_data: dict[str, Any]) -> float | None:
    """Try to infer global revenue ratio from available data. Returns None if undetectable."""
    # Currently rule-based: look for explicit ratio fields in ir_report data
    ratio = ir_data.get("global_revenue_ratio")
    if ratio is not None:
        try:
            return float(ratio)
        except (TypeError, ValueError):
            pass
    return None


def _infer_expansion_stage(
    regions: set[str],
    offices: list[str],
    revenue_ratio: float | None,
) -> str:
    """Infer expansion stage from available evidence."""
    region_count = len(regions)
    office_count = len(offices)

    if revenue_ratio is not None and revenue_ratio > 0.5:
        return "성숙"
    if revenue_ratio is not None and revenue_ratio > 0.2:
        return "성장"

    if region_count >= 4 or office_count >= 3:
        return "성숙"
    if region_count >= 2 or office_count >= 1:
        return "성장"
    if region_count >= 1:
        return "초기진출"
    return "준비중"
