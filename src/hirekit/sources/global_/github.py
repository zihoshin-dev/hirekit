"""GitHub organization tech maturity scoring."""

from __future__ import annotations

import subprocess
from collections import Counter
from typing import Any

from hirekit.core.company_resolver import DEFAULT_ORG_MAP  # re-exported for backwards compat
from hirekit.core.tech_taxonomy import (
    build_actual_work_profile,
    build_stack_reality,
    build_stack_signal,
    extract_stack_signals,
    extract_work_signals,
    normalize_tech,
)
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult


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
                capture_output=True,
                text=True,
                timeout=5,
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
            results.append(
                SourceResult(
                    source_name=self.name,
                    section="tech",
                    data=score_data,
                    url=f"https://github.com/{org}",
                    raw=f"GitHub org '{org}': {score_data.get('total_score', 0)}/100, "
                    f"{score_data.get('repo_count', 0)} repos, "
                    f"top languages: {', '.join(score_data.get('top_languages', [])[:5])}",
                )
            )

        return results

    def _fetch_repos(self, org: str) -> list[dict[str, Any]]:
        """Fetch public repos for a GitHub org."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"orgs/{org}/repos?per_page=100&sort=updated&type=public",
                    "--jq",
                    ".[].{name,stargazers_count,language,updated_at,fork,archived,description,topics}",
                ],
                capture_output=True,
                text=True,
                timeout=15,
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
        languages = [normalize_tech(str(r.get("language"))) for r in active_repos if r.get("language")]
        language_counts = Counter(languages)
        unique_langs = [tech for tech, _ in language_counts.most_common(10)]

        # Scoring dimensions (each 0-20, total 100)
        size_score = min(20, len(active_repos) * 2)  # 10+ repos = 20
        star_score = min(20, total_stars // 50)  # 1000+ stars = 20
        diversity_score = min(20, len(unique_langs) * 4)  # 5+ languages = 20
        from hirekit.core.scoring import current_year, score_to_grade

        cur_year = str(current_year())
        prev_year = str(current_year() - 1)
        activity_score = min(
            20,
            sum(1 for r in active_repos if cur_year in r.get("updated_at", "") or prev_year in r.get("updated_at", ""))
            * 4,
        )

        # Community score (repos with 100+ stars)
        popular = sum(1 for r in active_repos if r.get("stargazers_count", 0) >= 100)
        community_score = min(20, popular * 5)

        stack_signals = self._build_stack_signals(active_repos, language_counts)
        work_signals = self._build_work_signals(active_repos)

        total = size_score + star_score + diversity_score + activity_score + community_score
        grade = score_to_grade(total)

        return {
            "org": org,
            "repo_count": len(active_repos),
            "total_stars": total_stars,
            "top_languages": unique_langs[:10],
            "stack_signals": stack_signals,
            "stack_reality": build_stack_reality(stack_signals),
            "actual_work_signals": work_signals,
            "actual_work": build_actual_work_profile(work_signals),
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

    def _build_stack_signals(
        self,
        repos: list[dict[str, Any]],
        language_counts: Counter[str],
    ) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []
        total_repos = max(len(repos), 1)

        for tech, count in language_counts.most_common(10):
            if not tech:
                continue
            confidence = 0.66 + min(0.18, (count / total_repos) * 0.2)
            signals.append(
                build_stack_signal(
                    tech,
                    source_name=self.name,
                    source_authority="company_operated",
                    evidence=f"{count} active repos declare {tech} as the primary language",
                    confidence=confidence,
                    signal_type="repo_language",
                ),
            )

        signals.extend(
            extract_stack_signals(
                self._repo_surface_texts(repos),
                source_name=self.name,
                source_authority="company_operated",
                signal_type="repo_surface",
                base_confidence=0.62,
            ),
        )
        return signals

    def _build_work_signals(self, repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return extract_work_signals(
            self._repo_surface_texts(repos),
            source_name=self.name,
            source_authority="company_operated",
            base_confidence=0.6,
        )

    @staticmethod
    def _repo_surface_texts(repos: list[dict[str, Any]]) -> list[str]:
        texts: list[str] = []
        for repo in repos:
            name = str(repo.get("name", "")).strip()
            if name:
                texts.append(name)

            description = str(repo.get("description", "")).strip()
            if description:
                texts.append(description)

            topics = repo.get("topics", [])
            if isinstance(topics, list):
                topic_text = " ".join(str(topic).strip() for topic in topics if str(topic).strip())
                if topic_text:
                    texts.append(topic_text)
            elif isinstance(topics, str) and topics.strip():
                texts.append(topics.strip())
        return texts
