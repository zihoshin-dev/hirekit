"""GitHub organization tech maturity scoring."""

from __future__ import annotations

import subprocess
from typing import Any

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

# Well-known company -> GitHub org mappings
DEFAULT_ORG_MAP: dict[str, list[str]] = {
    "카카오": ["kakao"],
    "카카오페이": ["kakaopay"],
    "토스": ["toss"],
    "네이버": ["naver", "navercorp"],
    "네이버클라우드": ["NaverCloudPlatform"],
    "쿠팡": ["coupang"],
    "우아한형제들": ["woowabros"],
    "당근": ["daangn"],
    "무신사": ["musinsa"],
    "라인": ["line"],
    "야놀자": ["yanolja"],
}


@SourceRegistry.register
class GitHubSource(BaseSource):
    """Score a company's tech maturity via their GitHub organization."""

    name = "github"
    region = "global"
    sections = ["tech"]
    requires_api_key = False  # uses gh CLI auth

    def is_available(self) -> bool:
        """Check if gh CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True, text=True, timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        orgs = kwargs.get("github_orgs") or DEFAULT_ORG_MAP.get(company, [])
        if not orgs:
            # Try company name as org
            orgs = [company.lower().replace(" ", "")]

        results: list[SourceResult] = []

        for org in orgs:
            repos = self._fetch_repos(org)
            if not repos:
                continue

            score_data = self._score_org(org, repos)
            results.append(SourceResult(
                source_name=self.name,
                section="tech",
                data=score_data,
                url=f"https://github.com/{org}",
                raw=f"GitHub org '{org}': {score_data.get('total_score', 0)}/100, "
                    f"{score_data.get('repo_count', 0)} repos, "
                    f"top languages: {', '.join(score_data.get('top_languages', [])[:5])}",
            ))

        return results

    def _fetch_repos(self, org: str) -> list[dict[str, Any]]:
        """Fetch public repos for a GitHub org."""
        try:
            result = subprocess.run(
                ["gh", "api", f"orgs/{org}/repos?per_page=100&sort=updated&type=public",
                 "--jq", '.[].{name,stargazers_count,language,updated_at,fork,archived}'],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return []

            import json
            # gh api with --jq returns one JSON object per line
            repos = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        repos.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return repos
        except Exception:
            return []

    def _score_org(self, org: str, repos: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate tech maturity score (0-100) across 5 dimensions."""
        active_repos = [r for r in repos if not r.get("fork") and not r.get("archived")]
        total_stars = sum(r.get("stargazers_count", 0) for r in active_repos)

        # Language diversity
        languages = [r.get("language") for r in active_repos if r.get("language")]
        unique_langs = list(set(languages))

        # Scoring dimensions (each 0-20, total 100)
        size_score = min(20, len(active_repos) * 2)  # 10+ repos = 20
        star_score = min(20, total_stars // 50)  # 1000+ stars = 20
        diversity_score = min(20, len(unique_langs) * 4)  # 5+ languages = 20
        from hirekit.core.scoring import current_year, score_to_grade

        cur_year = str(current_year())
        prev_year = str(current_year() - 1)
        activity_score = min(20, sum(1 for r in active_repos
                                      if cur_year in r.get("updated_at", "")
                                      or prev_year in r.get("updated_at", "")) * 4)

        # Community score (repos with 100+ stars)
        popular = sum(1 for r in active_repos if r.get("stargazers_count", 0) >= 100)
        community_score = min(20, popular * 5)

        total = size_score + star_score + diversity_score + activity_score + community_score
        grade = score_to_grade(total)

        return {
            "org": org,
            "repo_count": len(active_repos),
            "total_stars": total_stars,
            "top_languages": unique_langs[:10],
            "total_score": total,
            "grade": grade,
            "dimensions": {
                "size": size_score,
                "stars": star_score,
                "diversity": diversity_score,
                "activity": activity_score,
                "community": community_score,
            },
        }
