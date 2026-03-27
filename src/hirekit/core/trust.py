from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

from hirekit.core.trust_contract import FreshnessPolicy, freshness_window


class TrustLabel(StrEnum):
    VERIFIED = "verified"
    SUPPORTING = "supporting"
    DERIVED = "derived"
    GENERATED = "generated"
    STALE = "stale"
    UNKNOWN = "unknown"


class VerdictLabel(StrEnum):
    APPLY = "apply"
    HOLD = "hold"
    PASS_ = "pass"
    UNKNOWN = "unknown"


_PUBLISHABLE: frozenset[TrustLabel] = frozenset(
    {TrustLabel.VERIFIED, TrustLabel.SUPPORTING, TrustLabel.DERIVED, TrustLabel.GENERATED}
)


def is_publishable(label: TrustLabel | str) -> bool:
    try:
        resolved = TrustLabel(label)
    except ValueError:
        return False
    return resolved in _PUBLISHABLE


def should_downgrade(
    label: TrustLabel | str,
    staleness_days: int,
    freshness_policy: FreshnessPolicy | str = "core_company_fact",
) -> TrustLabel:
    try:
        resolved = TrustLabel(label)
    except ValueError:
        return TrustLabel.UNKNOWN

    threshold_days = max(int(freshness_window(freshness_policy) / timedelta(days=1)), 1)
    if staleness_days >= threshold_days and resolved not in (TrustLabel.STALE, TrustLabel.UNKNOWN):
        return TrustLabel.STALE
    return resolved
