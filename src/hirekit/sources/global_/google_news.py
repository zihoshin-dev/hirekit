"""Google News search via RSS — no API key required."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult


@SourceRegistry.register
class GoogleNewsSource(BaseSource):
    """Collect recent news about a company via Google News RSS (no API key needed)."""

    name = "google_news"
    region = "global"
    sections = ["overview", "strategy", "industry"]
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        results: list[SourceResult] = []
        lang = kwargs.get("lang", "ko")

        queries = [
            f"{company} 채용 전략 AI",
            f"{company} 실적 사업",
        ] if lang == "ko" else [
            f"{company} strategy AI hiring",
            f"{company} earnings business",
        ]

        all_articles: list[dict[str, str]] = []
        for query in queries:
            articles = self._fetch_rss(query, lang)
            all_articles.extend(articles)

        if all_articles:
            # Deduplicate by title
            seen: set[str] = set()
            unique: list[dict[str, str]] = []
            for a in all_articles:
                if a["title"] not in seen:
                    seen.add(a["title"])
                    unique.append(a)

            raw_text = "\n\n".join(
                f"[{a['title']}] ({a['pub_date']})\n{a['source']}" for a in unique[:20]
            )

            results.append(SourceResult(
                source_name=self.name,
                section="overview",
                data={"google_news": unique[:20]},
                url=f"https://news.google.com/search?q={quote(company)}",
                raw=raw_text,
            ))

        return results

    def _fetch_rss(self, query: str, lang: str = "ko") -> list[dict[str, str]]:
        """Fetch Google News RSS feed."""
        hl = "ko" if lang == "ko" else "en"
        gl = "KR" if lang == "ko" else "US"
        ceid = f"{gl}:{hl}"

        try:
            resp = httpx.get(
                f"https://news.google.com/rss/search?q={quote(query)}&hl={hl}&gl={gl}&ceid={ceid}",
                timeout=10,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                return []

            return self._parse_rss(resp.text)
        except Exception:
            return []

    @staticmethod
    def _parse_rss(xml_text: str) -> list[dict[str, str]]:
        """Parse RSS XML into article list."""
        import xml.etree.ElementTree as ET

        articles: list[dict[str, str]] = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item")[:15]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                source = item.findtext("source", "")

                articles.append({
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                    "source": source,
                })
        except ET.ParseError:
            pass

        return articles
