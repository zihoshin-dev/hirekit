#!/usr/bin/env python3
"""기업 데이터 신선도 체크."""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG_PATH = ROOT / "docs/demo/data/update_log.json"
META_PATH = ROOT / "docs/demo/data/meta.json"


def check_log() -> int:
    """갱신 이력 확인. 경과 일수 반환."""
    if not LOG_PATH.exists():
        print("update_log.json 없음 — python tools/update_company_db.py 실행 필요")
        return 999

    with open(LOG_PATH, encoding="utf-8") as f:
        log = json.load(f)

    last_update = datetime.fromisoformat(log["updated_at"])
    age_days = (datetime.now() - last_update).days

    print(f"마지막 갱신: {log['updated_at']} ({age_days}일 전)")
    print(f"갱신된 소스: {', '.join(log.get('sources_updated', []))}")
    print(f"갱신 기업 수: {log.get('companies_updated', 'N/A')}")

    if log.get("errors"):
        print(f"이전 갱신 오류: {len(log['errors'])}건")
        for e in log["errors"][:5]:
            print(f"  - {e}")

    if age_days > 30:
        print("\n⚠️  30일 이상 미갱신 — python tools/update_company_db.py 실행 권장")
    elif age_days > 7:
        print("\nℹ️  7일 이상 — 시장 데이터 갱신 권장")
    else:
        print("\n✅ 데이터 최신 상태")

    return age_days


def check_meta() -> list[str]:
    """개별 기업 데이터 품질 체크. 이슈 목록 반환."""
    if not META_PATH.exists():
        print("meta.json 없음")
        return ["meta.json 없음"]

    with open(META_PATH, encoding="utf-8") as f:
        companies = json.load(f)

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

    age_days = check_log()
    issues = check_meta()

    print("\n" + "=" * 50)
    if age_days > 30 or len(issues) > 5:
        print("상태: 갱신 필요")
        sys.exit(1)
    elif age_days > 7 or issues:
        print("상태: 부분 갱신 권장")
        sys.exit(0)
    else:
        print("상태: 정상")
        sys.exit(0)


if __name__ == "__main__":
    main()
