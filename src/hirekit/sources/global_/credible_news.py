"""Credible international news sources via RSS feeds — Reuters, Bloomberg, TechCrunch, etc."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

# Curated list of credible news RSS feeds with search capability
NEWS_FEEDS: dict[str, dict[str, str]] = {
    "reuters": {
        "name": "Reuters",
        "search_url": "https://news.google.com/rss/search?q=site:reuters.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "bloomberg": {
        "name": "Bloomberg",
        "search_url": "https://news.google.com/rss/search?q=site:bloomberg.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "techcrunch": {
        "name": "TechCrunch",
        "search_url": "https://news.google.com/rss/search?q=site:techcrunch.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "wsj": {
        "name": "Wall Street Journal",
        "search_url": "https://news.google.com/rss/search?q=site:wsj.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "ft": {
        "name": "Financial Times",
        "search_url": "https://news.google.com/rss/search?q=site:ft.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "nikkei": {
        "name": "Nikkei Asia",
        "search_url": "https://news.google.com/rss/search?q=site:asia.nikkei.com+{query}&hl=en&gl=US&ceid=US:en",
    },
    "theinformation": {
        "name": "The Information",
        "search_url": "https://news.google.com/rss/search?q=site:theinformation.com+{query}&hl=en&gl=US&ceid=US:en",
    },
}

# Korean credible sources
KR_NEWS_FEEDS: dict[str, dict[str, str]] = {
    "hankyung": {
        "name": "한국경제",
        "search_url": "https://news.google.com/rss/search?q=site:hankyung.com+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
    "chosunbiz": {
        "name": "조선비즈",
        "search_url": "https://news.google.com/rss/search?q=site:biz.chosun.com+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
    "mk": {
        "name": "매일경제",
        "search_url": "https://news.google.com/rss/search?q=site:mk.co.kr+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
    "zdnet": {
        "name": "ZDNet Korea",
        "search_url": "https://news.google.com/rss/search?q=site:zdnet.co.kr+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
    "bloter": {
        "name": "블로터",
        "search_url": "https://news.google.com/rss/search?q=site:bloter.net+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
    "byline": {
        "name": "바이라인네트워크",
        "search_url": "https://news.google.com/rss/search?q=site:byline.network+{query}&hl=ko&gl=KR&ceid=KR:ko",
    },
}


@SourceRegistry.register
class CredibleNewsSource(BaseSource):
    """Collect news from curated credible international and Korean news sources."""

    name = "credible_news"
    region = "global"
    sections = ["overview", "strategy", "industry"]
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        results: list[SourceResult] = []
        lang = kwargs.get("lang", "ko")

        # International credible news
        intl_articles = self._collect_from_feeds(company, NEWS_FEEDS)
        if intl_articles:
            raw = "\n\n".join(
                f"[{a['source']}] {a['title']} ({a['pub_date']})"
                for a in intl_articles
            )
            results.append(SourceResult(
                source_name=self.name,
                section="strategy",
                data={"international_news": intl_articles},
                url=f"https://news.google.com/search?q={quote(company)}",
                raw=f"[해외 공신력 뉴스 — {len(intl_articles)}건]\n{raw}",
            ))

        # Korean credible news
        if lang == "ko":
            kr_articles = self._collect_from_feeds(company, KR_NEWS_FEEDS)
            if kr_articles:
                raw = "\n\n".join(
                    f"[{a['source']}] {a['title']} ({a['pub_date']})"
                    for a in kr_articles
                )
                results.append(SourceResult(
                    source_name=self.name,
                    section="overview",
                    data={"korean_credible_news": kr_articles},
                    raw=f"[국내 경제/IT 뉴스 — {len(kr_articles)}건]\n{raw}",
                ))

        return results

    def _collect_from_feeds(
        self, company: str, feeds: dict[str, dict[str, str]]
    ) -> list[dict[str, str]]:
        """Collect articles from multiple RSS feeds."""
        all_articles: list[dict[str, str]] = []

        for feed_id, feed_info in feeds.items():
            url = feed_info["search_url"].format(query=quote(company))
            try:
                resp = httpx.get(url, timeout=8, follow_redirects=True)
                if resp.status_code != 200:
                    continue

                articles = self._parse_rss(resp.text, feed_info["name"])
                all_articles.extend(articles[:3])  # Max 3 per source
            except Exception:
                continue

        return all_articles

    @staticmethod
    def _parse_rss(xml_text: str, source_name: str) -> list[dict[str, str]]:
        """Parse RSS XML."""
        articles: list[dict[str, str]] = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item"):
                articles.append({
                    "title": item.findtext("title", ""),
                    "link": item.findtext("link", ""),
                    "pub_date": item.findtext("pubDate", ""),
                    "source": source_name,
                })
        except ET.ParseError:
            pass
        return articles
