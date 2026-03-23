"""HireKit 계층형 예외 체계."""

from __future__ import annotations


class HireKitError(Exception):
    """Base exception for all HireKit errors."""


class SourceError(HireKitError):
    """데이터 소스 수집 오류."""

    def __init__(self, source_name: str, message: str) -> None:
        self.source_name = source_name
        super().__init__(f"[{source_name}] {message}")


class NetworkError(SourceError):
    """네트워크 연결/타임아웃 오류 — 재시도 가능."""

    retryable = True


class ParseError(SourceError):
    """응답 파싱 오류 — 재시도 불가, 소스 구조 변경."""

    retryable = False


class RateLimitError(SourceError):
    """API rate limit — 지수 백오프 재시도."""

    retryable = True

    def __init__(self, source_name: str, retry_after: int = 60) -> None:
        self.retry_after = retry_after
        super().__init__(source_name, f"Rate limited, retry after {retry_after}s")


class LLMError(HireKitError):
    """LLM 호출 오류."""


class LLMRefusalError(LLMError):
    """LLM이 응답을 거부 — trust label 'unknown' 전환."""


class LLMParseError(LLMError):
    """LLM 응답 파싱 실패 — retry 가능."""

    retryable = True


class ValidationError(HireKitError):
    """데이터 검증 오류."""
