from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

from hirekit.core.trust_contract import is_valid_trust_label
from hirekit.sources.base import SourceResult

_REQUIRED_DIMENSIONS = [
    "overview",
    "financials",
    "culture",
    "tech",
    "role",
]

_THRESHOLD_INSUFFICIENT = 0.4
_THRESHOLD_WARN = 0.7

_INTELLIGENCE_FIELDS: Final[dict[str, str]] = {
    "leadership": "leadership_evidence",
    "org_health": "org_health_evidence",
    "strategic_direction": "strategic_direction_evidence",
}

_HIGH_TRUST_AUTHORITIES: Final[frozenset[str]] = frozenset({"official", "company_operated", "credible_reporting"})
_VERIFIED_AUTHORITIES: Final[frozenset[str]] = frozenset({"official", "company_operated"})
_SUPPORTING_LABELS: Final[frozenset[str]] = frozenset({"supporting", "derived", "generated", "stale"})


def _default_intelligence_bucket() -> dict[str, Any]:
    return {
        "state": "unknown",
        "verified_facts": [],
        "supporting_signals": [],
        "contradictions": [],
        "unknowns": [],
    }


def _default_intelligence_layer() -> dict[str, dict[str, Any]]:
    return {category: _default_intelligence_bucket() for category in _INTELLIGENCE_FIELDS}


@dataclass
class ReviewResult:
    completeness_score: float
    missing_dimensions: list[str] = field(default_factory=list)
    low_confidence_warnings: list[str] = field(default_factory=list)
    recommendation: str = "proceed"
    intelligence_layer: dict[str, dict[str, Any]] = field(default_factory=_default_intelligence_layer)


class DataReviewer:
    def review(self, source_results: list[SourceResult]) -> ReviewResult:
        covered: dict[str, list[float]] = {}
        for result in source_results:
            if result.raw:
                covered.setdefault(result.section, []).append(result.confidence)

        missing = [dim for dim in _REQUIRED_DIMENSIONS if dim not in covered]
        completeness = 1.0 - len(missing) / len(_REQUIRED_DIMENSIONS)

        low_confidence_warnings: list[str] = []
        for dim, confidences in covered.items():
            avg = sum(confidences) / len(confidences)
            if avg < 0.5:
                low_confidence_warnings.append(f"{dim} (avg confidence: {avg:.2f})")

        intelligence_layer = self._build_intelligence_layer(source_results)
        low_confidence_warnings.extend(self._intelligence_warnings(intelligence_layer))

        if completeness < _THRESHOLD_INSUFFICIENT:
            recommendation = "insufficient"
        elif completeness < _THRESHOLD_WARN or low_confidence_warnings:
            recommendation = "warn"
        else:
            recommendation = "proceed"

        return ReviewResult(
            completeness_score=round(completeness, 4),
            missing_dimensions=missing,
            low_confidence_warnings=low_confidence_warnings,
            recommendation=recommendation,
            intelligence_layer=intelligence_layer,
        )

    def _build_intelligence_layer(self, source_results: list[SourceResult]) -> dict[str, dict[str, Any]]:
        layer = _default_intelligence_layer()
        for category, field_name in _INTELLIGENCE_FIELDS.items():
            signals = self._extract_signals(source_results, field_name)
            layer[category] = self._build_bucket(signals)
        return layer

    def _extract_signals(self, source_results: list[SourceResult], field_name: str) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []

        for result in source_results:
            raw_items = result.data.get(field_name, [])
            if not isinstance(raw_items, list):
                continue

            for index, item in enumerate(raw_items, start=1):
                if not isinstance(item, dict):
                    continue

                summary = str(
                    item.get("summary") or item.get("title") or item.get("signal") or item.get("value") or ""
                ).strip()
                if not summary:
                    continue

                authority = str(item.get("source_authority") or result.source_authority or "secondary_research")
                trust_label = self._normalize_trust_label(
                    str(item.get("trust_label") or result.trust_label or "unknown"),
                    authority,
                    result.is_stale,
                )

                signals.append(
                    {
                        "claim_key": str(item.get("claim_key") or field_name),
                        "summary": summary,
                        "status": str(item.get("status") or "unknown"),
                        "source_name": str(item.get("source_name") or result.source_name),
                        "source_authority": authority,
                        "trust_label": trust_label,
                        "evidence_id": str(item.get("evidence_id") or f"{result.evidence_id}:{field_name}:{index}"),
                        "url": str(item.get("url") or result.url),
                        "confidence": float(item.get("confidence", result.confidence)),
                        "collected_at": str(item.get("collected_at") or result.collected_at),
                    }
                )

        return signals

    def _build_bucket(self, signals: list[dict[str, Any]]) -> dict[str, Any]:
        bucket = _default_intelligence_bucket()
        if not signals:
            bucket["unknowns"] = ["no_evidence_collected"]
            return bucket

        verified_facts = [signal for signal in signals if signal["trust_label"] == "verified"]
        supporting_signals = [signal for signal in signals if signal["trust_label"] in _SUPPORTING_LABELS]
        contradictions = self._find_contradictions(signals)

        bucket["verified_facts"] = verified_facts
        bucket["supporting_signals"] = supporting_signals
        bucket["contradictions"] = contradictions

        has_high_trust_backbone = any(signal["source_authority"] in _HIGH_TRUST_AUTHORITIES for signal in signals)
        community_only = all(signal["source_authority"] == "community" for signal in signals)

        if community_only:
            bucket["unknowns"].append("official_or_credible_backbone_missing")
        elif not has_high_trust_backbone:
            bucket["unknowns"].append("high_trust_backbone_missing")

        if community_only:
            bucket["state"] = "unknown"
        elif contradictions:
            bucket["state"] = "contradictory"
        elif verified_facts:
            bucket["state"] = "verified"
        elif supporting_signals:
            bucket["state"] = "supporting"
        else:
            bucket["state"] = "unknown"

        return bucket

    def _find_contradictions(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}

        for signal in signals:
            status = str(signal.get("status") or "unknown").strip().lower()
            if not status or status == "unknown":
                continue

            claim_key = str(signal.get("claim_key") or "unknown")
            grouped.setdefault(claim_key, {}).setdefault(status, []).append(signal)

        contradictions: list[dict[str, Any]] = []
        for claim_key, by_status in grouped.items():
            if len(by_status) <= 1:
                continue

            contradictions.append(
                {
                    "claim_key": claim_key,
                    "statuses": sorted(by_status),
                    "signals": [signal for status in sorted(by_status) for signal in by_status[status]],
                }
            )

        return contradictions

    def _intelligence_warnings(self, intelligence_layer: dict[str, dict[str, Any]]) -> list[str]:
        warnings: list[str] = []
        for category, bucket in intelligence_layer.items():
            state = bucket.get("state", "unknown")
            if state == "contradictory":
                warnings.append(f"{category} (contradictory evidence)")
            elif state == "unknown" and bucket.get("supporting_signals"):
                warnings.append(f"{category} (supporting-only evidence)")
        return warnings

    @staticmethod
    def _normalize_trust_label(label: str, authority: str, is_stale: bool) -> str:
        if is_stale:
            return "stale"

        normalized = label if is_valid_trust_label(label) else "unknown"

        if authority == "community" and normalized not in {"unknown", "stale"}:
            return "supporting"

        if normalized == "verified" and authority not in _VERIFIED_AUTHORITIES:
            return "supporting"

        return normalized
