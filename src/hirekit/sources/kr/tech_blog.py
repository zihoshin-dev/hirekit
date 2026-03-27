"""Tech blog data source — collect recent posts from Korean company tech blogs."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from hirekit.core.filters import filter_recent
from hirekit.core.tech_taxonomy import (
    build_actual_work_profile,
    build_stack_reality,
    extract_stack_signals,
    extract_work_signals,
)
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

KNOWN_TECH_BLOGS: dict[str, str] = {
    "카카오": "https://tech.kakao.com",
    "토스": "https://toss.tech",
    "네이버": "https://d2.naver.com/helloworld",
    "당근": "https://medium.com/daangn",
    "당근마켓": "https://medium.com/daangn",
    "우아한형제들": "https://techblog.woowahan.com",
    "배달의민족": "https://techblog.woowahan.com",
    "라인": "https://engineering.linecorp.com/ko/blog",
    "라인플러스": "https://engineering.linecorp.com/ko/blog",
    "쿠팡": "https://medium.com/coupang-engineering",
    "무신사": "https://medium.com/musinsa-tech",
    "야놀자": "https://medium.com/yanolja",
    "카카오페이": "https://tech.kakaopay.com",
    "카카오뱅크": "https://tech.kakaobank.com",
}

TECH_KEYWORDS = [
    "Kubernetes",
    "Kafka",
    "React",
    "Spring",
    "ML",
    "LLM",
    "Docker",
    "Spark",
    "Flink",
    "Redis",
    "GraphQL",
    "gRPC",
    "Rust",
    "Go",
    "Python",
    "TypeScript",
    "AWS",
    "GCP",
    "Azure",
    "MSA",
    "CI/CD",
    "DevOps",
    "MLOps",
    "RAG",
    "GPT",
    "Transformer",
    "대규모",
    "분산",
]

AI_KEYWORDS = [
    "AI",
    "ML",
    "LLM",
    "딥러닝",
    "GPT",
    "생성형",
    "인공지능",
    "머신러닝",
    "딥러닝",
    "ChatGPT",
    "RAG",
    "MLOps",
    "Transformer",
    "생성AI",
    "GenAI",
    "Foundation Model",
    "파운데이션",
    "Diffusion",
]

MEDIUM_DOMAINS = {"medium.com"}


def _is_medium(url: str) -> bool:
    return any(domain in url for domain in MEDIUM_DOMAINS)


@SourceRegistry.register
class TechBlogSource(BaseSource):
    """Collect recent posts from Korean company tech blogs."""

    name = "tech_blog"
    region = "kr"
    sections = ["tech", "culture"]
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            __import__("bs4")

            return True
        except ImportError:
            return False

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        url = kwargs.get("tech_blog_url") or self._resolve_url(company)
        if not url:
            logger.debug("No tech blog URL found for '%s'", company)
            return []

        try:
            if _is_medium(url):
                posts = self._fetch_medium_rss(url)
            else:
                posts = self._fetch_html_blog(url)

            if not posts:
                return []

            # Filter to last 6 months only
            recent_posts = filter_recent(posts, months=6, date_keys=("date", "pub_date", "published"))
            active_posts = recent_posts or posts

            keywords = self._extract_keywords(active_posts)
            ai_posts = self._filter_ai_posts(active_posts)
            stack_signals = extract_stack_signals(
                [str(post.get("title", "")).strip() for post in active_posts],
                source_name=self.name,
                source_authority="company_operated",
                signal_type="post_title",
                base_confidence=0.68,
            )
            work_signals = extract_work_signals(
                [str(post.get("title", "")).strip() for post in active_posts],
                source_name=self.name,
                source_authority="company_operated",
                base_confidence=0.62,
            )
            stack_reality = build_stack_reality(stack_signals)
            actual_work = build_actual_work_profile(work_signals)
            tech_stack = self._normalized_stack_summary(stack_reality) or self._extract_tech_stack(active_posts)

            data: dict[str, Any] = {
                "blog_url": url,
                "recent_posts": active_posts[:10],
                "tech_keywords": keywords,
                "post_count": len(active_posts),
                "ai_posts_count": len(ai_posts),
                "tech_stack_mentioned": tech_stack,
                "stack_signals": stack_signals,
                "stack_reality": stack_reality,
                "actual_work_signals": work_signals,
                "actual_work": actual_work,
            }
            raw = self._format_raw(company, data, url)
            return [
                SourceResult(
                    source_name=self.name,
                    section="tech",
                    data=data,
                    url=url,
                    raw=raw,
                )
            ]
        except Exception as e:
            logger.debug("tech_blog collect failed for '%s': %s", company, e)
            return []

    def _resolve_url(self, company: str) -> str:
        normalized = company.strip().replace(" ", "")
        for known, url in KNOWN_TECH_BLOGS.items():
            known_norm = known.replace(" ", "")
            if normalized in known_norm or known_norm in normalized:
                return url
        return ""

    def _fetch_medium_rss(self, blog_url: str) -> list[dict[str, Any]]:
        """Parse Medium RSS feed for a publication or user."""
        # Extract slug from URL: https://medium.com/slug or https://medium.com/@user
        slug = blog_url.rstrip("/").split("medium.com/")[-1]
        rss_url = f"https://medium.com/feed/{slug}"
        try:
            resp = httpx.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                return []
            return self._parse_rss(resp.text)
        except Exception as e:
            logger.debug("Medium RSS fetch failed (%s): %s", rss_url, e)
            return []

    @staticmethod
    def _parse_rss(xml_text: str) -> list[dict[str, Any]]:
        """Parse RSS/Atom XML into post list."""
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

    def _fetch_html_blog(self, blog_url: str) -> list[dict[str, Any]]:
        """Scrape HTML blog for article titles and links."""
        try:
            from bs4 import BeautifulSoup

            resp = httpx.get(
                blog_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            posts: list[dict[str, Any]] = []

            # Try common article/post selectors
            for selector in ["article a", "h2 a", "h3 a", ".post-title a", ".entry-title a"]:
                try:
                    anchors = soup.select(selector)[:15]
                    for a in anchors:
                        title = a.get_text(strip=True)
                        href_attr = a.get("href", "")
                        href = href_attr if isinstance(href_attr, str) else ""
                        if not title or len(title) < 5:
                            continue
                        full_href = href if href.startswith("http") else blog_url.rstrip("/") + "/" + href.lstrip("/")
                        entry = {"title": title, "link": full_href, "date": ""}
                        if entry not in posts:
                            posts.append(entry)
                    if len(posts) >= 5:
                        break
                except Exception:
                    continue

            return posts[:10]
        except Exception as e:
            logger.debug("HTML blog fetch failed (%s): %s", blog_url, e)
            return []

    @staticmethod
    def _extract_keywords(posts: list[dict[str, Any]]) -> list[str]:
        """Extract tech keywords mentioned in post titles."""
        all_text = " ".join(p.get("title", "") for p in posts).lower()
        found = [kw for kw in TECH_KEYWORDS if kw.lower() in all_text]
        return found

    @staticmethod
    def _filter_ai_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return posts that mention AI-related keywords in the title."""
        ai_kw_lower = [kw.lower() for kw in AI_KEYWORDS]
        result = []
        for p in posts:
            title_lower = p.get("title", "").lower()
            if any(kw in title_lower for kw in ai_kw_lower):
                result.append(p)
        return result

    @staticmethod
    def _extract_tech_stack(posts: list[dict[str, Any]]) -> list[str]:
        """Extract tech stack keywords detected in post titles."""
        all_text = " ".join(p.get("title", "") for p in posts).lower()
        found = [kw for kw in TECH_KEYWORDS if kw.lower() in all_text]
        return found

    @staticmethod
    def _normalized_stack_summary(stack_reality: dict[str, list[dict[str, Any]]]) -> list[str]:
        normalized: list[str] = []
        for bucket in ("confirmed", "likely"):
            for claim in stack_reality.get(bucket, []):
                tech = str(claim.get("tech", "")).strip()
                if tech and tech not in normalized:
                    normalized.append(tech)
        return normalized

    @staticmethod
    def _format_raw(company: str, data: dict[str, Any], url: str) -> str:
        lines = [f"[{company} 기술 블로그: {url}]"]
        lines.append(f"최근 포스팅 {data.get('post_count', 0)}개 수집")
        ai_count = data.get("ai_posts_count", 0)
        if ai_count:
            lines.append(f"AI 관련 포스팅: {ai_count}개")
        tech_stack = data.get("tech_stack_mentioned", [])
        if tech_stack:
            lines.append(f"기술 스택: {', '.join(tech_stack)}")
        stack_reality = data.get("stack_reality", {})
        if isinstance(stack_reality, dict):
            confirmed = [item.get("tech", "") for item in stack_reality.get("confirmed", []) if item.get("tech")]
            likely = [item.get("tech", "") for item in stack_reality.get("likely", []) if item.get("tech")]
            adjacent = [item.get("tech", "") for item in stack_reality.get("adjacent", []) if item.get("tech")]
            if confirmed:
                lines.append(f"확인된 스택: {', '.join(confirmed)}")
            if likely:
                lines.append(f"가능성 높은 스택: {', '.join(likely)}")
            if adjacent:
                lines.append(f"역할 인접 도구: {', '.join(adjacent)}")
        actual_work = data.get("actual_work", {})
        if isinstance(actual_work, dict):
            work_patterns = [item.get("label", "") for item in actual_work.get("likely", []) if item.get("label")]
            if work_patterns:
                lines.append(f"실제 업무 신호: {', '.join(work_patterns)}")
        keywords = data.get("tech_keywords", [])
        if keywords:
            lines.append(f"기술 키워드: {', '.join(keywords)}")
        posts = data.get("recent_posts", [])
        if posts:
            lines.append("\n[최근 포스팅]")
            for p in posts:
                date_str = f" ({p['date']})" if p.get("date") else ""
                lines.append(f"  - {p['title']}{date_str}")
                if p.get("link"):
                    lines.append(f"    {p['link']}")
        return "\n".join(lines)
