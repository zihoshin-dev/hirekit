"""Company comparator — rule-based multi-dimensional comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hirekit.core.scoring import score_to_grade


# ---------------------------------------------------------------------------
# Known company data (rule-based, no LLM)
# ---------------------------------------------------------------------------

_COMPANY_DATA: dict[str, dict[str, Any]] = {
    "토스": {
        "industry": "fintech",
        "size": "mid",          # startup < mid < large < enterprise
        "size_employees": 3000,
        "growth": 4.5,          # 1-5 scale
        "compensation": 4.5,
        "culture": 4.5,
        "tech_level": 5.0,
        "brand": 4.0,
        "wlb": 3.5,
        "remote": 3.0,
        "region": "kr",
    },
    "toss": {
        "industry": "fintech",
        "size": "mid",
        "size_employees": 3000,
        "growth": 4.5,
        "compensation": 4.5,
        "culture": 4.5,
        "tech_level": 5.0,
        "brand": 4.0,
        "wlb": 3.5,
        "remote": 3.0,
        "region": "kr",
    },
    "카카오": {
        "industry": "tech",
        "size": "large",
        "size_employees": 15000,
        "growth": 3.0,
        "compensation": 4.0,
        "culture": 3.5,
        "tech_level": 4.0,
        "brand": 5.0,
        "wlb": 3.5,
        "remote": 3.5,
        "region": "kr",
    },
    "kakao": {
        "industry": "tech",
        "size": "large",
        "size_employees": 15000,
        "growth": 3.0,
        "compensation": 4.0,
        "culture": 3.5,
        "tech_level": 4.0,
        "brand": 5.0,
        "wlb": 3.5,
        "remote": 3.5,
        "region": "kr",
    },
    "네이버": {
        "industry": "tech",
        "size": "large",
        "size_employees": 20000,
        "growth": 3.5,
        "compensation": 4.0,
        "culture": 3.5,
        "tech_level": 4.5,
        "brand": 5.0,
        "wlb": 3.5,
        "remote": 4.0,
        "region": "kr",
    },
    "naver": {
        "industry": "tech",
        "size": "large",
        "size_employees": 20000,
        "growth": 3.5,
        "compensation": 4.0,
        "culture": 3.5,
        "tech_level": 4.5,
        "brand": 5.0,
        "wlb": 3.5,
        "remote": 4.0,
        "region": "kr",
    },
    "쿠팡": {
        "industry": "ecommerce",
        "size": "large",
        "size_employees": 50000,
        "growth": 4.0,
        "compensation": 4.5,
        "culture": 3.0,
        "tech_level": 4.5,
        "brand": 4.5,
        "wlb": 2.5,
        "remote": 2.0,
        "region": "kr",
    },
    "coupang": {
        "industry": "ecommerce",
        "size": "large",
        "size_employees": 50000,
        "growth": 4.0,
        "compensation": 4.5,
        "culture": 3.0,
        "tech_level": 4.5,
        "brand": 4.5,
        "wlb": 2.5,
        "remote": 2.0,
        "region": "kr",
    },
    "배달의민족": {
        "industry": "foodtech",
        "size": "large",
        "size_employees": 4000,
        "growth": 3.5,
        "compensation": 4.0,
        "culture": 4.0,
        "tech_level": 4.5,
        "brand": 4.5,
        "wlb": 3.5,
        "remote": 3.0,
        "region": "kr",
    },
    "baemin": {
        "industry": "foodtech",
        "size": "large",
        "size_employees": 4000,
        "growth": 3.5,
        "compensation": 4.0,
        "culture": 4.0,
        "tech_level": 4.5,
        "brand": 4.5,
        "wlb": 3.5,
        "remote": 3.0,
        "region": "kr",
    },
    "당근마켓": {
        "industry": "marketplace",
        "size": "mid",
        "size_employees": 700,
        "growth": 4.0,
        "compensation": 4.0,
        "culture": 4.5,
        "tech_level": 4.5,
        "brand": 4.0,
        "wlb": 4.0,
        "remote": 4.0,
        "region": "kr",
    },
    "당근": {
        "industry": "marketplace",
        "size": "mid",
        "size_employees": 700,
        "growth": 4.0,
        "compensation": 4.0,
        "culture": 4.5,
        "tech_level": 4.5,
        "brand": 4.0,
        "wlb": 4.0,
        "remote": 4.0,
        "region": "kr",
    },
    "google": {
        "industry": "tech",
        "size": "enterprise",
        "size_employees": 180000,
        "growth": 3.5,
        "compensation": 5.0,
        "culture": 4.5,
        "tech_level": 5.0,
        "brand": 5.0,
        "wlb": 4.0,
        "remote": 3.5,
        "region": "global",
    },
    "meta": {
        "industry": "tech",
        "size": "enterprise",
        "size_employees": 70000,
        "growth": 3.5,
        "compensation": 5.0,
        "culture": 3.5,
        "tech_level": 5.0,
        "brand": 4.0,
        "wlb": 3.5,
        "remote": 3.5,
        "region": "global",
    },
    "amazon": {
        "industry": "tech",
        "size": "enterprise",
        "size_employees": 1500000,
        "growth": 4.0,
        "compensation": 5.0,
        "culture": 3.0,
        "tech_level": 5.0,
        "brand": 5.0,
        "wlb": 2.5,
        "remote": 2.5,
        "region": "global",
    },
}

_DIMENSION_LABELS: dict[str, str] = {
    "growth": "성장성",
    "compensation": "보상",
    "culture": "문화",
    "tech_level": "기술 수준",
    "brand": "브랜드",
    "wlb": "워라밸",
    "remote": "원격근무",
}

_DIMENSION_WEIGHTS: dict[str, float] = {
    "growth": 0.20,
    "compensation": 0.20,
    "culture": 0.20,
    "tech_level": 0.15,
    "brand": 0.10,
    "wlb": 0.10,
    "remote": 0.05,
}


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ComparisonResult:
    """Result of comparing two or more companies."""

    companies: list[str]
    dimensions: dict[str, list[float]]   # {dimension_key: [score_c1, score_c2, ...]}
    winner_by_dimension: dict[str, str]  # {dimension_key: company_name}
    overall_scores: dict[str, float]     # {company: weighted_score 0-100}
    overall_recommendation: str
    comparison_table: dict[str, Any]     # detailed comparison data

    @property
    def winner(self) -> str:
        """Company with highest overall score."""
        if not self.overall_scores:
            return ""
        return max(self.overall_scores, key=lambda k: self.overall_scores[k])

    def to_markdown(self) -> str:
        """Render comparison as Markdown table."""
        lines = [
            f"# 기업 비교: {' vs '.join(self.companies)}",
            "",
            "## 차원별 비교",
            "",
        ]

        # Header
        header = "| 차원 | " + " | ".join(self.companies) + " | 승자 |"
        sep = "|------|" + "------|" * len(self.companies) + "------|"
        lines += [header, sep]

        for dim_key, label in _DIMENSION_LABELS.items():
            scores = self.dimensions.get(dim_key, [])
            score_cells = " | ".join(
                f"{s:.1f}/5" if s > 0 else "-" for s in scores
            )
            winner = self.winner_by_dimension.get(dim_key, "-")
            lines.append(f"| {label} | {score_cells} | {winner} |")

        lines += [
            "",
            "## 종합 점수",
            "",
        ]
        for company, score in self.overall_scores.items():
            grade = score_to_grade(score)
            lines.append(f"- **{company}**: {score:.0f}/100 (등급 {grade})")

        lines += [
            "",
            "## 추천",
            "",
            self.overall_recommendation,
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------


class CompanyComparator:
    """Rule-based multi-dimensional company comparator."""

    def compare(self, company_a: str, company_b: str) -> ComparisonResult:
        """Compare two companies across multiple dimensions."""
        return self.compare_many([company_a, company_b])

    def compare_many(self, companies: list[str]) -> ComparisonResult:
        """Compare 2-5 companies across multiple dimensions.

        Args:
            companies: List of company names (2-5).
        """
        if len(companies) < 2:
            raise ValueError("비교하려면 최소 2개 기업이 필요해요.")
        if len(companies) > 5:
            companies = companies[:5]

        # Load data for each company
        company_data = []
        resolved_names = []
        for name in companies:
            key = name.lower()
            data = _COMPANY_DATA.get(key, self._default_data(name))
            company_data.append(data)
            resolved_names.append(name)

        # Build dimension scores matrix
        dimensions: dict[str, list[float]] = {}
        for dim_key in _DIMENSION_LABELS:
            dimensions[dim_key] = [d.get(dim_key, 2.5) for d in company_data]

        # Winner by dimension
        winner_by_dimension: dict[str, str] = {}
        for dim_key, scores in dimensions.items():
            max_score = max(scores)
            winners = [
                resolved_names[i] for i, s in enumerate(scores) if s == max_score
            ]
            winner_by_dimension[dim_key] = " & ".join(winners)

        # Weighted overall scores (convert 1-5 → 0-100)
        overall_scores: dict[str, float] = {}
        for i, name in enumerate(resolved_names):
            weighted = sum(
                dimensions[dim][i] * weight
                for dim, weight in _DIMENSION_WEIGHTS.items()
                if dim in dimensions
            )
            overall_scores[name] = round((weighted / 5.0) * 100, 1)

        # Build recommendation
        winner_name = max(overall_scores, key=lambda k: overall_scores[k])
        recommendation = self._build_recommendation(
            resolved_names, company_data, overall_scores, winner_name
        )

        # Comparison table (full details)
        comparison_table: dict[str, Any] = {
            "companies": resolved_names,
            "scores": {
                name: {
                    dim: dimensions[dim][i]
                    for dim in _DIMENSION_LABELS
                }
                for i, name in enumerate(resolved_names)
            },
            "industry": {name: company_data[i].get("industry", "unknown") for i, name in enumerate(resolved_names)},
            "size": {name: company_data[i].get("size", "unknown") for i, name in enumerate(resolved_names)},
            "employees": {name: company_data[i].get("size_employees", 0) for i, name in enumerate(resolved_names)},
        }

        return ComparisonResult(
            companies=resolved_names,
            dimensions=dimensions,
            winner_by_dimension=winner_by_dimension,
            overall_scores=overall_scores,
            overall_recommendation=recommendation,
            comparison_table=comparison_table,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_data(name: str) -> dict[str, Any]:
        """Return neutral data for unknown companies."""
        return {
            "industry": "unknown",
            "size": "unknown",
            "size_employees": 0,
            "growth": 3.0,
            "compensation": 3.0,
            "culture": 3.0,
            "tech_level": 3.0,
            "brand": 3.0,
            "wlb": 3.0,
            "remote": 3.0,
            "region": "unknown",
        }

    @staticmethod
    def _build_recommendation(
        names: list[str],
        data: list[dict[str, Any]],
        scores: dict[str, float],
        winner: str,
    ) -> str:
        """Build a natural language recommendation."""
        winner_idx = names.index(winner)
        winner_data = data[winner_idx]
        winner_score = scores[winner]

        grade = score_to_grade(winner_score)
        lines = [
            f"**종합 추천: {winner}** (점수 {winner_score:.0f}/100, 등급 {grade})",
            "",
        ]

        # Highlight winner's best dimensions
        best_dims = sorted(
            _DIMENSION_LABELS.items(),
            key=lambda kv: winner_data.get(kv[0], 0),
            reverse=True,
        )[:2]
        best_labels = [label for _, label in best_dims]
        lines.append(f"{winner}의 강점: {', '.join(best_labels)}")

        # Situational advice
        if winner_data.get("wlb", 0) >= 4.0:
            lines.append("워라밸을 중시한다면 더욱 적합해요.")
        if winner_data.get("compensation", 0) >= 4.5:
            lines.append("보상 패키지가 업계 상위권이에요.")
        if winner_data.get("tech_level", 0) >= 4.5:
            lines.append("기술 성장 환경이 뛰어나요.")

        # Runner-up note
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) >= 2:
            runner_up, runner_score = sorted_scores[1]
            diff = winner_score - runner_score
            if diff < 5:
                lines.append(
                    f"\n{runner_up}도 {runner_score:.0f}점으로 근소한 차이예요. "
                    "개인 우선순위에 따라 선택하세요."
                )

        return "\n".join(lines)
