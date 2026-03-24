#!/usr/bin/env python3
"""79개 기업 데이터 검증 + _meta 필드 표준화."""

import importlib.util
import json
import os
import re
import sys
from datetime import UTC, datetime

COMPANIES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "companies"
)
META_JSON = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "meta.json"
)
PENSION_JSON = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "pension_data.json"
)
V2_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "v2_reports")
QUALITY_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "demo", "data", "quality_report.json"
)

REQUIRED_FIELDS = {"company", "region", "sections", "scorecard"}
SCORECARD_DIMENSIONS = {"job_fit", "career_leverage", "growth", "compensation", "culture_fit"}
SCORE_RANGE = (0, 5)


def _parse_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d-]", "", value)
        if digits:
            try:
                return int(digits)
            except ValueError:
                return None
    return None


def _section_employee_total(data):
    section = data.get("sections", {}).get("1", {})
    employees = section.get("employees", [])
    if not isinstance(employees, list) or not employees:
        return None

    total = 0
    found = False
    for employee in employees:
        if not isinstance(employee, dict):
            continue
        count = _parse_int(employee.get("total"))
        if count is None:
            headcount = _parse_int(employee.get("headcount"))
            contract_workers = _parse_int(employee.get("contract_workers")) or 0
            if headcount is not None:
                count = headcount + contract_workers
        if count is None:
            continue
        total += count
        found = True
    return total if found else None


def extract_employee_signals(data, meta_record=None, pension_record=None):
    signals = {}
    section_total = _section_employee_total(data)
    if section_total is not None:
        signals["sections.1.employees"] = section_total

    financial_deep = data.get("financial_deep", {})
    if isinstance(financial_deep, dict):
        employee_total = _parse_int(financial_deep.get("employee_total"))
        if employee_total is not None:
            signals["financial_deep.employee_total"] = employee_total

    employee_count = _parse_int(data.get("employee_count"))
    if employee_count is not None:
        signals["employee_count"] = employee_count

    pension_members = _parse_int(data.get("pension_members"))
    if pension_members is not None:
        signals["pension_members"] = pension_members

    if isinstance(meta_record, dict):
        meta_employee_count = _parse_int(meta_record.get("employee_count"))
        if meta_employee_count is not None:
            signals["meta.employee_count"] = meta_employee_count

        meta_pension_members = _parse_int(meta_record.get("pension_members"))
        if meta_pension_members is not None:
            signals["meta.pension_members"] = meta_pension_members

    if isinstance(pension_record, dict):
        external_pension_members = _parse_int(pension_record.get("pension_members"))
        if external_pension_members is not None:
            signals["pension_data.pension_members"] = external_pension_members

    return signals


def build_employee_consistency_issues(company_name, data, meta_record=None, pension_record=None):
    issues = []
    signals = extract_employee_signals(
        data,
        meta_record=meta_record,
        pension_record=pension_record,
    )

    contaminated_from = data.get("sections", {}).get("1", {}).get("_dart_contaminated_from")
    if contaminated_from and "sections.1.employees" in signals:
        issues.append({
            "company": company_name,
            "issue": (
                f"직원수 오염 가능성: sections.1.employees 가 "
                f"'{contaminated_from}' DART 데이터와 혼입된 표시가 있음"
            ),
            "issue_type": "employee_count_contamination_flag",
            "severity": "high",
            "signals": signals,
        })

    counts = list(signals.values())
    if len(counts) < 2:
        return issues

    min_count = min(counts)
    max_count = max(counts)
    spread = max_count - min_count
    baseline = max(1, min_count)
    spread_ratio = spread / baseline

    if spread >= 100 and spread_ratio >= 0.35:
        severity = "high"
    elif spread >= 50 and spread_ratio >= 0.15:
        severity = "medium"
    else:
        severity = ""

    if severity:
        issues.append({
            "company": company_name,
            "issue": (
                f"직원수 신호 불일치: 최소 {min_count:,}명, 최대 {max_count:,}명 "
                f"(차이 {spread:,}명, {spread_ratio:.0%})"
            ),
            "issue_type": "employee_count_inconsistency",
            "severity": severity,
            "signals": signals,
        })

    return issues


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_subsidiary_audit_runner():
    tools_dir = os.path.dirname(__file__)
    module_path = os.path.join(tools_dir, "audit_subsidiaries.py")
    spec = importlib.util.spec_from_file_location(
        "audit_subsidiaries_module",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load audit_subsidiaries.py from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_audit


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
    meta_map = {
        entry.get("name"): entry
        for entry in meta
        if isinstance(entry, dict) and entry.get("name")
    }
    pension_map = load_json(PENSION_JSON) if os.path.exists(PENSION_JSON) else {}
    meta_count = len(meta)
    print(f"[2] meta.json 기업 수: {meta_count}")
    if file_count != meta_count:
        issues.append({
            "company": "__global__",
            "issue": f"companies/ 파일 수({file_count}) != meta.json 기업 수({meta_count})",
            "severity": "high",
        })
        print("    WARNING: 불일치 감지")

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

        company_issues.extend(
            build_employee_consistency_issues(
                company_name,
                data,
                meta_record=meta_map.get(company_name),
                pension_record=pension_map.get(company_name),
            )
        )

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

    # 6.5 계열사 contamination audit 통합
    subsidiary_audit = load_subsidiary_audit_runner()()
    for issue in subsidiary_audit["issues"]:
        issues.append({
            "company": issue["company"],
            "issue": f"{issue['issue_type']} at {issue['field']}",
            "issue_type": issue["issue_type"],
            "severity": issue["severity"],
            "group": issue["group"],
            "found": issue.get("found"),
            "expected": issue.get("expected"),
        })

    # 7. 결과 출력 + JSON 리포트 저장
    verified_at = datetime.now(UTC).isoformat()
    employee_issue_count = sum(
        1 for issue in issues if str(issue.get("issue_type", "")).startswith("employee_count_")
    )
    summary = {
        "complete": complete,
        "partial": partial,
        "incomplete": incomplete,
        "employee_consistency_issues": employee_issue_count,
    }

    report = {
        "total_companies": file_count,
        "verified_at": verified_at,
        "issues": issues,
        "summary": summary,
        "subsidiary_audit": subsidiary_audit,
    }

    with open(QUALITY_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n[결과 요약]")
    print(f"  완전: {complete}개 | 부분: {partial}개 | 불완전: {incomplete}개")
    print(f"  이슈 총 {len(issues)}건")
    print(f"  직원수 정합성 이슈: {employee_issue_count}건")
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
