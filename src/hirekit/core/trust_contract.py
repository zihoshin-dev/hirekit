from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Final, Literal, cast

TrustLabel = Literal["verified", "supporting", "derived", "generated", "stale", "unknown"]
VerdictLabel = Literal["Go", "Hold", "Pass"]
PublicationBoundary = Literal["public_demo", "internal_only", "private_user"]
SourceAuthority = Literal[
    "official",
    "company_operated",
    "credible_reporting",
    "secondary_research",
    "community",
    "generated",
]
FreshnessPolicy = Literal["job_posting", "core_company_fact", "supporting_signal"]

TRUST_LABELS: Final[tuple[TrustLabel, ...]] = (
    "verified",
    "supporting",
    "derived",
    "generated",
    "stale",
    "unknown",
)

TRUST_LABEL_MEANINGS: Final[dict[TrustLabel, str]] = {
    "verified": "A fact directly grounded in a traceable source with provenance.",
    "supporting": (
        "A claim backed by secondary or partial evidence that is useful to "
        "surface but not strong enough to treat as verified."
    ),
    "derived": "A calculation or normalization produced from verified facts.",
    "generated": "An interpretation synthesized by rules or an LLM and never a source-of-truth fact.",
    "stale": "A fact or interpretation whose underlying evidence is older than the freshness window.",
    "unknown": "A field that remains unresolved because evidence is missing, too weak, or contradictory.",
}

VERDICT_LABELS: Final[tuple[VerdictLabel, ...]] = ("Go", "Hold", "Pass")

VERDICT_GUIDANCE: Final[dict[VerdictLabel, str]] = {
    "Go": ("Advisory only. Strong current signal to pursue, not a guarantee of interview, offer, or long-term fit."),
    "Hold": (
        "Advisory only. Mixed or incomplete signal; gather more evidence before committing time or personal data."
    ),
    "Pass": (
        "Advisory only. Current evidence suggests low leverage or elevated risk, not a moral judgment or permanent ban."
    ),
}

PUBLICATION_BOUNDARIES: Final[tuple[PublicationBoundary, ...]] = (
    "public_demo",
    "internal_only",
    "private_user",
)

PUBLICATION_BOUNDARY_RULES: Final[dict[PublicationBoundary, str]] = {
    "public_demo": (
        "Safe for GitHub Pages or other public snapshots. Must exclude "
        "private user inputs and publish only governed fields."
    ),
    "internal_only": (
        "For local development, QA, and operator review. Must not be published to public docs or demo assets."
    ),
    "private_user": (
        "Contains user-provided or user-derived material such as resumes, "
        "JDs, applications, or personal notes. Never publish under public "
        "paths."
    ),
}

SOURCE_AUTHORITIES: Final[tuple[SourceAuthority, ...]] = (
    "official",
    "company_operated",
    "credible_reporting",
    "secondary_research",
    "community",
    "generated",
)

SOURCE_AUTHORITY_MEANINGS: Final[dict[SourceAuthority, str]] = {
    "official": "Primary public authority such as regulatory filings or government data.",
    "company_operated": ("Directly published by the company or its official engineering/recruiting surfaces."),
    "credible_reporting": (
        "Editorial reporting with traceable sourcing and stronger curation than generic search results."
    ),
    "secondary_research": (
        "Aggregated or indirect research signals that are useful but should not stand alone as verified truth."
    ),
    "community": "Forum, review, or community commentary that can inform context but needs corroboration.",
    "generated": "Synthesized output from rule engines or models, never a primary source.",
}

FRESHNESS_POLICIES: Final[tuple[FreshnessPolicy, ...]] = (
    "job_posting",
    "core_company_fact",
    "supporting_signal",
)

FRESHNESS_POLICY_WINDOWS: Final[dict[FreshnessPolicy, timedelta]] = {
    "job_posting": timedelta(hours=24),
    "core_company_fact": timedelta(days=7),
    "supporting_signal": timedelta(days=30),
}

