"""Base LLM protocol — provider-agnostic interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    text: str
    structured: dict[str, Any] | None = None
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class BaseLLM(ABC):
    """LLM provider abstraction.

    Implementations: OpenAIAdapter, AnthropicAdapter, OllamaAdapter, NoLLM.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM backend is configured and reachable."""
        ...


class NoLLM(BaseLLM):
    """Fallback when no LLM is configured. Returns empty responses.

    The template engine handles report generation without LLM assistance.
    """

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        return LLMResponse(text="", model="none")

    def is_available(self) -> bool:
        return False
