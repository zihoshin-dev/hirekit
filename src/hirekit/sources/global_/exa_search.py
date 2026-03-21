"""Exa (formerly Metaphor) AI search — semantic search for company research."""

from __future__ import annotations

import os
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

EXA_API_URL = "https://api.exa.ai"


@SourceRegistry.register
class ExaSearchSource(BaseSource):
    """Semantic search for company intelligence via Exa API."""

    name = "exa_search"
    region = "global"
    sections = ["overview", "tech", "culture", "strategy"]
    requires_api_key = True
    api_key_env_var = "EXA_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env_var))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env_var, "")
        if not api_key:
            return []

        results: list[SourceResult] = []

        # Multiple semantic queries for comprehensive coverage
        queries = [
            f"{company} company culture engineering team work environment",
            f"{company} business strategy growth AI investment 2025 2026",
            f"{company} hiring jobs career employee reviews",
            f"{company} tech stack engineering blog open source",
        ]

        for query in queries:
            section = self._query_to_section(query)
            search_results = self._search(query, api_key)
            if search_results:
                raw = "\n\n".join(
                    f"[{r['title']}] (score: {r.get('score', 'N/A')})\n{r['text'][:300]}"
                    for r in search_results
                )
                results.append(SourceResult(
                    source_name=self.name,
                    section=section,
                    data={f"exa_{section}": search_results},
                    url=f"https://exa.ai/search?q={query}",
                    raw=raw,
                ))

        return results

    def _search(self, query: str, api_key: str) -> list[dict[str, Any]]:
        """Run Exa semantic search with content extraction."""
        try:
            resp = httpx.post(
                f"{EXA_API_URL}/search",
                json={
                    "query": query,
                    "num_results": 5,
                    "use_autoprompt": True,
                    "type": "auto",
                    "contents": {
                        "text": {"max_characters": 500},
                    },
                },
                headers={"x-api-key": api_key, "Content-Type": "application/json"},
                timeout=15,
            )
            data = resp.json()
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "text": r.get("text", ""),
                    "score": r.get("score", 0),
                    "published_date": r.get("publishedDate", ""),
                }
                for r in data.get("results", [])
            ]
        except Exception:
            return []

    @staticmethod
    def _query_to_section(query: str) -> str:
        """Map query keywords to report section."""
        q = query.lower()
        if "culture" in q or "hiring" in q or "employee" in q:
            return "culture"
        if "tech" in q or "engineering" in q or "open source" in q:
            return "tech"
        if "strategy" in q or "growth" in q or "investment" in q:
            return "strategy"
        return "overview"
