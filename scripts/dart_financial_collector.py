#!/usr/bin/env python3
"""DART API로 재무제표 + 직원현황 수집 후 meta.json financial_deep 필드 업데이트"""

import json
import time
import httpx

DART_KEY = "1aae86a4bbd44e49288456c8af6f5e8bd394a62c"
BASE_URL = "https://opendart.fss.or.kr/api"

DATA_DIR = "docs/demo/data"
DART_DB_PATH = f"{DATA_DIR}/dart_company_db.json"
META_PATH = f"{DATA_DIR}/meta.json"

# meta.json 기업명 -> dart_company_db.json 기업명 매핑
META_TO_DART = {
    "CJ ENM": "CJ ENM",
    "SK하이닉스": "SK하이닉스",
    "네이버": "네이버",
    "네이버웹툰": "네이버웹툰",
    "네이버클라우드": "네이버클라우드",
    "당근": "당근",
    "두나무": "두나무",
    "라인플러스": "라인플러스",
    "뤼튼": "뤼튼",
    "무신사": "무신사",
    "삼성SDS": "삼성SDS",
    "삼성전자": "삼성전자",
    "야놀자": "야놀자",
    "우아한형제들": "우아한형제들",
    "카카오": "카카오",
    "카카오뱅크": "카카오뱅크",
    "카카오엔터테인먼트": "카카오엔터테인먼트",
    "카카오페이": "카카오페이",
    "쿠팡": "쿠팡",
    "토스뱅크": "토스뱅크",
    "토스증권": "토스증권",
    "토스 (비바리퍼블리카)": "비바리퍼블리카",
}

# 핵심 계정과목 -> account_nm 패턴 (OFS 단독재무제표 기준, 우선순위 순)
ACCOUNT_MAP = {
    "revenue": ["매출액", "수익(매출액)", "영업수익", "순영업수익"],
    "operating_profit": ["영업이익", "영업이익(손실)"],
    "net_income": ["당기순이익", "당기순이익(손실)", "분기순이익", "반기순이익"],
    "total_assets": ["자산총계"],
    "total_debt": ["부채총계"],
    "total_equity": ["자본총계"],
}

REPRT_CODES = {
    "11011": "사업보고서",   # 연간
}


