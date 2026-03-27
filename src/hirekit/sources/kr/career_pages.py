"""채용 공고 수집기 — Greenhouse API + 네이버 API + Greeting ATS."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup

from hirekit.core.trust_contract import default_source_authority
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}

# Greenhouse Job Board 토큰 매핑
GREENHOUSE_BOARDS: dict[str, str] = {
    "쿠팡": "coupang",
    "당근": "daangn",
    "크래프톤": "krafton",
}

# Greeting ATS 슬러그 매핑
GREETING_SLUGS: dict[str, str] = {
    "SSG닷컴": "ssg",
    "리디": "ridi",
    "리벨리온": "rebellions",
    "마이리얼트립": "myrealtrip",
    "마키나락스": "makinarocks",
    "메이크스타": "makestar",
    "카카오페이": "kakaopay",
    "컬리": "kurly",
}

# 네이버 계열사 목록
NAVER_COMPANIES: frozenset[str] = frozenset(("네이버", "네이버웹툰", "네이버클라우드", "네이버파이낸셜"))

_EXPECTATION_SPLIT_PATTERN = re.compile(r"[\n;/]|(?:\s{2,})")


@dataclass
class JobPosting:
    """단일 채용 공고."""

    title: str
    company: str
    url: str
    location: str = ""
    department: str = ""
    employment_type: str = ""
    posted_at: str = ""
    description_snippet: str = ""  # 첫 200자


class JobPostingCollector:
    """채용 공고 수집기."""

    def __init__(self) -> None:
        self.client = httpx.Client(
            timeout=15,
            follow_redirects=True,
            headers=_HEADERS,
        )

    def collect_greenhouse(self, company: str) -> list[JobPosting]:
        """Greenhouse Job Board API로 채용 공고 수집."""
        board = GREENHOUSE_BOARDS.get(company)
        if not board:
            return []
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("greenhouse[%s]: request failed — %s", company, exc)
            return []

        jobs: list[dict[str, Any]] = resp.json().get("jobs", [])
        result: list[JobPosting] = []
        for j in jobs:
            departments: list[dict[str, Any]] = j.get("departments", [])
            dept = departments[0].get("name", "") if departments else ""
            result.append(
                JobPosting(
                    title=j.get("title", ""),
                    company=company,
                    url=j.get("absolute_url", ""),
                    location=j.get("location", {}).get("name", ""),
                    department=dept,
                    posted_at=(j.get("updated_at") or "")[:10],
                )
            )
        return result

    def collect_naver(self) -> list[JobPosting]:
        """네이버 채용 AJAX API로 공고 수집."""
        url = "https://recruit.navercorp.com/rcrt/loadJobList.do"
        params = {
            "entTypeCd": "",
            "workTypeCd": "",
            "enterTypeCd": "",
            "jobKindCd": "",
            "sysCompanyCd": "",
            "keyword": "",
            "classVal": "",
            "classDepth": "",
            "pageIndex": "1",
        }
        try:
            resp = self.client.post(url, data=params)
            resp.raise_for_status()
            payload: dict[str, Any] = resp.json()
        except Exception as exc:
            logger.warning("naver: request failed — %s", exc)
            return []

        job_list: list[dict[str, Any]] = payload.get("list", [])
        result: list[JobPosting] = []
        for j in job_list:
            recruit_no = j.get("rcrtNo", "")
            job_url = f"https://recruit.navercorp.com/rcrt/view.do?rcrtNo={recruit_no}" if recruit_no else ""
            result.append(
                JobPosting(
                    title=j.get("jobNm", ""),
                    company="네이버",
                    url=job_url,
                    location=j.get("workLocNm", ""),
                    department=j.get("deptNm", ""),
                    employment_type=j.get("enterTypeNm", ""),
                    posted_at=(j.get("rcrtEndDt") or "")[:10],
                )
            )
        return result

    def collect_greeting(self, company: str) -> list[JobPosting]:
        """Greeting ATS 공고 수집 (HTML 파싱)."""
        slug = GREETING_SLUGS.get(company)
        if not slug:
            return []
        url = f"https://{slug}.career.greetinghr.com/ko/career"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("greeting[%s]: request failed — %s", company, exc)
            return []

        try:
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception:
            soup = BeautifulSoup(resp.text, "html.parser")

        result: list[JobPosting] = []

        # Greeting HR renders job cards as <a> tags with data attributes or
        # nested title/department spans.
        for card in soup.find_all("a", href=True):
            href_value = card.get("href", "")
            href = href_value if isinstance(href_value, str) else ""
            if "/career/" not in href and "/job/" not in href:
                continue

            title_el = card.find(class_=_has_title_class) or card.find("h3") or card.find("h4") or card.find("strong")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            dept_el = card.find(class_=_has_department_class)
            dept = dept_el.get_text(strip=True) if dept_el else ""

            full_url = href if href.startswith("http") else f"https://{slug}.career.greetinghr.com{href}"
            result.append(
                JobPosting(
                    title=title[:120],
                    company=company,
                    url=full_url,
                    department=dept[:60],
                )
            )

        # Deduplicate by URL
        seen: set[str] = set()
        deduped: list[JobPosting] = []
        for p in result:
            key = p.url or p.title.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(p)
        return deduped

    def collect_all(self, company: str) -> list[JobPosting]:
        """기업에 맞는 수집기를 자동 선택."""
        if company in GREENHOUSE_BOARDS:
            return self.collect_greenhouse(company)
        if company in GREETING_SLUGS:
            return self.collect_greeting(company)
        if company in NAVER_COMPANIES:
            return self.collect_naver()
        return []

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> JobPostingCollector:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# BaseSource integration
# ---------------------------------------------------------------------------


@SourceRegistry.register
class CareerPagesSource(BaseSource):
    """실시간 채용 공고 수집 (Greenhouse / 네이버 / Greeting ATS)."""

    name = "career_pages"
    region = "kr"
    sections = ["job"]
    requires_api_key = False

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        with JobPostingCollector() as collector:
            postings = collector.collect_all(company)

        if not postings:
            return []

        total = len(postings)
        departments = sorted({p.department for p in postings if p.department})
        role_expectations = [_build_role_expectation(p) for p in postings[:50]]
        raw_lines = [f"채용 포지션 총 {total}개"]
        for p in postings[:30]:
            dept = f"[{p.department}] " if p.department else ""
            raw_lines.append(f"- {dept}{p.title}")

        return [
            SourceResult(
                source_name=self.name,
                section="job",
                data={
                    "total_positions": total,
                    "departments": departments,
                    "jobs": [
                        {
                            "title": p.title,
                            "url": p.url,
                            "location": p.location,
                            "department": p.department,
                            "employment_type": p.employment_type,
                            "posted_at": p.posted_at,
                            "description_snippet": p.description_snippet,
                        }
                        for p in postings[:50]
                    ],
                    "role_expectations": role_expectations,
                },
                confidence=0.9,
                raw="\n".join(raw_lines),
            )
        ]


def _extract_description_snippet(card: BeautifulSoup) -> str:
    return " ".join(card.stripped_strings)[:200]


def _has_title_class(class_name: str | None) -> bool:
    return bool(class_name and "title" in class_name.lower())


def _has_department_class(class_name: str | None) -> bool:
    return bool(class_name and any(kw in class_name.lower() for kw in ("department", "team", "category", "부서", "팀")))


def _build_role_expectation(posting: JobPosting) -> dict[str, Any]:
    expectations = _extract_role_expectations(posting)
    return {
        "title": posting.title,
        "department": posting.department,
        "expectations": expectations,
        "source_name": "career_pages",
        "source_authority": default_source_authority("career_pages"),
        "trust_label": "supporting" if expectations else "unknown",
    }


def _extract_role_expectations(posting: JobPosting) -> list[str]:
    text_candidates = [posting.description_snippet, posting.title, posting.department]
    expectations: list[str] = []

    for candidate in text_candidates:
        for part in _EXPECTATION_SPLIT_PATTERN.split(candidate):
            cleaned = re.sub(r"^[\-•·▪▶■\s]+", "", part).strip()
            if len(cleaned) < 4:
                continue
            if cleaned not in expectations:
                expectations.append(cleaned)

    return expectations[:5]
