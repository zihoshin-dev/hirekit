#!/usr/bin/env python3
"""워크넷 채용공고 데이터 수집.

워크넷 Open API (https://openapi.work.go.kr/opi/opi/opia/wantedApi.do)는
별도 워크넷 서비스 전용 인증키가 필요하며, 공공데이터포털 범용 키로는 인증 불가.

대안: 워크넷 웹 검색 + 사람인/잡코리아 공개 데이터 스크래핑으로 현재 채용공고 수집.
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode, quote, quote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).parent.parent
META_PATH = ROOT / "docs/demo/data/meta.json"
OUT_PATH = ROOT / "docs/demo/data/job_postings.json"

WORKNET_API_URL = "https://openapi.work.go.kr/opi/opi/opia/wantedApi.do"
SARAMIN_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
WORKNET_SEARCH_URL = "https://www.work.go.kr/empInfo/empInfoSrch/list/dtlEmpSrchList.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# ── 사람인 채용공고 스크래핑 ────────────────────────────────────────

def fetch_saramin_count(company_name: str) -> dict:
    """사람인에서 기업 채용공고 수 조회."""
    params = {
        "searchword": company_name,
        "recruitPage": "1",
        "recruitPageCount": "10",
        "recruitSort": "relation",
    }
    url = SARAMIN_URL + "?" + urlencode(params, quote_via=quote_plus)
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # 공고 수 패턴: "총 N건"
        count_match = re.search(r"총\s*([\d,]+)\s*건", html)
        total = int(count_match.group(1).replace(",", "")) if count_match else 0

        # 공고 제목 추출 (상위 5개)
        title_pattern = re.compile(
            r'class="[^"]*job_tit[^"]*"[^>]*>\s*<a[^>]*title="([^"]+)"', re.S
        )
        titles = title_pattern.findall(html)[:5]

        # 최근 공고 날짜
        date_pattern = re.compile(r"(\d{4}/\d{2}/\d{2})")
        dates = date_pattern.findall(html)
        recent_date = dates[0].replace("/", "-") if dates else None

        return {
            "active_job_postings": total,
            "recent_posting_date": recent_date,
            "hiring_positions": titles,
            "source": "saramin",
        }
    except (URLError, HTTPError, Exception) as e:
        return {
            "active_job_postings": None,
            "recent_posting_date": None,
            "hiring_positions": [],
            "source": "saramin",
            "error": str(e),
        }


def fetch_worknet_count(company_name: str) -> dict:
    """워크넷 웹에서 기업 채용공고 수 조회."""
    params = {
        "searchKeyword": company_name,
        "pageIndex": "1",
        "recordCountPerPage": "10",
    }
    url = WORKNET_SEARCH_URL + "?" + urlencode(params, quote_via=quote_plus)
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        count_match = re.search(r"총\s*([\d,]+)\s*(?:건|개)", html)
        total = int(count_match.group(1).replace(",", "")) if count_match else 0

        title_pattern = re.compile(r'class="[^"]*tit[^"]*"[^>]*>\s*<a[^>]*>([^<]+)</a>', re.S)
        titles = [t.strip() for t in title_pattern.findall(html) if t.strip()][:5]

        date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})")
        dates = date_pattern.findall(html)
        recent_date = dates[0] if dates else None

        return {
            "active_job_postings": total,
            "recent_posting_date": recent_date,
            "hiring_positions": titles,
            "source": "worknet",
        }
    except (URLError, HTTPError, Exception) as e:
        return {
            "active_job_postings": None,
            "recent_posting_date": None,
            "hiring_positions": [],
            "source": "worknet",
            "error": str(e),
        }


def fetch_job_postings(company_name: str) -> dict:
    """사람인 우선, 실패 시 워크넷 fallback."""
    result = fetch_saramin_count(company_name)
    if result.get("active_job_postings") is not None:
        return result

    time.sleep(0.5)
    return fetch_worknet_count(company_name)


def main():
    print("=== 워크넷/사람인 채용공고 데이터 수집 ===")

    with open(META_PATH, encoding="utf-8") as f:
        companies = json.load(f)

    print(f"대상 기업: {len(companies)}개")
    print("사람인 → 워크넷 순서로 채용공고 조회 (1초 간격)\n")

    results = {}
    for i, company in enumerate(companies):
        name = company["name"]
        print(f"  [{i+1:2d}/{len(companies)}] {name} ... ", end="", flush=True)

        data = fetch_job_postings(name)
        results[name] = data

        count = data.get("active_job_postings")
        src = data.get("source", "")
        if count is not None:
            print(f"{count}건 ({src})")
        else:
            err = data.get("error", "")[:40]
            print(f"실패 — {err}")

        time.sleep(1)  # rate limit

    # 통계
    success = sum(1 for v in results.values() if v.get("active_job_postings") is not None)
    total_postings = sum(
        v["active_job_postings"]
        for v in results.values()
        if v.get("active_job_postings") is not None
    )
    print(f"\n수집 결과:")
    print(f"  성공: {success}/{len(results)}개 기업")
    print(f"  총 채용공고: {total_postings}건")

    # 저장
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {OUT_PATH}")

    # meta.json 업데이트
    for company in companies:
        name = company["name"]
        if name in results:
            r = results[name]
            company["active_job_postings"] = r.get("active_job_postings")
            company["recent_posting_date"] = r.get("recent_posting_date")
            company["hiring_positions"] = r.get("hiring_positions", [])

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"meta.json 업데이트 완료 ({len(companies)}개 기업)")


if __name__ == "__main__":
    main()
