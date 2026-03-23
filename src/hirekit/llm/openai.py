"""OpenAI LLM adapter."""

from __future__ import annotations

import json
import os
from typing import Any

from hirekit.llm.base import BaseLLM, LLMResponse


class OpenAIAdapter(BaseLLM):
    """OpenAI API adapter (GPT-4o-mini, GPT-4o, etc.)."""

    _client: Any = None  # class-level singleton cache

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    @staticmethod
    def _build_response_format(json_schema: dict[str, Any]) -> dict[str, Any]:
        if "schema" in json_schema:
            schema = json_schema["schema"]
            name = json_schema.get("name", "structured_output")
            strict = json_schema.get("strict", True)
        else:
            schema = json_schema
            name = json_schema.get("name", "structured_output")
            strict = True
        return {
            "type": "json_schema",
            "json_schema": {
                "name": name,
                "strict": strict,
                "schema": schema,
            },
        }

    @staticmethod
    def _parse_structured_content(content: Any) -> dict[str, Any] | None:
        if not content:
            return None
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                return None
            return parsed if isinstance(parsed, dict) else None
        return None

    @classmethod
    def _get_client(cls) -> Any:
        """Return cached client, creating it on first call."""
        if cls._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                return None
            cls._client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return cls._client

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        if client is None:
            return LLMResponse(text="", model=self.model)

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
        if json_schema:
            kwargs["response_format"] = self._build_response_format(json_schema)

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            refusal = bool(getattr(choice.message, "refusal", None))
            content = choice.message.content or ""
            return LLMResponse(
                text="" if refusal else content,
                structured=self._parse_structured_content(content) if json_schema and not refusal else None,
                refusal=refusal,
                model=response.model,
                usage={
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
        except Exception as exc:
            # Sanitize error: never surface raw exception text (may contain API key)
            _safe_type = type(exc).__name__
            import logging as _logging
            _logging.getLogger(__name__).debug("OpenAI API error (%s)", _safe_type, exc_info=True)
            return LLMResponse(text="", model=self.model)

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))
