#!/usr/bin/env python3
"""DART DB 기준으로 meta.json 기본 정보 동기화."""
import json
from pathlib import Path


def _match_dart(name: str, dart_db: dict) -> dict | None:
    """meta.json 기업명을 dart_db 키와 매칭."""
    # 1. 직접 키 매칭
    if name in dart_db:
        return dart_db[name]

    # 2. 부분 문자열 매칭 (양방향)
    name_norm = name.replace(" ", "").lower()
    for key, val in dart_db.items():
        key_norm = key.replace(" ", "").lower()
        if name_norm in key_norm or key_norm in name_norm:
            return val

        # corp_name 필드로도 매칭 시도
        corp_name_norm = val.get("corp_name", "").replace(" ", "").lower()
        if corp_name_norm and (name_norm in corp_name_norm or corp_name_norm in name_norm):
            return val

    return None


def sync():
    base = Path(__file__).parent.parent / "docs/demo/data"
    dart_db_path = base / "dart_company_db.json"
    meta_path = base / "meta.json"

    if not dart_db_path.exists():
        print(f"ERROR: {dart_db_path} 없음. build_company_db.py를 먼저 실행하세요.")
        return

    with open(dart_db_path, encoding="utf-8") as f:
        dart_db = json.load(f)
    with open(meta_path, encoding="utf-8") as f:
        companies = json.load(f)

    changes = []
    ceo_warnings = []

    for company in companies:
        name = company["name"]
        dart = _match_dart(name, dart_db)

        if not dart:
            continue

        # 법인명 동기화 (DART corp_name 추가)
        if dart.get("corp_name") and company.get("corp_name") != dart["corp_name"]:
            old = company.get("corp_name", "(없음)")
            company["corp_name"] = dart["corp_name"]
            changes.append(f"{name}: corp_name '{old}' → '{dart['corp_name']}'")

        # 설립일 동기화
        if dart.get("est_dt"):
            try:
                est_year = int(dart["est_dt"][:4])
                if company.get("founded_year") != est_year:
                    old = company.get("founded_year", "(없음)")
                    changes.append(f"{name}: founded_year {old} → {est_year}")
                    company["founded_year"] = est_year
            except (ValueError, IndexError):
                pass

        # 주소 동기화 (DART 기준)
        if dart.get("adres"):
            old_addr = company.get("address", "")
            if old_addr != dart["adres"]:
                company["address"] = dart["adres"]
                changes.append(f"{name}: address 갱신 ('{dart['adres'][:30]}...')")

        # 홈페이지 (기존에 없을 때만)
        if dart.get("hm_url") and not company.get("homepage"):
            company["homepage"] = dart["hm_url"]
            changes.append(f"{name}: homepage 추가 '{dart['hm_url']}'")

        # 종목코드 동기화
        if dart.get("stock_code") and not company.get("stock_code"):
            company["stock_code"] = dart["stock_code"]
            changes.append(f"{name}: stock_code 추가 '{dart['stock_code']}'")

        # CEO 정보 — 자동 수정하지 않고 경고만 (DART 등기임원 vs 실제 대표 차이 가능)
        if dart.get("ceo_nm") and company.get("ceo") != dart["ceo_nm"]:
            ceo_warnings.append(
                f"[확인필요] {name}: meta.json CEO='{company.get('ceo', '(없음)')}' / "
                f"DART CEO='{dart['ceo_nm']}'"
            )

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"\n=== 동기화 완료: {len(changes)}건 변경 ===")
    for c in changes:
        print(f"  {c}")

    if ceo_warnings:
        print(f"\n=== CEO 불일치 확인 필요: {len(ceo_warnings)}건 ===")
        for w in ceo_warnings:
            print(f"  {w}")

    print(f"\nmeta.json 저장 완료: {meta_path}")


if __name__ == "__main__":
    sync()
