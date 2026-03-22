#!/usr/bin/env python3
"""Hugging Face Hub API로 기업별 AI 모델/데이터셋 수집."""
import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "docs/demo/data/hf_metrics.json"

# 기업 → HF org 매핑
HF_ORGS: dict[str, list[str]] = {
    "네이버": ["naver", "NAVER-CLOVA-X"],
    "카카오": ["kakaobrain", "kakaoenterprise"],
    "SK텔레콤": ["SKT"],
    "업스테이지": ["upstage"],
    "LG전자": ["lg-ai-research"],
    "삼성전자": ["samsung"],
    "리벨리온": ["rebellions"],
    "뤼튼": ["riiid"],
}

HF_BASE = "https://huggingface.co/api"


def fetch_models(org: str, client: httpx.Client) -> list[dict]:
    """org의 공개 모델 목록 수집 (최대 100개)."""
    try:
        resp = client.get(
            f"{HF_BASE}/models",
            params={"author": org, "limit": 100},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"    [hf models error] {org}: {e}")
    return []


def fetch_datasets(org: str, client: httpx.Client) -> list[dict]:
    """org의 공개 데이터셋 목록 수집 (최대 100개)."""
    try:
        resp = client.get(
            f"{HF_BASE}/datasets",
            params={"author": org, "limit": 100},
            timeout=20,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"    [hf datasets error] {org}: {e}")
    return []


def get_top_models(models: list[dict], n: int = 3) -> list[dict]:
    """다운로드 수 기준 상위 n개 모델 반환."""
    sorted_models = sorted(models, key=lambda m: m.get("downloads", 0), reverse=True)
    result = []
    for m in sorted_models[:n]:
        result.append({
            "name": m.get("id", ""),
            "downloads": m.get("downloads", 0),
            "task": m.get("pipeline_tag", ""),
        })
    return result


def fetch_org_metrics(org: str, client: httpx.Client) -> dict:
    """단일 org의 HF 지표 수집."""
    print(f"    org: {org}")
    models = fetch_models(org, client)
    time.sleep(0.3)
    datasets = fetch_datasets(org, client)
    time.sleep(0.3)

    total_downloads = sum(m.get("downloads", 0) for m in models)
    top_models = get_top_models(models)

    return {
        "hf_org": org,
        "hf_model_count": len(models),
        "hf_dataset_count": len(datasets),
        "hf_total_downloads": total_downloads,
        "hf_top_models": top_models,
    }


def merge_org_metrics(metrics_list: list[dict]) -> dict:
    """여러 org 지표를 단일 기업 지표로 합산."""
    if not metrics_list:
        return {
            "hf_orgs": [],
            "hf_model_count": 0,
            "hf_dataset_count": 0,
            "hf_total_downloads": 0,
            "hf_top_models": [],
        }

    all_top_models: list[dict] = []
    total_model_count = 0
    total_dataset_count = 0
    total_downloads = 0
    orgs = []

    for m in metrics_list:
        orgs.append(m["hf_org"])
        total_model_count += m["hf_model_count"]
        total_dataset_count += m["hf_dataset_count"]
        total_downloads += m["hf_total_downloads"]
        all_top_models.extend(m["hf_top_models"])

    all_top_models.sort(key=lambda x: x["downloads"], reverse=True)

    return {
        "hf_orgs": orgs,
        "hf_model_count": total_model_count,
        "hf_dataset_count": total_dataset_count,
        "hf_total_downloads": total_downloads,
        "hf_top_models": all_top_models[:3],
    }


def main() -> None:
    results: dict[str, dict] = {}

    with httpx.Client() as client:
        for company, orgs in HF_ORGS.items():
            print(f"  {company}: {orgs}")
            org_metrics = []
            for org in orgs:
                metrics = fetch_org_metrics(org, client)
                org_metrics.append(metrics)
                print(
                    f"    -> models={metrics['hf_model_count']}, "
                    f"datasets={metrics['hf_dataset_count']}, "
                    f"downloads={metrics['hf_total_downloads']:,}"
                )

            results[company] = merge_org_metrics(org_metrics)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUT_PATH} ({len(results)}개 기업)")


if __name__ == "__main__":
    main()
