"""Trust label taxonomy for HireKit data pipeline.

Defines TrustLabel and VerdictLabel as str Enums so they are JSON-serializable
and can be used anywhere a plain string is accepted.
"""

from __future__ import annotations


from enum import Enum


class TrustLabel(str, Enum):
    """Five-level trust classification for every data field in a report.

    Labels flow downward: a field starts at its source's natural level and may
    be downgraded (e.g., to STALE) but never upgraded automatically.
    """

    VERIFIED = "verified"
    """Directly confirmed from an authoritative, traceable source (DART, GitHub API, etc.)."""

    DERIVED = "derived"
    """Calculated or normalised from one or more VERIFIED facts (e.g., growth rate, NPS churn)."""

    GENERATED = "generated"
    """Synthesised by rule-engine or LLM; interpretive, never a source-of-truth fact."""

    STALE = "stale"
    """Evidence is older than the 90-day freshness window; treat with caution."""

    UNKNOWN = "unknown"
    """Field is unresolved: evidence missing, too weak, or contradictory."""


class VerdictLabel(str, Enum):
    """Advisory-only application verdict.

    Every value must be understood as *advisory only* — it is a signal to help
    prioritise effort, not a guarantee of interview, offer, or long-term fit.
    """

    APPLY = "apply"
    """Advisory only. Strong match + high-confidence data suggests pursuing this opportunity."""

    HOLD = "hold"
    """Advisory only. Mixed match or insufficient data; gather more evidence first."""

    PASS_ = "pass"
    """Advisory only. Weak match + high-confidence data suggests low leverage or elevated risk.
    Not a moral judgment or permanent ban. (Named PASS_ because 'pass' is a Python keyword.)"""

    UNKNOWN = "unknown"
    """Verdict cannot be determined from available evidence."""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

_PUBLISHABLE: frozenset[TrustLabel] = frozenset(
    {TrustLabel.VERIFIED, TrustLabel.DERIVED, TrustLabel.GENERATED}
)


def is_publishable(label: TrustLabel | str) -> bool:
    """Return True if *label* is safe to display in a public demo.

    STALE and UNKNOWN data must not appear in public-facing outputs because
    they either carry freshness risk or have no verified backing.

    Args:
        label: A TrustLabel member or its string value.

    Returns:
        True for verified / derived / generated; False for stale / unknown.
    """
    try:
        resolved = TrustLabel(label)
    except ValueError:
        return False
    return resolved in _PUBLISHABLE


def should_downgrade(label: TrustLabel | str, staleness_days: int) -> TrustLabel:
    """Return the effective label after applying the staleness rule.

    If *staleness_days* is 90 or more and the current label is not already
    STALE or UNKNOWN, the label is downgraded to STALE.

    Args:
        label: Current TrustLabel member or its string value.
        staleness_days: Age of the underlying evidence in days.

    Returns:
        The original label, or TrustLabel.STALE when the freshness window is exceeded.
    """
    try:
        resolved = TrustLabel(label)
    except ValueError:
        return TrustLabel.UNKNOWN

    if staleness_days >= 90 and resolved not in (TrustLabel.STALE, TrustLabel.UNKNOWN):
        return TrustLabel.STALE
    return resolved
