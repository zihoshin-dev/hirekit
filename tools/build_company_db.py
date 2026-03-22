#!/usr/bin/env python3
"""DART API로 기업 기본 DB 구축."""
import json
import sys
import time
from pathlib import Path

import httpx

DART_KEY = "1aae86a4bbd44e49288456c8af6f5e8bd394a62c"
DART_URL = "https://opendart.fss.or.kr/api/company.json"

# company_resolver.py에서 _REGISTRY 가져오기
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from hirekit.core.company_resolver import _REGISTRY


def fetch_company(corp_code: str) -> dict:
    resp = httpx.get(
        DART_URL,
        params={"crtfc_key": DART_KEY, "corp_code": corp_code},
        timeout=10,
    )
    data = resp.json()
    if data.get("status") == "000":
        return {
            "corp_code": corp_code,
            "corp_name": data.get("corp_name", ""),
            "corp_name_eng": data.get("corp_name_eng", ""),
            "stock_name": data.get("stock_name", ""),
            "stock_code": data.get("stock_code", ""),
            "ceo_nm": data.get("ceo_nm", ""),
            "corp_cls": data.get("corp_cls", ""),
            "jurir_no": data.get("jurir_no", ""),
            "bizr_no": data.get("bizr_no", ""),
            "adres": data.get("adres", ""),
            "hm_url": data.get("hm_url", ""),
            "ir_url": data.get("ir_url", ""),
            "phn_no": data.get("phn_no", ""),
            "fax_no": data.get("fax_no", ""),
            "induty_code": data.get("induty_code", ""),
            "est_dt": data.get("est_dt", ""),
            "acc_mt": data.get("acc_mt", ""),
        }
    return {}


def main():
    db = {}
    # 중복 dart_code 처리: 이미 수집한 corp_code는 건너뜀
    seen_codes: set[str] = set()

    for name, info in _REGISTRY.items():
        if not info.dart_code:
            continue
        if info.dart_code in seen_codes:
            # 중복 (예: 토스/비바리퍼블리카) — 이미 수집한 데이터 재사용
            existing = next(
                (v for v in db.values() if v.get("corp_code") == info.dart_code), None
            )
            if existing:
                db[name] = existing
            continue

        print(f"Fetching {name} ({info.dart_code})...")
        data = fetch_company(info.dart_code)
        if data:
            db[name] = data
            print(f"  OK {data['corp_name']} / CEO: {data['ceo_nm']}")
        else:
            print(f"  FAIL No data")
        seen_codes.add(info.dart_code)
        time.sleep(0.5)  # Rate limit

    out_path = Path(__file__).parent.parent / "docs/demo/data/dart_company_db.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(db)} entries to {out_path}")


if __name__ == "__main__":
    main()
