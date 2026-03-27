from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from hirekit.core.trust_contract import (
    FRESHNESS_POLICIES,
    FRESHNESS_POLICY_WINDOWS,
    PUBLICATION_BOUNDARIES,
    PUBLICATION_BOUNDARY_RULES,
    SOURCE_AUTHORITIES,
    SOURCE_AUTHORITY_MEANINGS,
    TRUST_LABEL_MEANINGS,
    TRUST_LABELS,
    VERDICT_GUIDANCE,
    VERDICT_LABELS,
    default_freshness_policy,
    default_source_authority,
    freshness_window,
    is_publication_safe,
    is_timestamp_stale,
    is_valid_freshness_policy,
    is_valid_publication_boundary,
    is_valid_source_authority,
    is_valid_trust_label,
    is_valid_verdict_label,
    normalize_verdict_label,
    require_freshness_policy,
    require_publication_boundary,
    require_source_authority,
    require_trust_label,
)


class TestTrustLabels:
    def test_trust_labels_match_contract(self):
        assert TRUST_LABELS == (
            "verified",
            "supporting",
            "derived",
            "generated",
            "stale",
            "unknown",
        )

    def test_every_trust_label_has_meaning(self):
        assert set(TRUST_LABELS) == set(TRUST_LABEL_MEANINGS)

    def test_valid_and_invalid_trust_labels(self):
        assert is_valid_trust_label("verified") is True
        assert is_valid_trust_label("supporting") is True
        assert is_valid_trust_label("hallucinated") is False

    def test_require_trust_label_rejects_unknown_values(self):
        with pytest.raises(ValueError, match="Unsupported trust label"):
            require_trust_label("hallucinated")


class TestVerdictLabels:
    def test_verdict_labels_preserve_existing_wording(self):
        assert VERDICT_LABELS == ("Go", "Hold", "Pass")

    def test_every_verdict_is_explicitly_advisory(self):
        for label in VERDICT_LABELS:
            assert "Advisory only" in VERDICT_GUIDANCE[label]

    def test_valid_and_invalid_verdict_labels(self):
        assert is_valid_verdict_label("Go") is True
        assert is_valid_verdict_label("Apply") is False

    def test_normalize_verdict_label_is_case_insensitive(self):
        assert normalize_verdict_label("go") == "Go"
        assert normalize_verdict_label(" HOLD ") == "Hold"
        assert normalize_verdict_label("Pass") == "Pass"

    def test_normalize_verdict_label_rejects_unknown_values(self):
        with pytest.raises(ValueError, match="Unsupported verdict label"):
            normalize_verdict_label("Apply")


class TestPublicationBoundaries:
    def test_publication_boundaries_match_contract(self):
        assert PUBLICATION_BOUNDARIES == (
            "public_demo",
            "internal_only",
            "private_user",
        )

    def test_every_publication_boundary_has_rule_text(self):
        assert set(PUBLICATION_BOUNDARIES) == set(PUBLICATION_BOUNDARY_RULES)

    def test_only_public_demo_is_publication_safe(self):
        assert is_publication_safe("public_demo") is True
        assert is_publication_safe("internal_only") is False
        assert is_publication_safe("private_user") is False

    def test_valid_and_invalid_publication_boundaries(self):
        assert is_valid_publication_boundary("private_user") is True
        assert is_valid_publication_boundary("github_pages") is False

    def test_require_publication_boundary_rejects_unknown_values(self):
        with pytest.raises(ValueError, match="Unsupported publication boundary"):
            require_publication_boundary("github_pages")


class TestSourceAuthority:
    def test_source_authorities_match_contract(self):
        assert SOURCE_AUTHORITIES == (
            "official",
            "company_operated",
            "credible_reporting",
            "secondary_research",
            "community",
            "generated",
        )

    def test_every_source_authority_has_meaning(self):
        assert set(SOURCE_AUTHORITIES) == set(SOURCE_AUTHORITY_MEANINGS)

    def test_valid_and_invalid_source_authorities(self):
        assert is_valid_source_authority("official") is True
        assert is_valid_source_authority("rumor") is False

    def test_default_source_authority_maps_known_and_unknown_sources(self):
        assert default_source_authority("dart") == "official"
        assert default_source_authority("github") == "company_operated"
        assert default_source_authority("community_review") == "community"
        assert default_source_authority("unknown_source") == "secondary_research"

    def test_require_source_authority_rejects_unknown_values(self):
        with pytest.raises(ValueError, match="Unsupported source authority"):
            require_source_authority("rumor")


class TestFreshnessPolicies:
    def test_freshness_policies_match_contract(self):
        assert FRESHNESS_POLICIES == (
            "job_posting",
            "core_company_fact",
            "supporting_signal",
        )

    def test_valid_and_invalid_freshness_policies(self):
        assert is_valid_freshness_policy("job_posting") is True
        assert is_valid_freshness_policy("forever") is False

    def test_require_freshness_policy_rejects_unknown_values(self):
        with pytest.raises(ValueError, match="Unsupported freshness policy"):
            require_freshness_policy("forever")

    def test_freshness_windows_match_sla(self):
        assert freshness_window("job_posting") == timedelta(hours=24)
        assert freshness_window("core_company_fact") == timedelta(days=7)
        assert freshness_window("supporting_signal") == timedelta(days=30)
        assert freshness_window("job_posting") == FRESHNESS_POLICY_WINDOWS["job_posting"]

    def test_default_freshness_policy_uses_source_and_section(self):
        assert default_freshness_policy("job_postings", "role") == "job_posting"
        assert default_freshness_policy("dart", "overview") == "core_company_fact"
        assert default_freshness_policy("community_review", "culture") == "supporting_signal"

    def test_job_postings_go_stale_after_24_hours(self):
        assert (
            is_timestamp_stale(
                "2026-03-25T23:59:59+00:00",
                "job_posting",
                now=datetime(2026, 3, 27, 0, 0, 0, tzinfo=UTC),
            )
            is True
        )

    def test_core_company_facts_stay_fresh_within_seven_days(self):
        assert (
            is_timestamp_stale(
                "2026-03-21T00:00:01+00:00",
                "core_company_fact",
                now=datetime(2026, 3, 27, 0, 0, 0, tzinfo=UTC),
            )
            is False
        )

    def test_supporting_signals_turn_stale_after_thirty_days(self):
        assert (
            is_timestamp_stale(
                "2026-02-20T00:00:00+00:00",
                "supporting_signal",
                now=datetime(2026, 3, 27, 0, 0, 0, tzinfo=UTC),
            )
            is True
        )
