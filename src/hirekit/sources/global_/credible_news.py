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

_LEADERSHIP_KEYWORDS = (
    "ceo",
    "cfo",
    "cto",
    "chairman",
    "founder",
    "leadership",
    "executive",
    "대표",
    "사장",
    "회장",
    "경영진",
    "임원",
)
_LEADERSHIP_TRANSITION_KEYWORDS = (
    "appoint",
    "appointed",
    "hire",
    "joins",
    "promote",
    "replace",
    "replaced",
    "resign",
    "steps down",
    "교체",
    "사임",
    "선임",
    "영입",
)
_ORG_HEALTH_KEYWORDS = (
    "layoff",
    "restructuring",
    "turnover",
    "attrition",
    "whistleblower",
    "morale",
    "union",
    "strike",
    "감원",
    "구조조정",
    "퇴사",
    "노조",
    "파업",
    "조직",
)
_STRATEGIC_DIRECTION_KEYWORDS = (
    "strategy",
    "vision",
    "mission",
    "roadmap",
    "investment",
    "expansion",
    "acquisition",
    "merger",
    "ai",
    "전략",
    "비전",
    "미션",
    "투자",
    "확장",
    "인수",
    "합병",
    "신사업",
)
_ORG_HEALTH_CONCERN_KEYWORDS = (
    "layoff",
    "restructuring",
    "turnover",
    "attrition",
    "whistleblower",
    "union",
    "strike",
    "감원",
    "구조조정",
    "퇴사",
    "파업",
)


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

        intl_articles = self._collect_from_feeds(company, NEWS_FEEDS)
        if intl_articles:
            raw = "\n\n".join(f"[{a['source']}] {a['title']} ({a['pub_date']})" for a in intl_articles)
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="strategy",
                    data={
                        "international_news": intl_articles,
                        "leadership_evidence": self._build_news_evidence(intl_articles, "leadership"),
                        "org_health_evidence": self._build_news_evidence(intl_articles, "org_health"),
                        "strategic_direction_evidence": self._build_news_evidence(
                            intl_articles,
                            "strategic_direction",
                        ),
                    },
                    url=f"https://news.google.com/search?q={quote(company)}",
                    raw=f"[해외 공신력 뉴스 — {len(intl_articles)}건]\n{raw}",
                    confidence=0.75,
                    trust_label="supporting",
                    source_authority="credible_reporting",
                )
            )

        if lang == "ko":
            kr_articles = self._collect_from_feeds(company, KR_NEWS_FEEDS)
            if kr_articles:
                raw = "\n\n".join(f"[{a['source']}] {a['title']} ({a['pub_date']})" for a in kr_articles)
                results.append(
                    SourceResult(
                        source_name=self.name,
                        section="overview",
                        data={
                            "korean_credible_news": kr_articles,
                            "leadership_evidence": self._build_news_evidence(kr_articles, "leadership"),
                            "org_health_evidence": self._build_news_evidence(kr_articles, "org_health"),
                            "strategic_direction_evidence": self._build_news_evidence(
                                kr_articles,
                                "strategic_direction",
                            ),
                        },
                        raw=f"[국내 경제/IT 뉴스 — {len(kr_articles)}건]\n{raw}",
                        confidence=0.75,
                        trust_label="supporting",
                        source_authority="credible_reporting",
                    )
                )

        return results

    def _collect_from_feeds(self, company: str, feeds: dict[str, dict[str, str]]) -> list[dict[str, str]]:
        """Collect articles from multiple RSS feeds."""
        all_articles: list[dict[str, str]] = []

        for feed_id, feed_info in feeds.items():
            url = feed_info["search_url"].format(query=quote(company))
            try:
                resp = httpx.get(url, timeout=8, follow_redirects=True)
                if resp.status_code != 200:
                    continue

                articles = self._parse_rss(resp.text, feed_info["name"])
                all_articles.extend(articles[:3])
            except Exception:
                continue

        return all_articles

    def _build_news_evidence(self, articles: list[dict[str, str]], category: str) -> list[dict[str, str]]:
        evidence: list[dict[str, str]] = []
        keywords = self._keywords_for_category(category)

        for index, article in enumerate(articles, start=1):
            haystack = " ".join(filter(None, [article.get("title", ""), article.get("description", "")])).lower()
            if not haystack or not any(keyword in haystack for keyword in keywords):
                continue

            source_slug = article.get("source", "news").lower().replace(" ", "_")
            evidence.append(
                {
                    "claim_key": self._claim_key_for_category(category),
                    "summary": article.get("title", ""),
                    "status": self._status_for_article(category, haystack),
                    "source_name": self.name,
                    "source_authority": "credible_reporting",
                    "trust_label": "supporting",
                    "evidence_id": f"{self.name}:{category}:{source_slug}:{index}",
                    "url": article.get("link", ""),
                    "published_at": article.get("pub_date", ""),
                }
            )

        return evidence[:6]

    @staticmethod
    def _claim_key_for_category(category: str) -> str:
        mapping = {
            "leadership": "leadership_signal",
            "org_health": "org_health_signal",
            "strategic_direction": "strategic_direction_signal",
        }
        return mapping.get(category, category)

    @staticmethod
    def _keywords_for_category(category: str) -> tuple[str, ...]:
        mapping = {
            "leadership": _LEADERSHIP_KEYWORDS,
            "org_health": _ORG_HEALTH_KEYWORDS,
            "strategic_direction": _STRATEGIC_DIRECTION_KEYWORDS,
        }
        return mapping.get(category, ())

    @staticmethod
    def _status_for_article(category: str, haystack: str) -> str:
        if category == "leadership":
            if any(keyword in haystack for keyword in _LEADERSHIP_TRANSITION_KEYWORDS):
                return "transition"
            return "reported"
        if category == "org_health":
            if any(keyword in haystack for keyword in _ORG_HEALTH_CONCERN_KEYWORDS):
                return "concern"
            return "reported"
        return "declared"

    @staticmethod
    def _parse_rss(xml_text: str, source_name: str) -> list[dict[str, str]]:
        articles: list[dict[str, str]] = []
        try:
            root = ET.fromstring(xml_text)
            for item in root.findall(".//item"):
                articles.append(
                    {
                        "title": item.findtext("title", ""),
                        "description": item.findtext("description", ""),
                        "link": item.findtext("link", ""),
                        "pub_date": item.findtext("pubDate", ""),
                        "source": source_name,
                    }
                )
        except ET.ParseError:
            pass
        return articles
