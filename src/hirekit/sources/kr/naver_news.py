"""Naver News search data source."""

from __future__ import annotations

import os
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult


@SourceRegistry.register
class NaverNewsSource(BaseSource):
    """Collect recent news articles about a company via Naver Search API."""

    name = "naver_news"
    region = "kr"
    sections = ["overview", "strategy", "industry"]
    requires_api_key = True
    api_key_env_var = "NAVER_CLIENT_ID"

    def is_available(self) -> bool:
        return bool(
            os.environ.get("NAVER_CLIENT_ID") and os.environ.get("NAVER_CLIENT_SECRET")
        )

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        client_id = os.environ.get("NAVER_CLIENT_ID", "")
        client_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            return []

        results: list[SourceResult] = []

        try:
            resp = httpx.get(
                "https://openapi.naver.com/v1/search/news.json",
                params={
                    "query": f"{company} 채용 OR 전략 OR AI OR 실적",
                    "display": 20,
                    "sort": "date",
                },
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret,
                },
                timeout=10,
            )
            data = resp.json()

            articles = data.get("items", [])
            if articles:
                news_data = [
                    {
                        "title": self._strip_html(a.get("title", "")),
                        "description": self._strip_html(a.get("description", "")),
                        "link": a.get("originallink", a.get("link", "")),
                        "pub_date": a.get("pubDate", ""),
                    }
                    for a in articles
                ]

                raw_text = "\n\n".join(
                    f"[{n['title']}] {n['description']}" for n in news_data
                )

                results.append(SourceResult(
                    source_name=self.name,
                    section="overview",
                    data={"recent_news": news_data},
                    url=f"https://search.naver.com/search.naver?query={company}",
                    raw=raw_text,
                ))
        except Exception:
            pass

        return results

    @staticmethod
    def _strip_html(text: str) -> str:
        """Remove HTML tags from text."""
        import re
        return re.sub(r"<[^>]+>", "", text)
