"""Anthropic Claude LLM adapter."""

from __future__ import annotations

import os
from typing import Any

from hirekit.llm.base import BaseLLM, LLMResponse


class AnthropicAdapter(BaseLLM):
    """Anthropic Claude API adapter (claude-sonnet, claude-haiku, etc.)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        try:
            import anthropic
        except ImportError:
            return LLMResponse(text="", model=self.model)

        client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        try:
            response = client.messages.create(**kwargs)
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text

            return LLMResponse(
                text=text,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )
        except Exception as exc:
            # Sanitize error: never surface raw exception text (may contain API key)
            _safe_type = type(exc).__name__
            import logging as _logging
            _logging.getLogger(__name__).debug("Anthropic API error (%s)", _safe_type, exc_info=True)
            return LLMResponse(text="", model=self.model)

    def is_available(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
