from __future__ import annotations

import pytest

from hirekit.core.trust_contract import (
    PUBLICATION_BOUNDARIES,
    PUBLICATION_BOUNDARY_RULES,
    TRUST_LABELS,
    TRUST_LABEL_MEANINGS,
    VERDICT_GUIDANCE,
    VERDICT_LABELS,
    is_publication_safe,
    is_valid_publication_boundary,
    is_valid_trust_label,
    is_valid_verdict_label,
    normalize_verdict_label,
    require_publication_boundary,
    require_trust_label,
)


class TestTrustLabels:
    def test_trust_labels_match_contract(self):
        assert TRUST_LABELS == (
            "verified",
            "derived",
            "generated",
            "stale",
            "unknown",
        )

    def test_every_trust_label_has_meaning(self):
        assert set(TRUST_LABELS) == set(TRUST_LABEL_MEANINGS)

    def test_valid_and_invalid_trust_labels(self):
        assert is_valid_trust_label("verified") is True
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
