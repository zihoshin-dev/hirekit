#!/usr/bin/env python3
"""KRX 시장 데이터 수집 — dart_company_db.json의 stock_code 기업 대상."""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from pykrx import stock
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pykrx", "-q"])
    from pykrx import stock

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "docs/demo/data/dart_company_db.json"
OUT_PATH = ROOT / "docs/demo/data/market_data.json"


def get_trading_date(days_back: int = 1) -> str:
    """최근 영업일 반환 (YYYYMMDD)."""
    d = datetime.now() - timedelta(days=days_back)
    # 주말 건너뜀
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def fetch_market_data(stock_code: str, date: str) -> dict:
    """단일 종목 시장 데이터 수집."""
    result = {}
    try:
        # 시가총액
        cap_df = stock.get_market_cap_by_date(date, date, stock_code)
        if not cap_df.empty:
            row = cap_df.iloc[-1]
            result["market_cap"] = int(row.get("시가총액", 0))
            result["shares"] = int(row.get("상장주식수", 0))
    except Exception as e:
        print(f"    [cap error] {e}")

    time.sleep(0.3)

    try:
        # PER, PBR, 배당수익률
        fund_df = stock.get_market_fundamental_by_date(date, date, stock_code)
        if not fund_df.empty:
            row = fund_df.iloc[-1]
            result["per"] = float(row.get("PER", 0)) if row.get("PER") else None
            result["pbr"] = float(row.get("PBR", 0)) if row.get("PBR") else None
            result["dividend_yield"] = float(row.get("DIV", 0)) if row.get("DIV") else None
    except Exception as e:
        print(f"    [fundamental error] {e}")

    time.sleep(0.3)

    try:
        # 외국인 지분율 — 52주 범위에서 최고/최저 OHLCV 함께
        year_ago = (datetime.strptime(date, "%Y%m%d") - timedelta(days=365)).strftime("%Y%m%d")
        ohlcv_df = stock.get_market_ohlcv_by_date(year_ago, date, stock_code)
        if not ohlcv_df.empty:
            result["week52_high"] = int(ohlcv_df["고가"].max())
            result["week52_low"] = int(ohlcv_df["저가"].min())
    except Exception as e:
        print(f"    [ohlcv error] {e}")

    time.sleep(0.3)

    try:
        # 외국인 지분율
        inv_df = stock.get_market_trading_volume_by_date(date, date, stock_code)
        if not inv_df.empty:
            pass  # 외국인 지분율은 별도 API
        foreign_df = stock.get_exhaustion_rates_of_foreign_investment_by_ticker(date, date, stock_code)
        if not foreign_df.empty:
            row = foreign_df.iloc[-1]
            result["foreign_ownership_pct"] = float(row.get("지분율", 0)) if "지분율" in row else None
    except Exception as e:
        print(f"    [foreign error] {e}")

    return result


def main():
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    # stock_code 있는 기업만
    targets = {name: info for name, info in db.items() if info.get("stock_code")}
    print(f"수집 대상: {len(targets)}개 기업")

    # 최근 영업일 (어제 또는 그 이전)
    trade_date = get_trading_date(days_back=1)
    print(f"기준일: {trade_date}")

    results = {}
    for name, info in targets.items():
        code = info["stock_code"]
        print(f"  [{code}] {name} 수집 중...")
        data = fetch_market_data(code, trade_date)
        data["stock_code"] = code
        data["corp_name"] = info.get("corp_name", name)
        data["trade_date"] = trade_date
        results[name] = data
        print(f"    -> market_cap={data.get('market_cap')}, per={data.get('per')}, pbr={data.get('pbr')}")
        time.sleep(1.0)  # Rate limit

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {OUT_PATH} ({len(results)}개)")


if __name__ == "__main__":
    main()
