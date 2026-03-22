#!/usr/bin/env python3
"""market_data.json + ai_metrics.json → meta.json 병합."""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent / "docs/demo/data"
META_PATH = BASE / "meta.json"
MARKET_PATH = BASE / "market_data.json"
AI_PATH = BASE / "ai_metrics.json"


def _match_key(name: str, data: dict) -> dict | None:
    """meta 기업명을 data 딕셔너리 키와 매칭 (직접 + 부분 문자열)."""
    if name in data:
        return data[name]
    name_norm = name.replace(" ", "").lower()
    for key, val in data.items():
        key_norm = key.replace(" ", "").lower()
        if name_norm == key_norm or name_norm in key_norm or key_norm in name_norm:
            return val
    return None


def main():
    with open(META_PATH, encoding="utf-8") as f:
        companies = json.load(f)

    with open(MARKET_PATH, encoding="utf-8") as f:
        market_data = json.load(f)

    with open(AI_PATH, encoding="utf-8") as f:
        ai_metrics = json.load(f)

    market_changes = []
    ai_changes = []

    for company in companies:
        name = company["name"]

        # 시장 데이터 병합 (stock_code 있는 기업)
        market = _match_key(name, market_data)
        if market:
            if market.get("market_cap"):
                company["market_cap"] = market["market_cap"]
            if market.get("per") is not None:
                company["per"] = market["per"]
            if market.get("pbr") is not None:
                company["pbr"] = market["pbr"]
            if market.get("dividend_yield") is not None:
                company["dividend_yield"] = market["dividend_yield"]
            if market.get("foreign_ownership_pct") is not None:
                company["foreign_ownership_pct"] = market["foreign_ownership_pct"]
            if market.get("week52_high"):
                company["week52_high"] = market["week52_high"]
            if market.get("week52_low"):
                company["week52_low"] = market["week52_low"]
            cap = market.get("market_cap")
            cap_str = f"{cap // 100_000_000:,}억" if cap else "N/A"
            market_changes.append(
                f"  {name}: 시총={cap_str}, "
                f"PER={market.get('per')}, 배당={market.get('dividend_yield')}%, "
                f"외인={market.get('foreign_ownership_pct')}%"
            )

        # AI 메트릭 병합 (github_orgs 있는 기업)
        ai = _match_key(name, ai_metrics)
        if ai and ai.get("ai_repos_count", 0) >= 0:
            company["ai_repos_count"] = ai["ai_repos_count"]
            company["ai_total_stars"] = ai["ai_total_stars"]
            company["top_ai_repos"] = ai["top_ai_repos"]
            ai_changes.append(
                f"  {name}: ai_repos={ai['ai_repos_count']}, "
                f"ai_stars={ai['ai_total_stars']}, "
                f"top={[r['name'] for r in ai['top_ai_repos']]}"
            )

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"시장 데이터 병합: {len(market_changes)}개 기업")
    for line in market_changes:
        print(line)
    print()
    print(f"AI 메트릭 병합: {len(ai_changes)}개 기업")
    for line in ai_changes:
        print(line)
    print(f"\nmeta.json 업데이트 완료 ({len(companies)}개 기업)")


if __name__ == "__main__":
    main()
