"""Company official website data source — mission, vision, values, products."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

KNOWN_WEBSITES: dict[str, str] = {
    "카카오": "https://kakaocorp.com",
    "토스": "https://toss.im/team",
    "네이버": "https://navercorp.com",
    "쿠팡": "https://aboutcoupang.com",
    "우아한형제들": "https://woowahan.com",
    "배달의민족": "https://woowahan.com",
    "당근": "https://about.daangn.com",
    "당근마켓": "https://about.daangn.com",
    "무신사": "https://musinsa.com/company",
    "라인": "https://linecorp.com",
    "라인플러스": "https://linecorp.com",
    "야놀자": "https://yanolja.in",
    "삼성전자": "https://samsung.com/sec/aboutsamsung",
    "SK하이닉스": "https://skhynix.com",
    "크래프톤": "https://krafton.com",
    "하이브": "https://hybecorp.com",
    "넥슨코리아": "https://company.nexon.com",
}


@SourceRegistry.register
class CompanyWebsiteSource(BaseSource):
    """Extract mission/vision/values/products from a company's official website."""

    name = "company_website"
    region = "global"
    sections = ["overview", "culture"]
    requires_api_key = False

    def is_available(self) -> bool:
        try:
            import bs4  # noqa: F401
            return True
        except ImportError:
            return False

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        url = kwargs.get("website_url") or self._resolve_url(company)
        if not url:
            logger.debug("No website URL found for '%s'", company)
            return []

        try:
            from bs4 import BeautifulSoup

            resp = httpx.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit/1.0)"},
                timeout=15,
                follow_redirects=True,
            )
            if resp.status_code != 200:
                logger.debug("company_website HTTP %s for %s", resp.status_code, url)
                return []

            soup = BeautifulSoup(resp.text, "lxml")
            data = self._extract(soup, url)
            if not data:
                return []

            raw = self._format_raw(company, data, url)
            return [
                SourceResult(
                    source_name=self.name,
                    section="overview",
                    data=data,
                    url=url,
                    raw=raw,
                )
            ]
        except Exception as e:
            logger.debug("company_website collect failed for '%s': %s", company, e)
            return []

    def _resolve_url(self, company: str) -> str:
        """Look up URL from known websites dict, with substring matching."""
        normalized = company.strip().replace(" ", "")
        for known, url in KNOWN_WEBSITES.items():
            known_norm = known.replace(" ", "")
            if normalized in known_norm or known_norm in normalized:
                return url
        return ""

    @staticmethod
    def _extract(soup: Any, url: str) -> dict[str, Any]:
        """Extract structured info from parsed HTML."""
        data: dict[str, Any] = {}

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            data["meta_description"] = meta_desc["content"].strip()

        # OG description fallback
        if "meta_description" not in data:
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                data["meta_description"] = og_desc["content"].strip()

        # Page title
        title_tag = soup.find("title")
        if title_tag:
            data["page_title"] = title_tag.get_text(strip=True)

        # About/mission/vision text blocks
        about_texts: list[str] = []
        for selector in [
            "[class*='about']", "[class*='mission']", "[class*='vision']",
            "[class*='value']", "[id*='about']", "[id*='mission']",
            "section", "main",
        ]:
            try:
                elements = soup.select(selector)[:3]
                for el in elements:
                    text = el.get_text(" ", strip=True)
                    if 30 < len(text) < 1000:
                        about_texts.append(text)
            except Exception:
                continue

        if about_texts:
            # Deduplicate while preserving order
            seen: set[str] = set()
            unique: list[str] = []
            for t in about_texts:
                if t not in seen:
                    seen.add(t)
                    unique.append(t)
            data["about_text"] = unique[:5]

        # Career page links
        career_links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            text = a.get_text(strip=True).lower()
            if any(kw in href.lower() or kw in text for kw in ["career", "job", "채용", "recruit"]):
                full_href = (
                        href if href.startswith("http")
                        else url.rstrip("/") + "/" + href.lstrip("/")
                    )
                if full_href not in career_links:
                    career_links.append(full_href)
        if career_links:
            data["career_links"] = career_links[:3]

        return data

    @staticmethod
    def _format_raw(company: str, data: dict[str, Any], url: str) -> str:
        lines = [f"[{company} 공식 홈페이지: {url}]"]
        if data.get("page_title"):
            lines.append(f"제목: {data['page_title']}")
        if data.get("meta_description"):
            lines.append(f"소개: {data['meta_description']}")
        if data.get("about_text"):
            lines.append("\n[About/Mission/Vision]")
            for t in data["about_text"]:
                lines.append(f"  - {t[:300]}")
        if data.get("career_links"):
            lines.append("\n[채용 페이지]")
            for link in data["career_links"]:
                lines.append(f"  - {link}")
        return "\n".join(lines)
