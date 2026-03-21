"""Google Gemini LLM adapter (free tier available)."""

from __future__ import annotations

import os
from typing import Any

from hirekit.llm.base import BaseLLM, LLMResponse

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiAdapter(BaseLLM):
    """Google Gemini API adapter.

    Free tier: Gemini 2.5 Flash-Lite (15 RPM, 1000 RPD).
    Get a free API key at: https://aistudio.google.com/apikey
    """

    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        self.model = model

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        import httpx

        api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
        if not api_key:
            return LLMResponse(text="", model=self.model)

        contents = []
        if system:
            contents.append({
                "role": "user",
                "parts": [{"text": f"System instruction: {system}"}],
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Understood. I will follow these instructions."}],
            })
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}],
        })

        try:
            resp = httpx.post(
                f"{GEMINI_API_URL}/models/{self.model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                    },
                },
                timeout=60,
            )
            data = resp.json()

            # Extract text from response
            candidates = data.get("candidates", [])
            if not candidates:
                return LLMResponse(text="", model=self.model)

            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

            # Usage metadata
            usage_meta = data.get("usageMetadata", {})

            return LLMResponse(
                text=text,
                model=self.model,
                usage={
                    "input_tokens": usage_meta.get("promptTokenCount", 0),
                    "output_tokens": usage_meta.get("candidatesTokenCount", 0),
                },
            )
        except Exception:
            return LLMResponse(text="", model=self.model)

    def is_available(self) -> bool:
        return bool(
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        )
