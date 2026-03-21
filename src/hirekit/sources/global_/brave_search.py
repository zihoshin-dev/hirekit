"""Brave Search API data source — web + news search."""

from __future__ import annotations

import os
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

BRAVE_API_URL = "https://api.search.brave.com/res/v1"


@SourceRegistry.register
class BraveSearchSource(BaseSource):
    """Search company information via Brave Search API."""

    name = "brave_search"
    region = "global"
    sections = ["overview", "industry", "culture"]
    requires_api_key = True
    api_key_env_var = "BRAVE_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env_var))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env_var, "")
        if not api_key:
            return []

        results: list[SourceResult] = []
        lang = kwargs.get("lang", "ko")

        # Web search for company info
        web_results = self._search_web(company, api_key, lang)
        if web_results:
            raw = "\n\n".join(
                f"[{r['title']}]\n{r['description']}\n{r['url']}" for r in web_results
            )
            results.append(SourceResult(
                source_name=self.name,
                section="overview",
                data={"brave_web_results": web_results},
                url=f"https://search.brave.com/search?q={company}",
                raw=raw,
            ))

        # News search
        news_results = self._search_news(company, api_key, lang)
        if news_results:
            raw = "\n\n".join(
                f"[{n['title']}] ({n.get('age', '')})\n{n['description']}" for n in news_results
            )
            results.append(SourceResult(
                source_name=self.name,
                section="industry",
                data={"brave_news": news_results},
                raw=raw,
            ))

        return results

    def _search_web(self, company: str, api_key: str, lang: str) -> list[dict[str, str]]:
        """Brave Web Search."""
        queries = [
            f"{company} 회사 채용 문화 전략"
            if lang == "ko"
            else f"{company} company culture strategy hiring",
        ]
        all_results: list[dict[str, str]] = []

        for query in queries:
            try:
                resp = httpx.get(
                    f"{BRAVE_API_URL}/web/search",
                    params={"q": query, "count": 10, "search_lang": lang},
                    headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
                    timeout=10,
                )
                data = resp.json()
                for r in data.get("web", {}).get("results", [])[:10]:
                    all_results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": r.get("description", ""),
                    })
            except Exception:
                pass

        return all_results

    def _search_news(self, company: str, api_key: str, lang: str) -> list[dict[str, str]]:
        """Brave News Search."""
        query = f"{company} 최신 뉴스" if lang == "ko" else f"{company} latest news"
        try:
            resp = httpx.get(
                f"{BRAVE_API_URL}/news/search",
                params={"q": query, "count": 10, "search_lang": lang},
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                    "age": r.get("age", ""),
                    "source": r.get("meta_url", {}).get("hostname", ""),
                }
                for r in data.get("results", [])[:10]
            ]
        except Exception:
            return []
