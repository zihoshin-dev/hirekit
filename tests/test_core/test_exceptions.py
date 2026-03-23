"""Tests for hirekit.core.exceptions — 계층형 예외 체계."""

from __future__ import annotations

import pytest

from hirekit.core.exceptions import (
    HireKitError,
    LLMError,
    LLMParseError,
    LLMRefusalError,
    NetworkError,
    ParseError,
    RateLimitError,
    SourceError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_source_error_is_hirekit_error(self):
        err = SourceError("dart", "failed")
        assert isinstance(err, HireKitError)

    def test_network_error_is_source_error(self):
        err = NetworkError("naver", "timeout")
        assert isinstance(err, SourceError)
        assert isinstance(err, HireKitError)

    def test_parse_error_is_source_error(self):
        err = ParseError("github", "unexpected html")
        assert isinstance(err, SourceError)

    def test_rate_limit_error_is_source_error(self):
        err = RateLimitError("brave")
        assert isinstance(err, SourceError)

    def test_llm_error_is_hirekit_error(self):
        err = LLMError("llm failed")
        assert isinstance(err, HireKitError)

    def test_llm_refusal_error_is_llm_error(self):
        err = LLMRefusalError("refusal")
        assert isinstance(err, LLMError)

    def test_llm_parse_error_is_llm_error(self):
        err = LLMParseError("parse failed")
        assert isinstance(err, LLMError)

    def test_validation_error_is_hirekit_error(self):
        err = ValidationError("bad data")
        assert isinstance(err, HireKitError)


class TestRetryableAttribute:
    def test_network_error_is_retryable(self):
        assert NetworkError.retryable is True

    def test_parse_error_is_not_retryable(self):
        assert ParseError.retryable is False

    def test_rate_limit_error_is_retryable(self):
        assert RateLimitError.retryable is True

    def test_llm_parse_error_is_retryable(self):
        assert LLMParseError.retryable is True


class TestSourceErrorMessage:
    def test_message_includes_source_name(self):
        err = SourceError("dart", "connection refused")
        assert "[dart]" in str(err)
        assert "connection refused" in str(err)

    def test_source_name_attribute(self):
        err = NetworkError("naver_news", "timeout after 30s")
        assert err.source_name == "naver_news"


class TestRateLimitError:
    def test_default_retry_after(self):
        err = RateLimitError("brave")
        assert err.retry_after == 60

    def test_custom_retry_after(self):
        err = RateLimitError("exa", retry_after=120)
        assert err.retry_after == 120

    def test_message_includes_retry_after(self):
        err = RateLimitError("exa", retry_after=30)
        assert "30s" in str(err)

    def test_is_retryable(self):
        err = RateLimitError("exa")
        assert err.retryable is True


class TestExceptionsAreCatchable:
    def test_catch_as_hirekit_error(self):
        with pytest.raises(HireKitError):
            raise NetworkError("src", "err")

    def test_catch_as_source_error(self):
        with pytest.raises(SourceError):
            raise ParseError("src", "bad html")

    def test_catch_as_llm_error(self):
        with pytest.raises(LLMError):
            raise LLMRefusalError("refused content")
