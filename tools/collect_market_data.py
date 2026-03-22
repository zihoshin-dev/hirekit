#!/usr/bin/env python3
"""KRX 시장 데이터 수집 — dart_company_db.json의 stock_code 기업 대상.

pykrx가 현재 환경에서 데이터를 반환하지 않아 yfinance(Yahoo Finance)를 사용합니다.
KRX 종목코드 → Yahoo Finance 티커: {code}.KS (KOSPI), {code}.KQ (KOSDAQ)
"""
import json
import time
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "docs/demo/data/dart_company_db.json"
OUT_PATH = ROOT / "docs/demo/data/market_data.json"

# corp_cls: Y=KOSPI, K=KOSDAQ, N=코넥스, E=기타
MARKET_SUFFIX = {"Y": "KS", "K": "KQ", "N": "KQ"}


def get_yahoo_ticker(stock_code: str, corp_cls: str) -> str:
    suffix = MARKET_SUFFIX.get(corp_cls, "KS")
    return f"{stock_code}.{suffix}"


def fetch_market_data(stock_code: str, corp_cls: str, corp_name: str) -> dict:
    """단일 종목 시장 데이터 수집."""
    ticker_str = get_yahoo_ticker(stock_code, corp_cls)
    result = {"stock_code": stock_code, "yahoo_ticker": ticker_str}

    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info

        market_cap = info.get("marketCap")
        result["market_cap"] = int(market_cap) if market_cap else None

        per = info.get("trailingPE") or info.get("forwardPE")
        result["per"] = round(float(per), 2) if per else None

        pbr = info.get("priceToBook")
        result["pbr"] = round(float(pbr), 2) if pbr else None

        div_yield = info.get("dividendYield")
        # Yahoo Finance dividendYield는 항상 소수점 비율 (1.83 = 1.83%)
        result["dividend_yield"] = round(float(div_yield), 2) if div_yield else None

        # 외국인 지분율 (기관+외국인 합산 근사치)
        foreign = info.get("heldPercentInstitutions")
        result["foreign_ownership_pct"] = round(float(foreign) * 100, 2) if foreign else None

        result["week52_high"] = info.get("fiftyTwoWeekHigh")
        result["week52_low"] = info.get("fiftyTwoWeekLow")

        # 현재가
        result["current_price"] = info.get("currentPrice") or info.get("regularMarketPrice")

    except Exception as e:
        print(f"    [error] {corp_name} ({ticker_str}): {e}")

    return result


def main():
    with open(DB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    targets = {name: info for name, info in db.items() if info.get("stock_code")}
    print(f"수집 대상: {len(targets)}개 기업 (stock_code 보유)")

    results = {}
    for name, info in targets.items():
        code = info["stock_code"]
        corp_cls = info.get("corp_cls", "Y")
        corp_name = info.get("corp_name", name)
        print(f"  [{code}] {name} 수집 중...")
        data = fetch_market_data(code, corp_cls, corp_name)
        data["corp_name"] = corp_name
        results[name] = data
        cap_str = f"{data.get('market_cap', 0) // 100_000_000:,}억" if data.get("market_cap") else "N/A"
        print(f"    -> 시총={cap_str}, PER={data.get('per')}, PBR={data.get('pbr')}, "
              f"배당={data.get('dividend_yield')}%, 외인={data.get('foreign_ownership_pct')}%")
        time.sleep(0.5)  # Rate limit

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {OUT_PATH} ({len(results)}개)")


if __name__ == "__main__":
    main()
