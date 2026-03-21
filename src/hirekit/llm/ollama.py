"""Ollama local LLM adapter (completely free, no API key needed)."""

from __future__ import annotations

from typing import Any

import httpx

from hirekit.llm.base import BaseLLM, LLMResponse


class OllamaAdapter(BaseLLM):
    """Ollama local model adapter.

    Runs models locally via Ollama (https://ollama.com).
    No API key, no internet, no cost. Privacy guaranteed.

    Install: `curl -fsSL https://ollama.com/install.sh | sh`
    Pull model: `ollama pull llama3.1`
    """

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
                timeout=120,  # local models can be slow
            )
            data = resp.json()

            return LLMResponse(
                text=data.get("message", {}).get("content", ""),
                model=self.model,
                usage={
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0),
                },
            )
        except Exception:
            return LLMResponse(text="", model=self.model)

    def is_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            resp = httpx.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False
