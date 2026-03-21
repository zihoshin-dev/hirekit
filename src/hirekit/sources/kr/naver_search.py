"""Naver Search API — blog, cafe, webkr (web documents) for Korean company research."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

NAVER_API_URL = "https://openapi.naver.com/v1/search"


@SourceRegistry.register
class NaverSearchSource(BaseSource):
    """Multi-type Naver search: blog, cafe, web for comprehensive Korean coverage."""

    name = "naver_search"
    region = "kr"
    sections = ["culture", "overview", "strategy"]
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

        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        results: list[SourceResult] = []

        # Blog search — culture, work environment, interview reviews
        blog_items = self._search(
            "blog", f"{company} 면접 후기 OR 기업문화 OR 합격", headers
        )
        if blog_items:
            raw = "\n\n".join(
                f"[블로그] {self._strip_html(b['title'])}\n{self._strip_html(b['description'])}"
                for b in blog_items
            )
            results.append(SourceResult(
                source_name=self.name,
                section="culture",
                data={"naver_blog": blog_items},
                url=f"https://search.naver.com/search.naver?where=blog&query={company}",
                raw=raw,
            ))

        # Cafe search — community discussions, insider info
        cafe_items = self._search(
            "cafearticle", f"{company} 채용 OR 연봉 OR 복지 OR 조직문화", headers
        )
        if cafe_items:
            raw = "\n\n".join(
                f"[카페] {self._strip_html(c['title'])}\n{self._strip_html(c['description'])}"
                for c in cafe_items
            )
            results.append(SourceResult(
                source_name=self.name,
                section="culture",
                data={"naver_cafe": cafe_items},
                raw=raw,
            ))

        # Web document search — official pages, articles
        web_items = self._search(
            "webkr", f"{company} 전략 비전 사업방향 AI", headers
        )
        if web_items:
            raw = "\n\n".join(
                f"[웹] {self._strip_html(w['title'])}\n{self._strip_html(w['description'])}"
                for w in web_items
            )
            results.append(SourceResult(
                source_name=self.name,
                section="strategy",
                data={"naver_web": web_items},
                raw=raw,
            ))

        return results

    def _search(
        self, search_type: str, query: str, headers: dict[str, str]
    ) -> list[dict[str, str]]:
        """Execute a Naver search API call."""
        try:
            resp = httpx.get(
                f"{NAVER_API_URL}/{search_type}.json",
                params={"query": query, "display": 10, "sort": "date"},
                headers=headers,
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": self._strip_html(item.get("title", "")),
                    "description": self._strip_html(item.get("description", "")),
                    "link": item.get("link", item.get("originallink", "")),
                    "pub_date": item.get("postdate", item.get("pubDate", "")),
                }
                for item in data.get("items", [])
            ]
        except Exception:
            return []

    @staticmethod
    def _strip_html(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)