def fetch_financial(corp_code: str, year: str) -> dict:
    """단일 연도 재무제표 수집 (BS 행 우선, 중복 시 BS 덮어쓰기)"""
    try:
        resp = httpx.get(
            f"{BASE_URL}/fnlttSinglAcntAll.json",
            params={
                "crtfc_key": DART_KEY,
                "corp_code": corp_code,
                "bsns_year": year,
                "reprt_code": "11011",
                "fs_div": "OFS",
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") == "000" and data.get("list"):
            result = {}
            for item in data["list"]:
                nm = item["account_nm"]
                sj_div = item.get("sj_div", "")
                # 아직 없거나, BS(재무상태표) 행이면 우선 저장
                if nm not in result or sj_div == "BS":
                    result[nm] = item
            return result
        return {}
    except Exception as e:
        print(f"  재무제표 오류 ({corp_code}, {year}): {e}")
        return {}


def fetch_employee(corp_code: str, year: str = "2024") -> dict:
    """직원현황 수집"""
    try:
        resp = httpx.get(
            f"{BASE_URL}/empSttus.json",
            params={
                "crtfc_key": DART_KEY,
                "corp_code": corp_code,
                "bsns_year": year,
                "reprt_code": "11011",
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") == "000" and data.get("list"):
            return data["list"]
        return []
    except Exception as e:
        print(f"  직원현황 오류 ({corp_code}, {year}): {e}")
        return []


def parse_amount(account_items: dict, keys: list) -> int | None:
    """계정명 리스트 중 매칭되는 첫 번째 금액 반환 (단위: 원)

    DART 일부 기업은 계정명 앞에 로마자 번호 접두사가 붙음 (예: 'Ⅰ. 매출액').
    exact match 후 suffix match로 fallback.
    """
    def extract_amount(item: dict) -> int | None:
        raw = item.get("thstrm_amount", "").replace(",", "").strip()
        if raw == "-":
            raw = "0"
        if raw:
            try:
                return int(raw)
            except ValueError:
                pass
        return None

    # 1차: exact match
    for key in keys:
        if key in account_items:
            amt = extract_amount(account_items[key])
            if amt is not None:
                return amt

    # 2차: suffix match (로마자/숫자 접두사 대응 — 예: 'Ⅰ. 매출액', 'I. 영업수익')
    # ". {key}" 패턴만 허용하여 '5. 기타의영업수익' 같은 부분 매칭 방지
    for key in keys:
        for nm, item in account_items.items():
            if nm == f". {key}" or nm.endswith(f". {key}"):
                # 접두사가 단순 로마자/알파벳/숫자인지 확인 (복합 계정명 제외)
                prefix = nm[: -(len(key) + 2)]  # '. ' 제외한 접두사
                if prefix and all(c not in prefix for c in ['가', '나', '다', '의', '기']):
                    amt = extract_amount(item)
                    if amt is not None:
                        return amt

    return None


def parse_employee_data(emp_list: list) -> dict:
    """직원현황 리스트에서 핵심 지표 추출

    실제 DART 필드:
      sm: 합계 인원수 (남+여 각각 행으로 분리됨)
      jan_salary_am: 1인 평균 월 급여 (원)
      avrg_cnwk_sdytrn: 평균근속연수 문자열 (예: '5년 6개월')
      fyer_salary_totamt: 연간 급여 총액 (원)
    """
    if not emp_list:
        return {"employee_total": None, "employee_avg_salary": None, "employee_avg_tenure": None}

    total_count = 0
    salary_weighted_sum = 0  # jan_salary_am 인원수 가중 합계 (원)
    tenure_raw = None  # 문자열 그대로 사용

    for row in emp_list:
        # 인원수 (sm = 정규직+계약직 합계, 성별로 행 분리되므로 합산)
        headcount_str = row.get("sm", "").replace(",", "").strip()
        try:
            hc = int(headcount_str) if headcount_str and headcount_str != "-" else 0
        except ValueError:
            hc = 0
        total_count += hc

        # jan_salary_am = 1인 평균 연봉 (원) — 가중합계로 전체 평균 계산
        sal_str = row.get("jan_salary_am", "").replace(",", "").strip()
        try:
            sal = int(sal_str) if sal_str and sal_str != "-" else 0
            if sal > 0 and hc > 0:
                salary_weighted_sum += sal * hc
        except ValueError:
            pass

        # 평균 근속 (문자열, 마지막 행 값 사용)
        t = row.get("avrg_cnwk_sdytrn", "").strip()
        if t and t != "-":
            tenure_raw = t

    # 1인 평균 연봉 = jan_salary_am 인원수 가중평균
    avg_annual_salary = None
    if total_count > 0 and salary_weighted_sum > 0:
        avg_annual_salary = salary_weighted_sum // total_count

    return {
        "employee_total": total_count if total_count > 0 else None,
        "employee_avg_salary": avg_annual_salary,
        "employee_avg_tenure": tenure_raw,
    }


def build_financial_deep(corp_code: str) -> dict:
    """3개년 재무 + 직원 데이터로 financial_deep 구성"""
    years = ["2024", "2023", "2022"]
    financials = {}

    for year in years:
        print(f"    [{year}] 재무제표 수집 중...")
        financials[year] = fetch_financial(corp_code, year)
        time.sleep(0.5)

    # 3개년 시계열
    def build_series(account_keys: list) -> list:
        series = []
        for year in years:
            amt = parse_amount(financials[year], account_keys)
            series.append({"year": int(year), "amount": amt})
        return series

    revenue_3y = build_series(ACCOUNT_MAP["revenue"])
    op_profit_3y = build_series(ACCOUNT_MAP["operating_profit"])
    net_income_3y = build_series(ACCOUNT_MAP["net_income"])

    # 최신연도 재무상태
    latest = financials["2024"] or financials["2023"] or {}
    total_assets = parse_amount(latest, ACCOUNT_MAP["total_assets"])
    total_debt = parse_amount(latest, ACCOUNT_MAP["total_debt"])
    total_equity = parse_amount(latest, ACCOUNT_MAP["total_equity"])

    # 부채비율
    debt_ratio = None
    if total_debt and total_equity and total_equity != 0:
        debt_ratio = round(total_debt / total_equity * 100, 1)

    # YoY 매출 성장률 (2024 vs 2023)
    revenue_growth_yoy = None
    r2024 = revenue_3y[0]["amount"]
    r2023 = revenue_3y[1]["amount"]
    if r2024 and r2023 and r2023 != 0:
        growth = (r2024 - r2023) / r2023 * 100
        sign = "+" if growth >= 0 else ""
        revenue_growth_yoy = f"{sign}{growth:.1f}%"

    # 영업이익률 (2024)
    profit_margin = None
    op2024 = op_profit_3y[0]["amount"]
    if op2024 and r2024 and r2024 != 0:
        margin = op2024 / r2024 * 100
        profit_margin = f"{margin:.1f}%"

    # 직원현황
    print(f"    직원현황 수집 중...")
    emp_list = fetch_employee(corp_code, "2024")
    time.sleep(0.5)
    emp_data = parse_employee_data(emp_list)

    return {
        "revenue_3y": revenue_3y,
        "operating_profit_3y": op_profit_3y,
        "net_income_3y": net_income_3y,
        "total_assets": total_assets,
        "total_debt": total_debt,
        "debt_ratio": debt_ratio,
        "revenue_growth_yoy": revenue_growth_yoy,
        "profit_margin": profit_margin,
        **emp_data,
    }


def main():
    with open(DART_DB_PATH, encoding="utf-8") as f:
        dart_db = json.load(f)

    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)

    updated = 0
    skipped = 0

    for i, company in enumerate(meta):
        meta_name = company["name"]
        dart_name = META_TO_DART.get(meta_name)

        if not dart_name or dart_name not in dart_db:
            print(f"[{i+1:02d}] SKIP: {meta_name} (DART 매핑 없음)")
            skipped += 1
            continue

        corp_code = dart_db[dart_name]["corp_code"]
        print(f"\n[{i+1:02d}] {meta_name} (corp_code: {corp_code})")

        financial_deep = build_financial_deep(corp_code)
        company["financial_deep"] = financial_deep
        updated += 1

        # 중간 저장 (API 오류 시 손실 방지)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"  -> 저장 완료 (revenue_2024: {financial_deep['revenue_3y'][0]['amount']})")

    print(f"\n=== 완료: {updated}개 업데이트, {skipped}개 스킵 ===")


if __name__ == "__main__":
    main()
