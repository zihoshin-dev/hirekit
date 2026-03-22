#!/usr/bin/env python3
"""DART API로 기업 기본 DB 구축 + 금융위/국세청 API로 추가 정보 수집."""
import json
import sys
import time
from pathlib import Path
from urllib.parse import unquote

import httpx

DART_KEY = "1aae86a4bbd44e49288456c8af6f5e8bd394a62c"
DART_URL = "https://opendart.fss.or.kr/api/company.json"

DATA_GO_KR_KEY = "j4f%2F4vYj4oKFfkbawHzuO8hsAoCfFRyXjlzi1DqaaTV0gliUd5f7vxh2U6%2FcM9vKzisMHpmv%2FZfQ2njSNXZFyQ%3D%3D"
FSC_URL = "https://apis.data.go.kr/1160100/service/GetCorpBasicInfoService_V2/getCorpOutline_V2"
NTS_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"

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


def fetch_fsc_corp(jurir_no: str) -> dict:
    """금융위 기업기본정보 API — 중소기업 여부, 주요사업, 직원수, 감사인."""
    if not jurir_no:
        return {}
    try:
        resp = httpx.get(
            FSC_URL,
            params={
                "serviceKey": unquote(DATA_GO_KR_KEY),
                "crno": jurir_no,
                "numOfRows": "1",
                "pageNo": "1",
                "resultType": "json",
            },
            timeout=15,
        )
        body = resp.json()
        items = (
            body.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )
        if not items:
            return {}
        item = items[0] if isinstance(items, list) else items
        return {
            "is_sme": item.get("smenpYn", ""),
            "main_business": item.get("enpMainBizNm", ""),
            "employee_count_fsc": item.get("enpEmpeCnt", ""),
            "auditor": item.get("actnAudpnNm", ""),
        }
    except Exception as e:
        print(f"  FSC API 실패 ({jurir_no}): {e}")
        return {}


def fetch_nts_biz(bizr_no: str) -> dict:
    """국세청 사업자 상태 API — 계속/휴업/폐업, 과세유형."""
    if not bizr_no:
        return {}
    b_no = bizr_no.replace("-", "").strip()
    try:
        resp = httpx.post(
            NTS_URL,
            params={"serviceKey": unquote(DATA_GO_KR_KEY)},
            headers={
                "Authorization": f"Infuser {unquote(DATA_GO_KR_KEY)}",
                "Content-Type": "application/json",
            },
            json={"b_no": [b_no]},
            timeout=15,
        )
        body = resp.json()
        data_list = body.get("data", [])
        if not data_list:
            return {}
        item = data_list[0]
        return {
            "biz_status": item.get("b_stt", ""),
            "tax_type": item.get("tax_type", ""),
        }
    except Exception as e:
        print(f"  NTS API 실패 ({bizr_no}): {e}")
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

        # 1. DART 기본 정보
        data = fetch_company(info.dart_code)
        if not data:
            print(f"  FAIL No DART data")
            seen_codes.add(info.dart_code)
            continue

        print(f"  DART OK {data['corp_name']} / CEO: {data['ceo_nm']}")
        time.sleep(0.5)

        # 2. 금융위 기업기본정보 (jurir_no 필요)
        jurir_no = data.get("jurir_no", "")
        if jurir_no:
            fsc_data = fetch_fsc_corp(jurir_no)
            if fsc_data:
                data.update(fsc_data)
                print(f"  FSC OK is_sme={fsc_data.get('is_sme')} emp={fsc_data.get('employee_count_fsc')}")
            time.sleep(0.5)

        # 3. 국세청 사업자 상태 (bizr_no 필요)
        bizr_no = data.get("bizr_no", "")
        if bizr_no:
            nts_data = fetch_nts_biz(bizr_no)
            if nts_data:
                data.update(nts_data)
                print(f"  NTS OK status={nts_data.get('biz_status')}")
            time.sleep(0.5)

        db[name] = data
        seen_codes.add(info.dart_code)

    out_path = Path(__file__).parent.parent / "docs/demo/data/dart_company_db.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(db)} entries to {out_path}")


if __name__ == "__main__":
    main()
