#!/usr/bin/env python3
"""GitHub AI 레포 분석 — company_resolver의 github_orgs 기업 대상."""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT_PATH = ROOT / "docs/demo/data/ai_metrics.json"

AI_KEYWORDS = {"ai", "ml", "llm", "deep", "neural", "nlp", "gpt", "bert",
               "transformer", "diffusion", "rag", "embedding", "inference",
               "model", "train", "finetune", "vision", "speech", "recommend"}


def gh_api(path: str) -> list | dict | None:
    """gh CLI로 GitHub API 호출 (paginate 없이 per_page=100 사용)."""
    # path에 ? 포함 여부에 따라 쿼리 파라미터 추가
    sep = "&" if "?" in path else "?"
    full_path = f"{path}{sep}per_page=100"
    try:
        result = subprocess.run(
            ["gh", "api", full_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None
        text = result.stdout.strip()
        if not text:
            return None
        return json.loads(text)
    except Exception as e:
        print(f"    [gh error] {path}: {e}")
        return None


def is_ai_repo(repo_name: str, topics: list, description: str) -> bool:
    """AI/ML 관련 레포 여부 판단."""
    name_lower = repo_name.lower()
    desc_lower = (description or "").lower()
    topic_set = set(t.lower() for t in (topics or []))

    # 이름에 AI 키워드 포함
    for kw in AI_KEYWORDS:
        if kw in name_lower:
            return True
    # 토픽에 AI 키워드 포함
    if topic_set & AI_KEYWORDS:
        return True
    # 설명에 주요 AI 키워드 포함
    for kw in {"machine learning", "deep learning", "artificial intelligence",
               "large language", "neural network", "natural language"}:
        if kw in desc_lower:
            return True
    return False


def fetch_org_ai_metrics(org: str) -> dict | None:
    """단일 GitHub org의 AI 관련 지표 수집."""
    print(f"    org: {org}")
    repos = gh_api(f"orgs/{org}/repos?per_page=100&type=public&sort=updated")
    if repos is None:
        # org가 아닌 user일 수도 있음
        repos = gh_api(f"users/{org}/repos?per_page=100&type=public&sort=updated")
    if not repos or not isinstance(repos, list):
        return None

    ai_repos = []
    for repo in repos:
        name = repo.get("name", "")
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language", "")
        description = repo.get("description", "")
        topics = repo.get("topics", [])

        if is_ai_repo(name, topics, description):
            ai_repos.append({
                "name": name,
                "stars": stars,
                "language": language,
                "description": (description or "")[:100],
            })

    ai_repos.sort(key=lambda x: x["stars"], reverse=True)

    return {
        "ai_repos_count": len(ai_repos),
        "ai_total_stars": sum(r["stars"] for r in ai_repos),
        "top_ai_repos": [{"name": r["name"], "stars": r["stars"], "language": r["language"]}
                         for r in ai_repos[:3]],
    }


def check_huggingface(company_name: str, org_names: list[str]) -> bool:
    """Hugging Face org 존재 여부 확인."""
    # 간단히 company name에서 HF org 이름 추정
    candidates = set()
    for org in org_names:
        candidates.add(org.lower())
        candidates.add(org.lower().replace("-", ""))

    for candidate in candidates:
        result = subprocess.run(
            ["gh", "api", f"https://huggingface.co/api/organizations/{candidate}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                if data.get("name"):
                    return True
            except Exception:
                pass
    return False


def main():
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from hirekit.core.company_resolver import _REGISTRY

    targets = {name: info for name, info in _REGISTRY.items() if info.github_orgs}
    # 중복 org 제거를 위해 이미 처리한 orgs 추적
    processed_orgs: dict[str, dict] = {}  # org -> metrics
    results = {}

    print(f"수집 대상: {len(targets)}개 기업 (github_orgs 보유)")

    for name, info in targets.items():
        orgs = info.github_orgs
        print(f"  {name}: {orgs}")

        # org별 metrics 합산
        total_ai_repos = 0
        total_ai_stars = 0
        all_top_repos: list[dict] = []

        for org in orgs:
            if org in processed_orgs:
                metrics = processed_orgs[org]
            else:
                metrics = fetch_org_ai_metrics(org)
                processed_orgs[org] = metrics
                time.sleep(0.5)  # Rate limit

            if metrics:
                total_ai_repos += metrics.get("ai_repos_count", 0)
                total_ai_stars += metrics.get("ai_total_stars", 0)
                all_top_repos.extend(metrics.get("top_ai_repos", []))

        all_top_repos.sort(key=lambda x: x["stars"], reverse=True)

        results[name] = {
            "github_orgs": orgs,
            "ai_repos_count": total_ai_repos,
            "ai_total_stars": total_ai_stars,
            "top_ai_repos": all_top_repos[:3],
        }
        print(f"    -> ai_repos={total_ai_repos}, ai_stars={total_ai_stars}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {OUT_PATH} ({len(results)}개)")


if __name__ == "__main__":
    main()
