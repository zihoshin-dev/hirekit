"""Career page scraper — collect open positions from known company career sites."""

from __future__ import annotations

from typing import Any

import httpx
from bs4 import BeautifulSoup

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

KNOWN_CAREER_PAGES: dict[str, str] = {
    "카카오": "https://careers.kakao.com/jobs",
    "토스": "https://toss.im/career/jobs",
    "네이버": "https://recruit.navercorp.com",
    "쿠팡": "https://coupang.jobs/kr/jobs",
    "우아한형제들": "https://career.woowahan.com",
    "당근": "https://team.daangn.com/jobs",
    "무신사": "https://career.musinsa.com",
    "라인": "https://careers.linecorp.com/jobs",
    "야놀자": "https://yanolja.recruiter.co.kr",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


@SourceRegistry.register
class CareerPageSource(BaseSource):
    """Fetch open job positions from known company career pages."""

    name = "career_page"
    region = "global"
    sections = ["job", "culture"]
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        url = KNOWN_CAREER_PAGES.get(company)
        if not url:
            # Attempt a generic URL guess only if company name is ASCII-safe
            return []

        jobs = self._fetch_jobs(url)
        if not jobs:
            return []

        total = len(jobs)
        departments = sorted({j["department"] for j in jobs if j["department"]})
        raw_lines = [f"채용 포지션 총 {total}개 | {url}"]
        for j in jobs[:30]:  # cap raw text
            dept = f"[{j['department']}] " if j["department"] else ""
            raw_lines.append(f"- {dept}{j['title']}")

        raw = "\n".join(raw_lines)

        return [
            SourceResult(
                source_name=self.name,
                section="job",
                data={
                    "career_page_url": url,
                    "total_positions": total,
                    "departments": departments,
                    "jobs": jobs[:50],
                },
                confidence=0.8,
                url=url,
                raw=raw,
            )
        ]

    def _fetch_jobs(self, url: str) -> list[dict[str, str]]:
        """GET career page and extract job listings via BeautifulSoup."""
        try:
            resp = httpx.get(url, headers=_HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception:
            return []

        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            soup = BeautifulSoup(resp.text, "html.parser")

        jobs: list[dict[str, str]] = []

        # Strategy 1: look for common job list patterns
        # <li> or <div> containing role/position keywords
        candidates = (
            soup.find_all("li", class_=lambda c: c and any(
                kw in c.lower() for kw in ("job", "position", "role", "career", "posting", "item")
            ))
            or soup.find_all("div", class_=lambda c: c and any(
                kw in c.lower() for kw in ("job", "position", "role", "career", "posting")
            ))
        )

        for el in candidates[:100]:
            title = _extract_text(el, ["h1", "h2", "h3", "h4", "strong", "span", "a"])
            if not title or len(title) < 3:
                continue
            department = _extract_department(el)
            jobs.append({"title": title[:120], "department": department})

        # Strategy 2: fallback — any <a> whose text looks like a job title
        if not jobs:
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if 4 <= len(text) <= 80 and _looks_like_job(text):
                    jobs.append({"title": text, "department": ""})
                if len(jobs) >= 60:
                    break

        return _deduplicate(jobs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text(el: Any, tags: list[str]) -> str:
    for tag in tags:
        found = el.find(tag)
        if found:
            text = found.get_text(strip=True)
            if text:
                return text
    return el.get_text(separator=" ", strip=True)[:120]


def _extract_department(el: Any) -> str:
    """Try to find a department/team label inside a job element."""
    for cls_kw in ("department", "team", "category", "group", "부서", "팀"):
        node = el.find(class_=lambda c: c and cls_kw in c.lower())
        if node:
            text = node.get_text(strip=True)
            if text:
                return text[:60]
    return ""


_JOB_KEYWORDS = (
    "개발", "엔지니어", "디자이너", "기획", "마케팅", "데이터", "분석",
    "manager", "engineer", "developer", "designer", "analyst", "product",
    "backend", "frontend", "devops", "ios", "android", "ml", "ai",
)


def _looks_like_job(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _JOB_KEYWORDS)


def _deduplicate(jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for j in jobs:
        key = j["title"].strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(j)
    return result
