"""Community review aggregator — indirect collection via search APIs (TOS-compliant)."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

BRAVE_API_URL = "https://api.search.brave.com/res/v1"
NAVER_API_URL = "https://openapi.naver.com/v1/search"

_RATING_PATTERN = re.compile(r"(\d(?:\.\d)?)\s*[점/]?\s*(?:점|\/\s*5)?")
_POSITIVE_KEYWORDS = (
    "좋아", "최고", "만족", "추천", "복지", "자율", "성장", "유연", "워라밸",
    "수평", "좋은", "긍정", "문화", "장점",
)
_NEGATIVE_KEYWORDS = (
    "야근", "힘들", "스트레스", "불만", "낮아", "단점", "퇴사", "힘든",
    "구식", "꼰대", "워라밸 나쁨", "수직",
)


@SourceRegistry.register
class CommunityReviewSource(BaseSource):
    """Collect company reviews indirectly via Brave/Naver search snippets."""

    name = "community_review"
    region = "kr"
    sections = ["culture"]
    requires_api_key = True
    api_key_env_var = "BRAVE_API_KEY"

    def is_available(self) -> bool:
        return bool(
            os.environ.get("BRAVE_API_KEY")
            or (os.environ.get("NAVER_CLIENT_ID") and os.environ.get("NAVER_CLIENT_SECRET"))
        )

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        results: list[SourceResult] = []

        snippets: list[dict[str, str]] = []

        brave_key = os.environ.get("BRAVE_API_KEY", "")
        if brave_key:
            snippets.extend(self._collect_brave(company, brave_key))

        naver_id = os.environ.get("NAVER_CLIENT_ID", "")
        naver_secret = os.environ.get("NAVER_CLIENT_SECRET", "")
        if naver_id and naver_secret:
            snippets.extend(self._collect_naver(company, naver_id, naver_secret))

        if not snippets:
            return []

        # Extract ratings and classify themes
        ratings = _extract_ratings(snippets)
        positive_themes = _classify_themes(snippets, _POSITIVE_KEYWORDS)
        negative_themes = _classify_themes(snippets, _NEGATIVE_KEYWORDS)

        avg_rating = sum(ratings) / len(ratings) if ratings else None

        raw_lines = [f"[{company} 커뮤니티 리뷰 — {len(snippets)}개 스니펫]"]
        if avg_rating is not None:
            raw_lines.append(f"추출 평균 평점: {avg_rating:.1f}")
        if positive_themes:
            raw_lines.append(f"긍정 키워드: {', '.join(positive_themes)}")
        if negative_themes:
            raw_lines.append(f"부정 키워드: {', '.join(negative_themes)}")
        raw_lines.append("")
        for s in snippets[:15]:
            raw_lines.append(f"[{s.get('source', '')}] {s.get('title', '')}")
            raw_lines.append(s.get("description", ""))

        results.append(SourceResult(
            source_name=self.name,
            section="culture",
            data={
                "snippet_count": len(snippets),
                "avg_rating": avg_rating,
                "positive_themes": positive_themes,
                "negative_themes": negative_themes,
                "snippets": snippets[:20],
            },
            confidence=0.6,
            url=f"https://search.naver.com/search.naver?query={company}+잡플래닛",
            raw="\n".join(raw_lines),
        ))

        return results

    # ------------------------------------------------------------------
    # Brave search helpers
    # ------------------------------------------------------------------

    def _collect_brave(self, company: str, api_key: str) -> list[dict[str, str]]:
        queries = [
            f"{company} 잡플래닛 평점",
            f"{company} 블라인드 리뷰 연봉",
        ]
        items: list[dict[str, str]] = []
        for query in queries:
            items.extend(self._brave_web_search(query, api_key))
        return items

    def _brave_web_search(self, query: str, api_key: str) -> list[dict[str, str]]:
        try:
            resp = httpx.get(
                f"{BRAVE_API_URL}/web/search",
                params={"q": query, "count": 10, "search_lang": "ko"},
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "source": "brave",
                    "title": r.get("title", ""),
                    "description": r.get("description", ""),
                    "url": r.get("url", ""),
                }
                for r in data.get("web", {}).get("results", [])[:10]
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Naver search helpers
    # ------------------------------------------------------------------

    def _collect_naver(
        self, company: str, client_id: str, client_secret: str
    ) -> list[dict[str, str]]:
        queries = [
            f"{company} 잡플래닛 평점",
            f"{company} 블라인드 리뷰 연봉",
        ]
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }
        items: list[dict[str, str]] = []
        for query in queries:
            items.extend(self._naver_web_search(query, headers))
        return items

    def _naver_web_search(
        self, query: str, headers: dict[str, str]
    ) -> list[dict[str, str]]:
        try:
            resp = httpx.get(
                f"{NAVER_API_URL}/webkr.json",
                params={"query": query, "display": 10},
                headers=headers,
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "source": "naver",
                    "title": _strip_html(item.get("title", "")),
                    "description": _strip_html(item.get("description", "")),
                    "url": item.get("link", ""),
                }
                for item in data.get("items", [])
            ]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _extract_ratings(snippets: list[dict[str, str]]) -> list[float]:
    ratings: list[float] = []
    for s in snippets:
        text = s.get("title", "") + " " + s.get("description", "")
        for match in _RATING_PATTERN.finditer(text):
            try:
                val = float(match.group(1))
                if 1.0 <= val <= 5.0:
                    ratings.append(val)
            except ValueError:
                continue
    return ratings


def _classify_themes(
    snippets: list[dict[str, str]], keywords: tuple[str, ...]
) -> list[str]:
    found: set[str] = set()
    for s in snippets:
        text = s.get("title", "") + " " + s.get("description", "")
        for kw in keywords:
            if kw in text:
                found.add(kw)
    return sorted(found)
