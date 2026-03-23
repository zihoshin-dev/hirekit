#!/usr/bin/env python3
"""계열사 데이터 정합성 감사.

docs/demo/data/companies/ 내 JSON 파일을 분석하여
모회사 데이터가 자회사에 혼입된 케이스를 탐지·보고한다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 계열사 그룹 정의
# ---------------------------------------------------------------------------

SUBSIDIARY_GROUPS: dict[str, dict[str, Any]] = {
    "카카오": {
        "parent": "카카오",
        "subsidiaries": [
            "카카오뱅크",
            "카카오페이",
            "카카오스타일",
            "카카오엔터테인먼트",
            "카카오페이증권",
        ],
    },
    "토스": {
        "parent": "비바리퍼블리카",
        "subsidiaries": ["토스뱅크", "토스증권", "토스페이먼츠", "토스랩"],
    },
    "네이버": {
        "parent": "네이버",
        "subsidiaries": [
            "네이버웹툰",
            "네이버클라우드",
            "네이버파이낸셜",
            "스노우",
            "라인플러스",
        ],
    },
}

# 파일명 매핑: 표준 이름 → JSON 파일명 (확장자 제외)
_FILE_MAP: dict[str, str] = {
    "카카오": "카카오",
    "카카오뱅크": "카카오뱅크",
    "카카오페이": "카카오페이",
    "카카오스타일": "카카오스타일",
    "카카오엔터테인먼트": "카카오엔터테인먼트",
    "카카오페이증권": "카카오페이증권",
    "비바리퍼블리카": "비바리퍼블리카",
    "토스": "토스",
    "토스뱅크": "토스뱅크",
    "토스증권": "토스증권",
    "토스페이먼츠": "토스페이먼츠",
    "토스랩": "토스랩",
    "네이버": "네이버",
    "네이버웹툰": "네이버웹툰",
    "네이버클라우드": "네이버클라우드",
    "네이버파이낸셜": "네이버파이낸셜",
    "스노우": "스노우",
    "라인플러스": "라인플러스",
}

_COMPANIES_DIR = (
    Path(__file__).parent.parent / "docs" / "demo" / "data" / "companies"
)


# ---------------------------------------------------------------------------
# 로더
# ---------------------------------------------------------------------------


def _load(name: str, companies_dir: Path) -> dict[str, Any] | None:
    fname = _FILE_MAP.get(name, name)
    path = companies_dir / f"{fname}.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _sec1(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("sections", {}).get("1", {})


def _sec7(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("sections", {}).get("7", {})


def _employees_total(sec1: dict[str, Any]) -> int:
    return sum(
        int(e.get("total", "0").replace(",", ""))
        for e in sec1.get("employees", [])
        if e.get("total")
    )


# ---------------------------------------------------------------------------
# 감사 함수들
# ---------------------------------------------------------------------------


def audit_dart_contamination(
    group_name: str,
    group_def: dict[str, Any],
    companies_dir: Path,
) -> list[dict[str, Any]]:
    """DART 섹션1 데이터(직원수·주소·회사명)가 자회사에 혼입된 케이스 탐지."""
    issues: list[dict[str, Any]] = []
    parent_name = group_def["parent"]
    parent_data = _load(parent_name, companies_dir)
    if parent_data is None:
        return issues

    parent_s1 = _sec1(parent_data)
    parent_corp_name = parent_s1.get("company_name", "")
    parent_emp_total = _employees_total(parent_s1)

    for sub_name in group_def["subsidiaries"]:
        sub_data = _load(sub_name, companies_dir)
        if sub_data is None:
            continue
        sub_s1 = _sec1(sub_data)
        sub_corp_name = sub_s1.get("company_name", "")
        sub_emp_total = _employees_total(sub_s1)

        # 회사명 오염: 섹션1의 company_name이 모회사와 동일
        if sub_corp_name and sub_corp_name == parent_corp_name:
            issues.append({
                "group": group_name,
                "company": sub_name,
                "issue_type": "dart_corp_name_contamination",
                "field": "sections.1.company_name",
                "found": sub_corp_name,
                "expected": f"{sub_name} 고유 DART 데이터",
                "severity": "high",
            })

        # 직원수 오염: 자회사의 직원수가 모회사와 동일
        if parent_emp_total > 0 and sub_emp_total == parent_emp_total:
            issues.append({
                "group": group_name,
                "company": sub_name,
                "issue_type": "employee_count_contamination",
                "field": "sections.1.employees",
                "found": sub_emp_total,
                "expected": f"{sub_name} 고유 직원수",
                "severity": "high",
            })

    return issues


def audit_news_contamination(
    group_name: str,
    group_def: dict[str, Any],
    companies_dir: Path,
) -> list[dict[str, Any]]:
    """뉴스 제목에 다른 계열사 이름이 포함된 케이스 탐지."""
    issues: list[dict[str, Any]] = []
    all_members = [group_def["parent"]] + group_def["subsidiaries"]

    for company_name in all_members:
        data = _load(company_name, companies_dir)
        if data is None:
            continue
        s1 = _sec1(data)
        news_items: list[dict[str, Any]] = s1.get("google_news", []) + s1.get(
            "recent_news", []
        )

        for idx, item in enumerate(news_items):
            title = item.get("title", "")
            # 다른 계열사 이름이 제목에 포함되어 있는지 확인
            for other in all_members:
                if other == company_name:
                    continue
                if other in title:
                    issues.append({
                        "group": group_name,
                        "company": company_name,
                        "issue_type": "news_subsidiary_mention",
                        "field": f"sections.1.google_news[{idx}].title",
                        "found": title[:80],
                        "mixed_with": other,
                        "severity": "medium",
                    })
                    break

    return issues


def audit_tech_blog_contamination(
    group_name: str,
    group_def: dict[str, Any],
    companies_dir: Path,
) -> list[dict[str, Any]]:
    """tech blog URL이 모회사 것으로 공유된 케이스 탐지."""
    issues: list[dict[str, Any]] = []
    parent_name = group_def["parent"]
    parent_data = _load(parent_name, companies_dir)
    if parent_data is None:
        return issues

    parent_blog_url = _sec7(parent_data).get("blog_url", "")
    if not parent_blog_url:
        return issues

    for sub_name in group_def["subsidiaries"]:
        sub_data = _load(sub_name, companies_dir)
        if sub_data is None:
            continue
        sub_blog_url = _sec7(sub_data).get("blog_url", "")
        if sub_blog_url and sub_blog_url == parent_blog_url:
            issues.append({
                "group": group_name,
                "company": sub_name,
                "issue_type": "tech_blog_url_shared",
                "field": "sections.7.blog_url",
                "found": sub_blog_url,
                "expected": f"{sub_name} 고유 기술 블로그 URL",
                "severity": "low",
            })

    return issues


def audit_meta_description_contamination(
    group_name: str,
    group_def: dict[str, Any],
    companies_dir: Path,
) -> list[dict[str, Any]]:
    """meta_description이 모회사 것으로 공유된 케이스 탐지."""
    issues: list[dict[str, Any]] = []
    parent_name = group_def["parent"]
    parent_data = _load(parent_name, companies_dir)
    if parent_data is None:
        return issues

    parent_meta_desc = _sec1(parent_data).get("meta_description", "")
    if not parent_meta_desc:
        return issues

    for sub_name in group_def["subsidiaries"]:
        sub_data = _load(sub_name, companies_dir)
        if sub_data is None:
            continue
        sub_meta_desc = _sec1(sub_data).get("meta_description", "")
        if sub_meta_desc and sub_meta_desc == parent_meta_desc:
            issues.append({
                "group": group_name,
                "company": sub_name,
                "issue_type": "meta_description_contamination",
                "field": "sections.1.meta_description",
                "found": sub_meta_desc[:60],
                "expected": f"{sub_name} 고유 meta_description",
                "severity": "medium",
            })

    return issues


# ---------------------------------------------------------------------------
# 전체 감사 실행
# ---------------------------------------------------------------------------


def run_audit(companies_dir: Path | None = None) -> dict[str, Any]:
    """모든 그룹에 대해 정합성 감사를 실행하고 결과를 반환한다."""
    if companies_dir is None:
        companies_dir = _COMPANIES_DIR

    all_issues: list[dict[str, Any]] = []

    for group_name, group_def in SUBSIDIARY_GROUPS.items():
        all_issues.extend(
            audit_dart_contamination(group_name, group_def, companies_dir)
        )
        all_issues.extend(
            audit_news_contamination(group_name, group_def, companies_dir)
        )
        all_issues.extend(
            audit_tech_blog_contamination(group_name, group_def, companies_dir)
        )
        all_issues.extend(
            audit_meta_description_contamination(group_name, group_def, companies_dir)
        )

    # 심각도 집계
    severity_counts: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for issue in all_issues:
        sev = issue.get("severity", "low")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "total_issues": len(all_issues),
        "severity_counts": severity_counts,
        "issues": all_issues,
    }


# ---------------------------------------------------------------------------
# CLI 진입점
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="계열사 데이터 정합성 감사")
    parser.add_argument(
        "--companies-dir",
        type=Path,
        default=_COMPANIES_DIR,
        help="companies JSON 디렉토리 경로",
    )
    parser.add_argument(
        "--output",
        choices=["summary", "json", "full"],
        default="summary",
        help="출력 형식",
    )
    args = parser.parse_args()

    result = run_audit(args.companies_dir)

    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n계열사 데이터 정합성 감사 결과")
    print(f"{'=' * 50}")
    print(f"총 이슈: {result['total_issues']}건")
    for sev, cnt in result["severity_counts"].items():
        print(f"  {sev}: {cnt}건")

    if args.output == "full" or result["total_issues"] > 0:
        print(f"\n{'─' * 50}")
        # 그룹별 출력
        by_group: dict[str, list[dict[str, Any]]] = {}
        for issue in result["issues"]:
            grp = issue["group"]
            by_group.setdefault(grp, []).append(issue)

        for grp, issues in by_group.items():
            print(f"\n[{grp} 그룹] {len(issues)}건")
            for iss in issues:
                sev_mark = {"high": "!!!", "medium": "!!", "low": "!"}.get(
                    iss["severity"], "!"
                )
                print(
                    f"  {sev_mark} [{iss['issue_type']}] {iss['company']}"
                    f" → {iss['field']}"
                )
                if args.output == "full":
                    print(f"     found: {iss['found']}")
                    if "expected" in iss:
                        print(f"     expected: {iss['expected']}")
                    if "mixed_with" in iss:
                        print(f"     mixed_with: {iss['mixed_with']}")


if __name__ == "__main__":
    main()
