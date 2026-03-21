"""OpenAI LLM adapter."""

from __future__ import annotations

import os
from typing import Any

from hirekit.llm.base import BaseLLM, LLMResponse


class OpenAIAdapter(BaseLLM):
    """OpenAI API adapter (GPT-4o-mini, GPT-4o, etc.)."""

    def __init__(self, model: str = "gpt-4o-mini"):
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
            from openai import OpenAI
        except ImportError:
            return LLMResponse(text="", model=self.model)

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            return LLMResponse(
                text=choice.message.content or "",
                model=response.model,
                usage={
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
        except Exception:
            return LLMResponse(text="", model=self.model)

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))
