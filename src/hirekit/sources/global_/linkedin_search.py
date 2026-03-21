"""LinkedIn company info — indirect collection via Brave Search (no LinkedIn API)."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

BRAVE_API_URL = "https://api.search.brave.com/res/v1"

KNOWN_LINKEDIN_SLUGS: dict[str, str] = {
    "카카오": "kakaocorp",
    "토스": "viva-republica",
    "네이버": "naver-corporation",
    "쿠팡": "coupang",
    "당근": "danggeun-market",
}

_EMPLOYEE_PATTERN = re.compile(
    r"([\d,]+)\s*(?:명|employees?|직원|명의\s*직원)",
    re.IGNORECASE,
)
_INDUSTRY_PATTERN = re.compile(
    r"(?:산업|Industry|업종)[:\s]+([^\n\|·]{3,40})",
    re.IGNORECASE,
)
_LOCATION_PATTERN = re.compile(
    r"(?:본사|Headquarters?|위치|Location)[:\s]+([^\n\|·]{3,40})",
    re.IGNORECASE,
)


@SourceRegistry.register
class LinkedInSearchSource(BaseSource):
    """Collect LinkedIn company data indirectly via Brave Search snippets."""

    name = "linkedin_search"
    region = "global"
    sections = ["overview", "culture"]
    requires_api_key = True
    api_key_env_var = "BRAVE_API_KEY"

    def is_available(self) -> bool:
        return bool(os.environ.get(self.api_key_env_var))

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        api_key = os.environ.get(self.api_key_env_var, "")
        if not api_key:
            return []

        slug = KNOWN_LINKEDIN_SLUGS.get(company) or _guess_slug(company)
        linkedin_url = f"https://www.linkedin.com/company/{slug}"

        snippets = self._search_linkedin(slug, api_key)
        if not snippets:
            return []

        combined_text = " ".join(
            s.get("title", "") + " " + s.get("description", "") for s in snippets
        )

        employee_count = _extract_employees(combined_text)
        industry = _extract_first(combined_text, _INDUSTRY_PATTERN)
        headquarters = _extract_first(combined_text, _LOCATION_PATTERN)

        raw_lines = [f"[LinkedIn — {company}] {linkedin_url}"]
        if employee_count:
            raw_lines.append(f"직원 수: {employee_count}")
        if industry:
            raw_lines.append(f"산업: {industry}")
        if headquarters:
            raw_lines.append(f"본사: {headquarters}")
        raw_lines.append("")
        for s in snippets[:10]:
            raw_lines.append(f"[{s.get('url', '')}]")
            raw_lines.append(s.get("description", ""))

        return [
            SourceResult(
                source_name=self.name,
                section="overview",
                data={
                    "linkedin_url": linkedin_url,
                    "slug": slug,
                    "employee_count": employee_count,
                    "industry": industry,
                    "headquarters": headquarters,
                    "snippets": snippets[:10],
                },
                confidence=0.65,
                url=linkedin_url,
                raw="\n".join(raw_lines),
            )
        ]

    def _search_linkedin(self, slug: str, api_key: str) -> list[dict[str, str]]:
        query = f"site:linkedin.com/company/{slug}"
        try:
            resp = httpx.get(
                f"{BRAVE_API_URL}/web/search",
                params={"q": query, "count": 10, "search_lang": "en"},
                headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "title": r.get("title", ""),
                    "description": r.get("description", ""),
                    "url": r.get("url", ""),
                }
                for r in data.get("web", {}).get("results", [])[:10]
            ]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_slug(company: str) -> str:
    """Best-effort slug from company name (ASCII-only, lowercased, hyphenated)."""
    slug = company.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or company


def _extract_employees(text: str) -> str:
    match = _EMPLOYEE_PATTERN.search(text)
    if match:
        return match.group(1).replace(",", "") + "명"
    return ""


def _extract_first(text: str, pattern: re.Pattern[str]) -> str:
    match = pattern.search(text)
    if match:
        return match.group(1).strip()[:60]
    return ""