SOURCE_NAME_AUTHORITIES: Final[dict[str, SourceAuthority]] = {
    "dart": "official",
    "fsc_corp": "official",
    "nts_biz": "official",
    "pension": "official",
    "military_service": "official",
    "company_website": "company_operated",
    "career_page": "company_operated",
    "career_pages": "company_operated",
    "tech_blog": "company_operated",
    "github": "company_operated",
    "ir_report": "company_operated",
    "credible_news": "credible_reporting",
    "google_news": "secondary_research",
    "naver_news": "secondary_research",
    "naver_search": "secondary_research",
    "brave_search": "secondary_research",
    "exa_search": "secondary_research",
    "medium_velog": "secondary_research",
    "linkedin_search": "secondary_research",
    "job_postings": "secondary_research",
    "community_review": "community",
}

_CORE_FACT_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "dart",
        "fsc_corp",
        "nts_biz",
        "pension",
        "military_service",
        "company_website",
        "career_page",
        "career_pages",
        "tech_blog",
        "github",
        "ir_report",
        "parent_company",
    }
)

_ROLE_POLICY_SOURCES: Final[frozenset[str]] = frozenset({"job_postings"})

_VERDICT_LOOKUP: Final[dict[str, VerdictLabel]] = {label.lower(): label for label in VERDICT_LABELS}


def is_valid_trust_label(label: str) -> bool:
    return label in TRUST_LABELS


def is_valid_verdict_label(label: str) -> bool:
    return label in VERDICT_LABELS


def is_valid_publication_boundary(boundary: str) -> bool:
    return boundary in PUBLICATION_BOUNDARIES


def is_valid_source_authority(authority: str) -> bool:
    return authority in SOURCE_AUTHORITIES


def is_valid_freshness_policy(policy: str) -> bool:
    return policy in FRESHNESS_POLICIES


def normalize_verdict_label(label: str) -> VerdictLabel:
    normalized = _VERDICT_LOOKUP.get(label.strip().lower())
    if normalized is None:
        raise ValueError(f"Unsupported verdict label: {label!r}")
    return normalized


def is_publication_safe(boundary: PublicationBoundary | str) -> bool:
    return boundary == "public_demo"


def default_source_authority(source_name: str) -> SourceAuthority:
    return SOURCE_NAME_AUTHORITIES.get(source_name, "secondary_research")


def default_freshness_policy(source_name: str, section: str) -> FreshnessPolicy:
    if source_name in _ROLE_POLICY_SOURCES:
        return "job_posting"
    if source_name in _CORE_FACT_SOURCES or section in {"overview", "financials", "business"}:
        return "core_company_fact"
    return "supporting_signal"


def freshness_window(policy: FreshnessPolicy | str) -> timedelta:
    resolved = require_freshness_policy(policy)
    return FRESHNESS_POLICY_WINDOWS[resolved]


def is_timestamp_stale(
    collected_at: str,
    policy: FreshnessPolicy | str,
    *,
    now: datetime | None = None,
) -> bool:
    resolved_now = now or datetime.now(UTC)
    collected = datetime.fromisoformat(collected_at)
    return resolved_now - collected > freshness_window(policy)


def require_trust_label(label: str) -> TrustLabel:
    if not is_valid_trust_label(label):
        raise ValueError(f"Unsupported trust label: {label!r}")
    return cast(TrustLabel, label)


def require_publication_boundary(boundary: str) -> PublicationBoundary:
    if not is_valid_publication_boundary(boundary):
        raise ValueError(f"Unsupported publication boundary: {boundary!r}")
    return cast(PublicationBoundary, boundary)


def require_source_authority(authority: str) -> SourceAuthority:
    if not is_valid_source_authority(authority):
        raise ValueError(f"Unsupported source authority: {authority!r}")
    return cast(SourceAuthority, authority)


def require_freshness_policy(policy: str) -> FreshnessPolicy:
    if not is_valid_freshness_policy(policy):
        raise ValueError(f"Unsupported freshness policy: {policy!r}")
    return cast(FreshnessPolicy, policy)
