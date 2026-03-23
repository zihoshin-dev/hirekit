"""Tests for hirekit.core.trust — TrustLabel, VerdictLabel, and helper functions."""

from __future__ import annotations

import pytest

from hirekit.core.trust import (
    TrustLabel,
    VerdictLabel,
    is_publishable,
    should_downgrade,
)
from hirekit.sources.base import SourceResult


class TestTrustLabelEnum:
    def test_all_values_are_valid_strings(self):
        expected = {"verified", "derived", "generated", "stale", "unknown"}
        assert {label.value for label in TrustLabel} == expected

    def test_members_are_strings(self):
        for label in TrustLabel:
            assert isinstance(label, str), f"{label!r} should be a str subclass"

    def test_invalid_label_is_rejected(self):
        with pytest.raises(ValueError):
            TrustLabel("hallucinated")

    def test_json_serialisable(self):
        import json

        payload = {"trust": TrustLabel.VERIFIED}
        dumped = json.dumps(payload)
        assert '"verified"' in dumped


class TestVerdictLabelEnum:
    def test_all_values_are_valid_strings(self):
        expected = {"apply", "hold", "pass", "unknown"}
        assert {label.value for label in VerdictLabel} == expected

    def test_members_are_strings(self):
        for label in VerdictLabel:
            assert isinstance(label, str)

    def test_pass_member_name_avoids_keyword_clash(self):
        assert VerdictLabel.PASS_.value == "pass"

    def test_invalid_label_is_rejected(self):
        with pytest.raises(ValueError):
            VerdictLabel("Go")  # old wording from trust_contract.py, not valid here


class TestIsPublishable:
    def test_verified_is_publishable(self):
        assert is_publishable(TrustLabel.VERIFIED) is True

    def test_derived_is_publishable(self):
        assert is_publishable(TrustLabel.DERIVED) is True

    def test_generated_is_publishable(self):
        assert is_publishable(TrustLabel.GENERATED) is True

    def test_stale_is_not_publishable(self):
        assert is_publishable(TrustLabel.STALE) is False

    def test_unknown_is_not_publishable(self):
        assert is_publishable(TrustLabel.UNKNOWN) is False

    def test_accepts_plain_string(self):
        assert is_publishable("verified") is True
        assert is_publishable("stale") is False

    def test_garbage_string_returns_false(self):
        assert is_publishable("hallucinated") is False


class TestShouldDowngrade:
    def test_downgrade_at_90_days(self):
        result = should_downgrade(TrustLabel.VERIFIED, staleness_days=90)
        assert result == TrustLabel.STALE

    def test_downgrade_at_91_days(self):
        result = should_downgrade(TrustLabel.VERIFIED, staleness_days=91)
        assert result == TrustLabel.STALE

    def test_no_downgrade_at_89_days(self):
        result = should_downgrade(TrustLabel.VERIFIED, staleness_days=89)
        assert result == TrustLabel.VERIFIED

    def test_stale_stays_stale(self):
        result = should_downgrade(TrustLabel.STALE, staleness_days=200)
        assert result == TrustLabel.STALE

    def test_unknown_stays_unknown(self):
        result = should_downgrade(TrustLabel.UNKNOWN, staleness_days=200)
        assert result == TrustLabel.UNKNOWN

    def test_accepts_plain_string(self):
        result = should_downgrade("derived", staleness_days=91)
        assert result == TrustLabel.STALE

    def test_garbage_string_returns_unknown(self):
        result = should_downgrade("hallucinated", staleness_days=91)
        assert result == TrustLabel.UNKNOWN


class TestSourceResultNewFields:
    def test_evidence_id_defaults_to_empty_or_auto(self):
        sr = SourceResult(source_name="dart", section="financials")
        # __post_init__ auto-generates evidence_id when blank, so it must be non-empty
        assert isinstance(sr.evidence_id, str)
        assert sr.evidence_id != ""

    def test_cross_validated_defaults_to_false(self):
        sr = SourceResult(source_name="dart", section="financials")
        assert sr.cross_validated is False

    def test_trust_label_field_exists_with_default(self):
        sr = SourceResult(source_name="dart", section="financials")
        assert hasattr(sr, "trust_label")
        # default is "verified" per base.py
        assert sr.trust_label == "verified"

    def test_cross_validated_can_be_set_true(self):
        sr = SourceResult(source_name="dart", section="financials", cross_validated=True)
        assert sr.cross_validated is True

    def test_evidence_id_can_be_set_explicitly(self):
        sr = SourceResult(source_name="dart", section="financials", evidence_id="dart:financials:abc123")
        assert sr.evidence_id == "dart:financials:abc123"
