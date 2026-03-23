from __future__ import annotations

from typing import Final

from hirekit.sources.base import SourceResult


SOURCE_AUTHORITY: Final[dict[str, int]] = {
    "dart": 3,
    "ir_report": 3,
    "pension": 2,
    "nts_biz": 2,
    "google_news": 2,
    "credible_news": 2,
    "github": 2,
    "tech_blog": 2,
    "naver_news": 1,
    "naver_search": 1,
    "exa_search": 1,
    "community_review": 1,
    "medium_velog": 1,
}

_CULTURE_SIGNAL_MAP: Final[dict[str, str]] = {
    "work_life_balance": "워라밸",
    "wlb": "워라밸",
    "leadership": "리더십",
    "growth": "성장",
    "benefits": "복지",
}


def source_authority(source_name: str) -> int:
    return SOURCE_AUTHORITY.get(source_name, 1)


def conflicting_keys(source_results: list[SourceResult]) -> set[str]:
    seen: dict[str, set[str]] = {}
    for result in source_results:
        for key, value in result.data.items():
            if isinstance(value, (str, int, float, bool)):
                seen.setdefault(key, set()).add(str(value).strip().lower())
    return {key for key, values in seen.items() if len(values) > 1}


def derive_confidence(expected_sources: list[str], source_results: list[SourceResult]) -> str:
    relevant = [result for result in source_results if result.source_name in expected_sources]
    if not relevant:
        return "low"

    fresh = [result for result in relevant if not result.is_stale]
    if not fresh:
        return "low"

    matched_names = {result.source_name for result in fresh}
    authority_points = sum(source_authority(result.source_name) for result in fresh)

    if len(matched_names) >= 3 and authority_points >= 4:
        confidence = "high"
    elif len(matched_names) >= 1 and authority_points >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    if len(fresh) < len(relevant) and confidence == "high":
        confidence = "medium"

    if conflicting_keys(fresh):
        if confidence == "high":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "low"

    return confidence


def culture_signal_labels(source_results: list[SourceResult]) -> list[str]:
    labels: list[str] = []
    for result in source_results:
        for key, label in _CULTURE_SIGNAL_MAP.items():
            if key in result.data and label not in labels:
                labels.append(label)
    return labels
