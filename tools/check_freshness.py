#!/usr/bin/env python3
"""기업 데이터 신선도 체크."""

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "docs/demo/data/update_log.json"
META_PATH = ROOT / "docs/demo/data/meta.json"
QUALITY_REPORT_PATH = ROOT / "docs/demo/data/quality_report.json"


def load_meta() -> list[dict[str, object]]:
    if not META_PATH.exists():
        return []
    with open(META_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_update_log() -> dict[str, object]:
    if not LOG_PATH.exists():
        return {}
    with open(LOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_quality_report() -> dict[str, object]:
    if not QUALITY_REPORT_PATH.exists():
        return {}
    with open(QUALITY_REPORT_PATH, encoding="utf-8") as f:
        return json.load(f)


def refresh_quality_report() -> dict[str, object]:
    module_path = Path(__file__).with_name("verify_company_data.py")
    spec = importlib.util.spec_from_file_location("verify_company_data_module", module_path)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.verify_companies()
    if isinstance(report, dict):
        return report
    return {}


def build_freshness_contract(update_log: dict[str, object], *, meta_count: int) -> dict[str, object]:
    sources_updated = update_log.get("sources_updated", [])
    if not isinstance(sources_updated, list):
        sources_updated = []

    snapshot_source = str(update_log.get("source") or "snapshot")
    return {
        "dataset_mode": "public_snapshot",
        "publication_boundary": update_log.get("publication_boundary", "public_demo"),
        "snapshot_source": snapshot_source,
        "snapshot_updated_at": update_log.get("updated_at"),
        "cross_validated": bool(update_log.get("cross_validated", False)),
        "sources_updated": sources_updated,
        "snapshot_company_count": meta_count,
        "requires_live_dataset": False,
    }


def check_log(meta_count: int) -> tuple[int, list[str], dict[str, object]]:
    update_log = load_update_log()
    if not update_log:
        print("update_log.json 없음 — python tools/update_company_db.py 실행 필요")
        return 999, ["update_log.json 없음"], {}

    contract = build_freshness_contract(update_log, meta_count=meta_count)

    last_update = datetime.fromisoformat(str(update_log["updated_at"]))
    age_days = (datetime.now() - last_update).days
    issues: list[str] = []

    sources_updated = contract.get("sources_updated", [])
    if not isinstance(sources_updated, list):
        sources_updated = []
    snapshot_company_count = contract.get("snapshot_company_count", meta_count)
    if not isinstance(snapshot_company_count, int):
        snapshot_company_count = meta_count

    print(f"마지막 스냅샷 갱신: {contract['snapshot_updated_at']} ({age_days}일 전)")
    print(f"공개 경계: {contract['publication_boundary']}")
    print(f"데이터 모드: {contract['dataset_mode']} / 소스: {contract['snapshot_source']}")
    print(f"갱신된 항목: {', '.join(str(item) for item in sources_updated) or '없음'}")
    print(f"스냅샷 기업 수: {snapshot_company_count}")

    if update_log.get("companies_updated") != meta_count:
        issues.append(f"update_log 기업 수 불일치: {update_log.get('companies_updated')} != {meta_count}")
    if not update_log.get("sources_updated"):
        issues.append("sources_updated 비어 있음")
    if update_log.get("publication_boundary") != "public_demo":
        issues.append("publication_boundary 누락 또는 public_demo 아님")
    if not isinstance(update_log.get("cross_validated"), bool):
        issues.append("cross_validated 플래그 누락")
    if contract.get("dataset_mode") != "public_snapshot":
        issues.append("dataset_mode 이 public_snapshot 이 아님")

    if update_log.get("errors"):
        errors = update_log.get("errors", [])
        if not isinstance(errors, list):
            errors = []
        print(f"이전 갱신 오류: {len(errors)}건")
        for e in errors[:5]:
            print(f"  - {e}")

    if age_days > 30:
        print("\n⚠️  30일 이상 미갱신 — python tools/update_company_db.py 실행 권장")
    elif age_days > 7:
        print("\nℹ️  7일 이상 — 시장 데이터 갱신 권장")
    else:
        print("\n✅ 데이터 최신 상태")

    if issues:
        print("\n⚠️  로그 계약 이슈:")
        for issue in issues:
            print(f"  - {issue}")

    return age_days, issues, contract


def check_quality_report(
    meta_count: int,
    contract: dict[str, object],
    report: dict[str, object] | None = None,
) -> list[str]:
    if report is None:
        report = load_quality_report()

    if not report:
        return ["quality_report.json 없음"]

    issues: list[str] = []

    total_companies = report.get("total_companies")
    if total_companies != meta_count:
        issues.append(f"quality_report total_companies 불일치: {total_companies} != {meta_count}")

    report_governance = report.get("governance", {})
    if not isinstance(report_governance, dict):
        issues.append("quality_report governance 누락")
        return issues

    contract_dataset_mode = contract.get("dataset_mode")
    contract_publication_boundary = contract.get("publication_boundary")
    contract_snapshot_source = contract.get("snapshot_source")

    if report_governance.get("dataset_mode") != contract_dataset_mode:
        issues.append("quality_report dataset_mode 이 snapshot contract 와 불일치")
    if report_governance.get("publication_boundary") != contract_publication_boundary:
        issues.append("quality_report publication_boundary 불일치")
    if report_governance.get("snapshot_source") != contract_snapshot_source:
        issues.append("quality_report snapshot_source 불일치")

    return issues


def check_meta() -> list[str]:
    """개별 기업 데이터 품질 체크. 이슈 목록 반환."""
    if not META_PATH.exists():
        print("meta.json 없음")
        return ["meta.json 없음"]

    companies = load_meta()

    print(f"\n기업 수: {len(companies)}개")

    issues: list[str] = []
    for c in companies:
        name = c.get("name", "unknown")
        if not c.get("ceo"):
            issues.append(f"{name}: CEO 정보 없음")
        if not c.get("core_business"):
            issues.append(f"{name}: 핵심 사업 정보 없음")
        if not c.get("key_metrics"):
            issues.append(f"{name}: 핵심 지표 없음")
        if not c.get("description"):
            issues.append(f"{name}: 설명 없음")
        if not c.get("tech_stack"):
            issues.append(f"{name}: 기술 스택 정보 없음")

    if issues:
        print(f"\n⚠️  데이터 품질 이슈 {len(issues)}건:")
        for i in issues[:10]:
            print(f"  {i}")
        if len(issues) > 10:
            print(f"  ... 외 {len(issues) - 10}건")
    else:
        print("✅ 모든 기업 데이터 품질 정상")

    return issues


def main() -> None:
    print("=" * 50)
    print("HireKit 데이터 신선도 체크")
    print("=" * 50)

    companies = load_meta()
    age_days, log_issues, contract = check_log(meta_count=len(companies))
    quality_report = load_quality_report()
    quality_report_issues = check_quality_report(len(companies), contract, quality_report)
    if quality_report_issues:
        print("quality_report.json 갱신 중...")
        quality_report = refresh_quality_report()
        quality_report_issues = check_quality_report(len(companies), contract, quality_report)
    issues = check_meta()

    print("\n" + "=" * 50)
    if log_issues or quality_report_issues:
        print("상태: 스냅샷 계약 점검 필요")
    elif age_days > 30:
        print("상태: 스냅샷은 오래됐지만 공개 데모는 정상")
    elif age_days > 7:
        print("상태: 스냅샷 최신성 주의")
    else:
        print("상태: 공개 스냅샷 정상")

    if issues:
        print(f"검토용 데이터 품질 이슈: {len(issues)}건")
    sys.exit(1 if log_issues or quality_report_issues else 0)


if __name__ == "__main__":
    main()
