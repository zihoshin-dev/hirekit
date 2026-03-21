"""Business segment analysis — rule-based extraction of revenue segments and diversification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BusinessSegment:
    """A single business segment within a company."""

    name: str
    revenue_ratio: float | None = None  # 0.0–1.0
    growth_direction: str = "유지"  # "성장", "유지", "축소"
    key_products: list[str] = field(default_factory=list)


@dataclass
class BusinessAnalysis:
    """Full business segment analysis for a company."""

    segments: list[BusinessSegment] = field(default_factory=list)
    main_segment: str = ""
    diversification_level: str = "단일사업"  # "단일사업", "다각화초기", "다각화"


# Known segment data per company (rule-based seed)
_KNOWN_SEGMENTS: dict[str, list[dict[str, Any]]] = {
    "카카오": [
        {"name": "플랫폼", "revenue_ratio": 0.35, "growth_direction": "유지",
         "key_products": ["카카오톡", "검색", "광고"]},
        {"name": "콘텐츠", "revenue_ratio": 0.30, "growth_direction": "성장",
         "key_products": ["카카오엔터테인먼트", "웹툰", "게임"]},
        {"name": "커머스", "revenue_ratio": 0.20, "growth_direction": "성장",
         "key_products": ["카카오쇼핑", "카카오메이커스"]},
        {"name": "핀테크", "revenue_ratio": 0.15, "growth_direction": "성장",
         "key_products": ["카카오페이", "카카오뱅크"]},
    ],
    "네이버": [
        {"name": "서치플랫폼", "revenue_ratio": 0.30, "growth_direction": "유지",
         "key_products": ["네이버 검색", "디스플레이 광고"]},
        {"name": "커머스", "revenue_ratio": 0.25, "growth_direction": "성장",
         "key_products": ["스마트스토어", "브랜드스토어"]},
        {"name": "핀테크", "revenue_ratio": 0.15, "growth_direction": "성장",
         "key_products": ["네이버페이"]},
        {"name": "콘텐츠", "revenue_ratio": 0.20, "growth_direction": "성장",
         "key_products": ["웹툰", "시리즈", "치지직"]},
        {"name": "클라우드", "revenue_ratio": 0.10, "growth_direction": "성장",
         "key_products": ["네이버클라우드", "CLOVA"]},
    ],
    "토스": [
        {"name": "금융플랫폼", "revenue_ratio": 0.50, "growth_direction": "성장",
         "key_products": ["토스", "간편송금", "대출중개"]},
        {"name": "뱅킹", "revenue_ratio": 0.30, "growth_direction": "성장",
         "key_products": ["토스뱅크"]},
        {"name": "증권", "revenue_ratio": 0.20, "growth_direction": "성장",
         "key_products": ["토스증권"]},
    ],
    "쿠팡": [
        {"name": "프로덕트커머스", "revenue_ratio": 0.70, "growth_direction": "유지",
         "key_products": ["로켓배송", "쿠팡마켓플레이스"]},
        {"name": "개발도상 오퍼링", "revenue_ratio": 0.30, "growth_direction": "성장",
         "key_products": ["쿠팡이츠", "쿠팡플레이", "로켓그로스"]},
    ],
    "우아한형제들": [
        {"name": "음식배달", "revenue_ratio": 0.85, "growth_direction": "유지",
         "key_products": ["배달의민족"]},
        {"name": "B2B솔루션", "revenue_ratio": 0.15, "growth_direction": "성장",
         "key_products": ["배민상회", "배민외식업광장"]},
    ],
    "배달의민족": [
        {"name": "음식배달", "revenue_ratio": 0.85, "growth_direction": "유지",
         "key_products": ["배달의민족"]},
        {"name": "B2B솔루션", "revenue_ratio": 0.15, "growth_direction": "성장",
         "key_products": ["배민상회", "배민외식업광장"]},
    ],
}


def analyze_segments(company: str, source_data: dict[str, Any]) -> BusinessAnalysis:
    """Analyze a company's business segments from available source data.

    Parameters
    ----------
    company:
        Company name (Korean canonical form preferred).
    source_data:
        Dict mapping source_name → data dict (from SourceResult.data).

    Returns
    -------
    BusinessAnalysis
        Rule-based result. No LLM calls.
    """
    normalized = company.strip().replace(" ", "")

    # Look up known segments
    seed_segments: list[dict[str, Any]] = []
    for known, segs in _KNOWN_SEGMENTS.items():
        if normalized in known.replace(" ", "") or known.replace(" ", "") in normalized:
            seed_segments = segs
            break

    if seed_segments:
        segments = [
            BusinessSegment(
                name=s["name"],
                revenue_ratio=s.get("revenue_ratio"),
                growth_direction=s.get("growth_direction", "유지"),
                key_products=s.get("key_products", []),
            )
            for s in seed_segments
        ]
    else:
        # Fall back to minimal single-segment inference from financial data
        segments = _infer_segments_from_financials(source_data)

    main_segment = _determine_main_segment(segments)
    diversification_level = _classify_diversification(segments)

    return BusinessAnalysis(
        segments=segments,
        main_segment=main_segment,
        diversification_level=diversification_level,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _infer_segments_from_financials(source_data: dict[str, Any]) -> list[BusinessSegment]:
    """Attempt to infer segments from financial data when no seed data available."""
    financials = source_data.get("dart", {}).get("financials", [])
    if not financials:
        return []

    # Without segment breakdown, create a single segment placeholder
    return [
        BusinessSegment(
            name="주요사업",
            revenue_ratio=1.0,
            growth_direction="유지",
            key_products=[],
        )
    ]


def _determine_main_segment(segments: list[BusinessSegment]) -> str:
    """Return the segment name with the highest revenue ratio."""
    if not segments:
        return ""
    # Sort by revenue_ratio descending; treat None as 0
    top = max(segments, key=lambda s: s.revenue_ratio or 0.0)
    return top.name


def _classify_diversification(segments: list[BusinessSegment]) -> str:
    """Classify diversification level based on segment count and ratios."""
    n = len(segments)
    if n <= 1:
        return "단일사업"
    if n == 2:
        return "다각화초기"
    # Check if any single segment dominates (>70%)
    for s in segments:
        if (s.revenue_ratio or 0) > 0.70:
            return "다각화초기"
    return "다각화"
