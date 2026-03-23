#!/usr/bin/env python3
"""79개 기업 데이터 검증 + _meta 필드 표준화."""

import json
import os
import sys
from datetime import datetime, timezone

COMPANIES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "companies"
)
META_JSON = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "meta.json"
)
V2_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "v2_reports")
QUALITY_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "quality_report.json"
)

REQUIRED_FIELDS = {"company", "region", "sections", "scorecard"}
SCORECARD_DIMENSIONS = {"job_fit", "career_leverage", "growth", "compensation", "culture_fit"}
SCORE_RANGE = (0, 5)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def verify_companies():
    issues = []
    companies_path = os.path.abspath(COMPANIES_DIR)

    # 1. companies/ 파일 목록
    json_files = sorted(
        f for f in os.listdir(companies_path) if f.endswith(".json")
    )
    file_count = len(json_files)
    print(f"[1] companies/ JSON 파일 수: {file_count}")

    # 2. meta.json 기업 수
    meta = load_json(META_JSON)
    meta_count = len(meta)
    print(f"[2] meta.json 기업 수: {meta_count}")
    if file_count != meta_count:
        issues.append({
            "company": "__global__",
            "issue": f"companies/ 파일 수({file_count}) != meta.json 기업 수({meta_count})",
            "severity": "high",
        })
        print(f"    WARNING: 불일치 감지")

    # 3-5. 각 JSON 검증
    complete = 0
    partial = 0
    incomplete = 0

    for fname in json_files:
        fpath = os.path.join(companies_path, fname)
        company_name = fname.replace(".json", "")
        company_issues = []

        try:
            data = load_json(fpath)
        except json.JSONDecodeError as e:
            issues.append({
                "company": company_name,
                "issue": f"JSON 파싱 오류: {e}",
                "severity": "high",
            })
            incomplete += 1
            continue

        # 3. 필수 필드
        missing_fields = REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            for field in missing_fields:
                company_issues.append({
                    "company": company_name,
                    "issue": f"missing field: {field}",
                    "severity": "high",
                })

        # 4. scorecard 5차원 점수 범위 검증
        scorecard = data.get("scorecard", {})
        dimensions = scorecard.get("dimensions", [])
        dim_names = {d["name"] for d in dimensions if isinstance(d, dict)}
        missing_dims = SCORECARD_DIMENSIONS - dim_names
        if missing_dims:
            company_issues.append({
                "company": company_name,
                "issue": f"missing scorecard dimensions: {missing_dims}",
                "severity": "medium",
            })
        for dim in dimensions:
            if not isinstance(dim, dict):
                continue
            score = dim.get("score")
            name = dim.get("name", "unknown")
            if score is not None and not (SCORE_RANGE[0] <= score <= SCORE_RANGE[1]):
                company_issues.append({
                    "company": company_name,
                    "issue": f"scorecard.{name}.score={score} out of range {SCORE_RANGE}",
                    "severity": "medium",
                })

        # 5. sections 키가 숫자(문자열)인지
        sections = data.get("sections", {})
        if isinstance(sections, dict):
            for key in sections.keys():
                if not key.isdigit():
                    company_issues.append({
                        "company": company_name,
                        "issue": f"sections key '{key}' is not numeric",
                        "severity": "low",
                    })

        issues.extend(company_issues)

        # 완성도 분류
        if not company_issues:
            complete += 1
        elif any(i["severity"] == "high" for i in company_issues):
            incomplete += 1
        else:
            partial += 1

    # 6. v2_reports 기업명 일치 여부
    v2_path = os.path.abspath(V2_REPORTS_DIR)
    if os.path.isdir(v2_path):
        v2_files = {f.replace(".json", "") for f in os.listdir(v2_path) if f.endswith(".json")}
        companies_set = {f.replace(".json", "") for f in json_files}
        only_in_v2 = v2_files - companies_set
        only_in_companies = companies_set - v2_files
        if only_in_v2:
            issues.append({
                "company": "__global__",
                "issue": f"v2_reports에만 있는 기업: {sorted(only_in_v2)}",
                "severity": "low",
            })
        if only_in_companies:
            issues.append({
                "company": "__global__",
                "issue": f"companies/에만 있는 기업 (v2_reports 없음): {sorted(only_in_companies)}",
                "severity": "low",
            })
        print(f"[6] v2_reports JSON: {len(v2_files)}개, companies/: {len(companies_set)}개")
    else:
        print(f"[6] v2_reports 디렉토리 없음: {v2_path}")

    # 7. 결과 출력 + JSON 리포트 저장
    verified_at = datetime.now(timezone.utc).isoformat()
    summary = {"complete": complete, "partial": partial, "incomplete": incomplete}

    report = {
        "total_companies": file_count,
        "verified_at": verified_at,
        "issues": issues,
        "summary": summary,
    }

    with open(QUALITY_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n[결과 요약]")
    print(f"  완전: {complete}개 | 부분: {partial}개 | 불완전: {incomplete}개")
    print(f"  이슈 총 {len(issues)}건")
    if issues:
        high = [i for i in issues if i["severity"] == "high"]
        medium = [i for i in issues if i["severity"] == "medium"]
        low = [i for i in issues if i["severity"] == "low"]
        print(f"  HIGH: {len(high)}, MEDIUM: {len(medium)}, LOW: {len(low)}")
    print(f"  리포트 저장: {QUALITY_REPORT_PATH}")

    return report


if __name__ == "__main__":
    report = verify_companies()
    has_high = any(i["severity"] == "high" for i in report["issues"]
                   if i["company"] != "__global__")
    sys.exit(1 if has_high else 0)
