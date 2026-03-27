from __future__ import annotations

from typing import Any, Final

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

_SOURCE_AUTHORITY_BY_LABEL: Final[dict[str, int]] = {
    "official": 3,
    "company_operated": 3,
    "credible_reporting": 2,
    "secondary_research": 1,
    "community": 1,
    "generated": 0,
}


def source_authority(source_name: str) -> int:
    return SOURCE_AUTHORITY.get(source_name, 1)


def source_authority_score(result: SourceResult) -> int:
    authority = result.source_authority or "secondary_research"
    return _SOURCE_AUTHORITY_BY_LABEL.get(authority, source_authority(result.source_name))


def conflicting_keys(source_results: list[SourceResult]) -> set[str]:
    seen: dict[str, set[str]] = {}
    for result in source_results:
        for key, value in result.data.items():
            if isinstance(value, (str, int, float, bool)):
                seen.setdefault(key, set()).add(str(value).strip().lower())
    return {key for key, values in seen.items() if len(values) > 1}


def derive_confidence(expected_sources: list[str], source_results: list[SourceResult]) -> str:
    return summarize_evidence_state(expected_sources, source_results)["confidence"]


def summarize_evidence_state(expected_sources: list[str], source_results: list[SourceResult]) -> dict[str, Any]:
    relevant = [result for result in source_results if result.source_name in expected_sources]
    if not relevant:
        return {
            "confidence": "low",
            "has_conflicts": False,
            "conflicting_keys": [],
            "stale_sources": [],
            "supporting_sources": [],
            "matched_sources": [],
        }

    fresh = [result for result in relevant if not result.is_stale]
    stale_sources = sorted({result.source_name for result in relevant if result.is_stale})
    if not fresh:
        return {
            "confidence": "low",
            "has_conflicts": False,
            "conflicting_keys": [],
            "stale_sources": stale_sources,
            "supporting_sources": [],
            "matched_sources": sorted({result.source_name for result in relevant}),
        }

    matched_names = {result.source_name for result in fresh}
    authority_points = sum(source_authority_score(result) for result in fresh)
    authoritative_sources = sum(1 for result in fresh if source_authority_score(result) >= 2)
    supporting_sources = sorted({result.source_name for result in fresh if result.trust_label == "supporting"})
    conflicts = sorted(conflicting_keys(fresh))

    if len(matched_names) >= 3 and authority_points >= 5 and authoritative_sources >= 2:
        confidence = "high"
    elif len(matched_names) >= 1 and authority_points >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    if len(fresh) < len(relevant) and confidence == "high":
        confidence = "medium"

    if conflicts:
        if confidence == "high":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "low"

    if supporting_sources and confidence == "high":
        confidence = "medium"

    return {
        "confidence": confidence,
        "has_conflicts": bool(conflicts),
        "conflicting_keys": conflicts,
        "stale_sources": stale_sources,
        "supporting_sources": supporting_sources,
        "matched_sources": sorted(matched_names),
    }


def culture_signal_labels(source_results: list[SourceResult]) -> list[str]:
    labels: list[str] = []
    for result in source_results:
        for key, label in _CULTURE_SIGNAL_MAP.items():
            if key in result.data and label not in labels:
                labels.append(label)
    return labels
