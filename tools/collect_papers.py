#!/usr/bin/env python3
"""Semantic Scholar API로 기업별 AI 논문 수집 (최근 3년)."""
import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "docs/demo/data/papers_metrics.json"

S2_BASE = "https://api.semanticscholar.org/graph/v1"

# 탑 AI 컨퍼런스/저널
TOP_VENUES = {"NeurIPS", "ICML", "ICLR", "CVPR", "ECCV", "ICCV", "ACL", "EMNLP",
              "NAACL", "AAAI", "IJCAI", "KDD", "WWW", "SIGIR", "WSDM", "RecSys",
              "INTERSPEECH", "ICASSP", "TACL", "JMLR"}

# 기업명 → 검색 쿼리 매핑
COMPANY_QUERIES: dict[str, list[str]] = {
    "네이버": ["NAVER AI", "NAVER CLOVA"],
    "카카오": ["Kakao AI", "KakaoBrain"],
    "SK텔레콤": ["SK Telecom AI"],
    "업스테이지": ["Upstage AI"],
    "LG전자": ["LG AI Research"],
    "삼성전자": ["Samsung AI", "Samsung Research AI"],
    "리벨리온": ["Rebellions AI"],
    "뤼튼": ["Riiid AI"],
    "현대자동차": ["Hyundai AI Research"],
    "SK하이닉스": ["SK Hynix AI"],
}

# 수집 기준 연도 (최근 3년)
import datetime
CURRENT_YEAR = datetime.date.today().year
MIN_YEAR = CURRENT_YEAR - 3


def search_papers(query: str, client: httpx.Client, retries: int = 3) -> list[dict]:
    """단일 쿼리로 논문 검색. 429 시 지수 백오프 재시도."""
    params = {
        "query": query,
        "limit": 50,
        "fields": "title,year,venue,citationCount,externalIds",
    }
    for attempt in range(retries):
        try:
            resp = client.get(f"{S2_BASE}/paper/search", params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
            elif resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    [s2 rate limit] {query!r} — {wait}s 대기")
                time.sleep(wait)
            else:
                print(f"    [s2 error] {query!r}: HTTP {resp.status_code}")
                break
        except Exception as e:
            print(f"    [s2 exception] {query!r}: {e}")
            time.sleep(2)
    return []


def filter_recent(papers: list[dict]) -> list[dict]:
    """MIN_YEAR 이후 논문만 반환."""
    return [p for p in papers if (p.get("year") or 0) >= MIN_YEAR]


def extract_venue(paper: dict) -> str:
    """venue 문자열 추출 (없으면 빈 문자열)."""
    return (paper.get("venue") or "").strip()


def get_top_venues(papers: list[dict]) -> list[str]:
    """탑 컨퍼런스 중 실제 발표된 venue 목록 반환 (중복 제거, 빈도순)."""
    venue_counts: dict[str, int] = {}
    for p in papers:
        venue = extract_venue(p)
        for tv in TOP_VENUES:
            if tv.lower() in venue.lower():
                venue_counts[tv] = venue_counts.get(tv, 0) + 1
                break
    return sorted(venue_counts, key=venue_counts.__getitem__, reverse=True)


def get_top_papers(papers: list[dict], n: int = 3) -> list[dict]:
    """인용수 기준 상위 n개 논문 반환."""
    sorted_papers = sorted(papers, key=lambda p: p.get("citationCount") or 0, reverse=True)
    result = []
    for p in sorted_papers[:n]:
        result.append({
            "title": p.get("title", ""),
            "year": p.get("year"),
            "venue": extract_venue(p),
            "citations": p.get("citationCount") or 0,
        })
    return result


def fetch_company_papers(company: str, queries: list[str], client: httpx.Client) -> dict:
    """기업별 논문 지표 수집 (여러 쿼리 합산, 중복 제거)."""
    print(f"  {company}: {queries}")
    all_papers: dict[str, dict] = {}  # paper_id → paper (중복 제거)

    for query in queries:
        papers = search_papers(query, client)
        recent = filter_recent(papers)
        for p in recent:
            pid = p.get("paperId") or p.get("title", "")
            if pid and pid not in all_papers:
                all_papers[pid] = p
        time.sleep(1.5)  # Rate limit: 100 req/5분 → ~1.2req/s 이하 유지

    papers_list = list(all_papers.values())
    total_citations = sum(p.get("citationCount") or 0 for p in papers_list)
    top_venues = get_top_venues(papers_list)
    top_papers = get_top_papers(papers_list)

    print(
        f"    -> papers={len(papers_list)}, citations={total_citations}, "
        f"venues={top_venues[:3]}"
    )

    return {
        "paper_count": len(papers_list),
        "top_venues": top_venues,
        "total_citations": total_citations,
        "top_papers": top_papers,
    }


def main() -> None:
    results: dict[str, dict] = {}

    print(f"수집 기준: {MIN_YEAR}년 이후 AI 논문\n")

    with httpx.Client() as client:
        for company, queries in COMPANY_QUERIES.items():
            results[company] = fetch_company_papers(company, queries, client)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUT_PATH} ({len(results)}개 기업)")


if __name__ == "__main__":
    main()
