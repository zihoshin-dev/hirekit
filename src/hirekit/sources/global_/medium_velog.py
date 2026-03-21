"""Medium and Velog tech article source — collect company engineering posts."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

KNOWN_MEDIUM_PUBS: dict[str, str] = {
    "당근": "daangn",
    "당근마켓": "daangn",
    "쿠팡": "coupang-engineering",
    "무신사": "musinsa-tech",
    "야놀자": "yanolja",
}

# Velog company tag mappings (Korean company → velog tag slug)
KNOWN_VELOG_TAGS: dict[str, str] = {
    "카카오": "kakao",
    "토스": "toss",
    "네이버": "naver",
    "당근": "daangn",
    "쿠팡": "coupang",
}


@SourceRegistry.register
class MediumVelogSource(BaseSource):
    """Collect tech articles from Medium publications and Velog tags."""

    name = "medium_velog"
    region = "global"
    sections = ["tech", "culture"]
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            import bs4  # noqa: F401
            return True
        except ImportError:
            return False

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        results: list[SourceResult] = []

        # Medium
        medium_slug = kwargs.get("medium_slug") or self._resolve_medium_slug(company)
        if medium_slug:
            medium_results = self._collect_medium(company, medium_slug)
            results.extend(medium_results)

        # Velog
        velog_tag = kwargs.get("velog_tag") or self._resolve_velog_tag(company)
        if velog_tag:
            velog_results = self._collect_velog(company, velog_tag)
            results.extend(velog_results)

        return results

    def _resolve_medium_slug(self, company: str) -> str:
        normalized = company.strip().replace(" ", "")
        for known, slug in KNOWN_MEDIUM_PUBS.items():
            known_norm = known.replace(" ", "")
            if normalized in known_norm or known_norm in normalized:
                return slug
        return ""

    def _resolve_velog_tag(self, company: str) -> str:
        normalized = company.strip().replace(" ", "")
        for known, tag in KNOWN_VELOG_TAGS.items():
            known_norm = known.replace(" ", "")
            if normalized in known_norm or known_norm in normalized:
                return tag
        return ""

    def _collect_medium(self, company: str, slug: str) -> list[SourceResult]:
        """Fetch articles from a Medium publication via RSS."""
        rss_url = f"https://medium.com/feed/{slug}"
        try:
            resp = httpx.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                logger.debug("Medium RSS %s returned HTTP %s", rss_url, resp.status_code)
                return []

            posts = self._parse_rss(resp.text)
            if not posts:
                return []

            pub_url = f"https://medium.com/{slug}"
            data: dict[str, Any] = {
                "source": "medium",
                "publication": slug,
                "posts": posts[:10],
                "post_count": len(posts),
            }
            return [
                SourceResult(
                    source_name=self.name,
                    section="tech",
                    data=data,
                    url=pub_url,
                    raw=self._format_raw_medium(company, data, pub_url),
                )
            ]
        except Exception as e:
            logger.debug("Medium collect failed for slug '%s': %s", slug, e)
            return []

    def _collect_velog(self, company: str, tag: str) -> list[SourceResult]:
        """Scrape Velog tag page for company-related posts."""
        velog_url = f"https://velog.io/tags/{tag}"
        try:
            from bs4 import BeautifulSoup

            resp = httpx.get(
                velog_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                logger.debug("Velog %s returned HTTP %s", velog_url, resp.status_code)
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            posts: list[dict[str, Any]] = []

            for selector in ["h2 a", "h3 a", ".title a", "a[href*='/@']"]:
                try:
                    anchors = soup.select(selector)[:15]
                    for a in anchors:
                        title = a.get_text(strip=True)
                        href = a.get("href", "")
                        if not title or len(title) < 5:
                            continue
                        full_href = (
                            href if href.startswith("http")
                            else "https://velog.io" + href
                        )
                        entry = {"title": title, "link": full_href, "date": ""}
                        if entry not in posts:
                            posts.append(entry)
                    if len(posts) >= 5:
                        break
                except Exception:
                    continue

            if not posts:
                return []

            data = {
                "source": "velog",
                "tag": tag,
                "posts": posts[:10],
                "post_count": len(posts),
            }
            return [
                SourceResult(
                    source_name=self.name,
                    section="tech",
                    data=data,
                    url=velog_url,
                    raw=self._format_raw_velog(company, data, velog_url),
                )
            ]
        except Exception as e:
            logger.debug("Velog collect failed for tag '%s': %s", tag, e)
            return []

    @staticmethod
    def _parse_rss(xml_text: str) -> list[dict[str, Any]]:
        """Parse RSS 2.0 or Atom XML into a post list."""
        posts: list[dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        # RSS 2.0
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item")[:10]:
                title = item.findtext("title", "").strip()
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()
                if title:
                    posts.append({"title": title, "link": link, "date": pub_date})
            return posts

        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns)[:10]:
            title_el = entry.find("atom:title", ns)
            link_el = entry.find("atom:link", ns)
            updated_el = entry.find("atom:updated", ns)
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.get("href", "") if link_el is not None else ""
            date = updated_el.text.strip() if updated_el is not None and updated_el.text else ""
            if title:
                posts.append({"title": title, "link": link, "date": date})

        return posts

    @staticmethod
    def _format_raw_medium(company: str, data: dict[str, Any], url: str) -> str:
        lines = [f"[{company} Medium 블로그: {url}]"]
        pub = data.get("publication", "")
        count = data.get("post_count", 0)
        lines.append(f"publication: {pub}, 포스팅 {count}개")
        posts = data.get("posts", [])
        if posts:
            lines.append("\n[최근 포스팅]")
            for p in posts:
                date_str = f" ({p['date']})" if p.get("date") else ""
                lines.append(f"  - {p['title']}{date_str}")
                if p.get("link"):
                    lines.append(f"    {p['link']}")
        return "\n".join(lines)

    @staticmethod
    def _format_raw_velog(company: str, data: dict[str, Any], url: str) -> str:
        lines = [f"[{company} Velog: {url}]"]
        lines.append(f"tag: {data.get('tag', '')}, 포스팅 {data.get('post_count', 0)}개")
        posts = data.get("posts", [])
        if posts:
            lines.append("\n[최근 포스팅]")
            for p in posts:
                lines.append(f"  - {p['title']}")
                if p.get("link"):
                    lines.append(f"    {p['link']}")
        return "\n".join(lines)
