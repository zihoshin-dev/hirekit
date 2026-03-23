from __future__ import annotations

from typing import Final, Literal, cast

TrustLabel = Literal["verified", "derived", "generated", "stale", "unknown"]
VerdictLabel = Literal["Go", "Hold", "Pass"]
PublicationBoundary = Literal["public_demo", "internal_only", "private_user"]

TRUST_LABELS: Final[tuple[TrustLabel, ...]] = (
    "verified",
    "derived",
    "generated",
    "stale",
    "unknown",
)

TRUST_LABEL_MEANINGS: Final[dict[TrustLabel, str]] = {
    "verified": "A fact directly grounded in a traceable source with provenance.",
    "derived": "A calculation or normalization produced from verified facts.",
    "generated": "An interpretation synthesized by rules or an LLM and never a source-of-truth fact.",
    "stale": "A fact or interpretation whose underlying evidence is older than the freshness window.",
    "unknown": "A field that remains unresolved because evidence is missing, too weak, or contradictory.",
}

VERDICT_LABELS: Final[tuple[VerdictLabel, ...]] = ("Go", "Hold", "Pass")

VERDICT_GUIDANCE: Final[dict[VerdictLabel, str]] = {
    "Go": "Advisory only. Strong current signal to pursue, not a guarantee of interview, offer, or long-term fit.",
    "Hold": "Advisory only. Mixed or incomplete signal; gather more evidence before committing time or personal data.",
    "Pass": "Advisory only. Current evidence suggests low leverage or elevated risk, not a moral judgment or permanent ban.",
}

PUBLICATION_BOUNDARIES: Final[tuple[PublicationBoundary, ...]] = (
    "public_demo",
    "internal_only",
    "private_user",
)

PUBLICATION_BOUNDARY_RULES: Final[dict[PublicationBoundary, str]] = {
    "public_demo": "Safe for GitHub Pages or other public snapshots. Must exclude private user inputs and publish only governed fields.",
    "internal_only": "For local development, QA, and operator review. Must not be published to public docs or demo assets.",
    "private_user": "Contains user-provided or user-derived material such as resumes, JDs, applications, or personal notes. Never publish under public paths.",
}

_VERDICT_LOOKUP: Final[dict[str, VerdictLabel]] = {
    label.lower(): label for label in VERDICT_LABELS
}


def is_valid_trust_label(label: str) -> bool:
    return label in TRUST_LABELS


def is_valid_verdict_label(label: str) -> bool:
    return label in VERDICT_LABELS


def normalize_verdict_label(label: str) -> VerdictLabel:
    normalized = _VERDICT_LOOKUP.get(label.strip().lower())
    if normalized is None:
        raise ValueError(f"Unsupported verdict label: {label!r}")
    return normalized


def is_valid_publication_boundary(boundary: str) -> bool:
    return boundary in PUBLICATION_BOUNDARIES


def is_publication_safe(boundary: PublicationBoundary | str) -> bool:
    return boundary == "public_demo"


def require_trust_label(label: str) -> TrustLabel:
    if not is_valid_trust_label(label):
        raise ValueError(f"Unsupported trust label: {label!r}")
    return cast(TrustLabel, label)


def require_publication_boundary(boundary: str) -> PublicationBoundary:
    if not is_valid_publication_boundary(boundary):
        raise ValueError(f"Unsupported publication boundary: {boundary!r}")
    return cast(PublicationBoundary, boundary)
