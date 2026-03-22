#!/usr/bin/env python3
"""hf_metrics.json + papers_metrics.json → meta.json 병합."""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent / "docs/demo/data"
META_PATH = BASE / "meta.json"
HF_PATH = BASE / "hf_metrics.json"
PAPERS_PATH = BASE / "papers_metrics.json"


def _match_key(name: str, data: dict) -> dict | None:
    """meta 기업명을 data 딕셔너리 키와 정확 매칭 (공백/대소문자 정규화)."""
    if name in data:
        return data[name]
    name_norm = name.replace(" ", "").lower()
    for key, val in data.items():
        key_norm = key.replace(" ", "").lower()
        if name_norm == key_norm:
            return val
    return None


def main() -> None:
    with open(META_PATH, encoding="utf-8") as f:
        companies = json.load(f)

    hf_data: dict = {}
    if HF_PATH.exists():
        with open(HF_PATH, encoding="utf-8") as f:
            hf_data = json.load(f)
    else:
        print(f"[skip] {HF_PATH} 없음")

    papers_data: dict = {}
    if PAPERS_PATH.exists():
        with open(PAPERS_PATH, encoding="utf-8") as f:
            papers_data = json.load(f)
    else:
        print(f"[skip] {PAPERS_PATH} 없음")

    hf_changes = []
    papers_changes = []

    for company in companies:
        name = company["name"]

        # HF 지표 병합
        hf = _match_key(name, hf_data)
        if hf:
            company["hf_model_count"] = hf.get("hf_model_count", 0)
            company["hf_dataset_count"] = hf.get("hf_dataset_count", 0)
            company["hf_total_downloads"] = hf.get("hf_total_downloads", 0)
            company["hf_top_models"] = hf.get("hf_top_models", [])
            hf_changes.append(
                f"  {name}: models={hf['hf_model_count']}, "
                f"datasets={hf['hf_dataset_count']}, "
                f"downloads={hf['hf_total_downloads']:,}"
            )

        # 논문 지표 병합
        papers = _match_key(name, papers_data)
        if papers:
            company["paper_count"] = papers.get("paper_count", 0)
            company["top_venues"] = papers.get("top_venues", [])
            company["total_citations"] = papers.get("total_citations", 0)
            company["top_papers"] = papers.get("top_papers", [])
            papers_changes.append(
                f"  {name}: papers={papers['paper_count']}, "
                f"citations={papers['total_citations']}, "
                f"venues={papers['top_venues'][:3]}"
            )

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"HF 데이터 병합: {len(hf_changes)}개 기업")
    for line in hf_changes:
        print(line)
    print()
    print(f"논문 데이터 병합: {len(papers_changes)}개 기업")
    for line in papers_changes:
        print(line)
    print(f"\nmeta.json 업데이트 완료 ({len(companies)}개 기업)")


if __name__ == "__main__":
    main()
