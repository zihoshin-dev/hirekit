"""Company analysis orchestrator — collects data, scores, and generates reports."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Mapping

from rich.panel import Panel
from rich.text import Text

from hirekit.core.cache import Cache
from hirekit.core.config import HireKitConfig
from hirekit.core.parallel import collect_parallel
from hirekit.engine.scorer import ScoreDimension, Scorecard, create_default_scorecard
from hirekit.llm.base import BaseLLM, NoLLM
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult


def _source_hash(sources: list[BaseSource]) -> str:
    """Return a short hash of the active source names for cache key versioning."""
    names = ",".join(sorted(s.name for s in sources))
    return hashlib.md5(names.encode()).hexdigest()[:8]


# Section mapping for tier-based analysis
TIER_SECTIONS = {
    1: "all",  # Full analysis: all 12 sections
    2: [1, 3, 5, 7, 11],  # Key sections only
    3: [1, 11],  # Minimal: overview + verdict
}

SECTION_NAMES = {
    1: "Company Overview",
    2: "Industry Positioning & Competition",
    3: "Leadership & Group Strategy",
    4: "Culture, Philosophy & Talent",
    5: "Role-Specific Analysis",
    6: "Data Privacy & Compliance",
    7: "AI Strategy & Tech Trends",
    8: "Industry Policy & Regulation",
    9: "Career Mapping & Differentiation",
    10: "Interview Preparation Guide",
    11: "Overall Verdict & Scorecard",
    12: "Key References",
}


@dataclass
class AnalysisReport:
    """Structured analysis report for a company."""

    company: str
    region: str
    tier: int
    sections: dict[int, dict[str, Any]] = field(default_factory=dict)
    source_results: list[SourceResult] = field(default_factory=list)
    scorecard: Scorecard | None = None

    def to_markdown(self, template: str = "report_ko") -> str:
        """Render report as Markdown using Jinja2 templates.

        Parameters
        ----------
        template:
            Template name without extension — ``"report_ko"`` (default) or
            ``"report_en"``.
        """
        from hirekit.output.markdown import MarkdownRenderer

        renderer = MarkdownRenderer()
        return renderer.render(self, template=template)

    def to_dict(self) -> dict[str, Any]:
        """Serialize report as dict."""
        return {
            "company": self.company,
            "region": self.region,
            "tier": self.tier,
            "sections": self.sections,
            "scorecard": {
                "total": self.scorecard.total_score if self.scorecard else 0,
                "grade": self.scorecard.grade if self.scorecard else "N/A",
                "dimensions": [
                    {"name": d.name, "label": d.label, "weight": d.weight,
                     "score": d.score, "evidence": d.evidence,
                     "confidence": d.confidence, "source": d.source}
                    for d in (self.scorecard.dimensions if self.scorecard else [])
                ],
            },
            "sources": [r.as_reference() for r in self.source_results],
        }

    def to_rich(self) -> Panel:
        """Render report for terminal display."""
        text = Text()
        text.append(f"{self.company}\n", style="bold cyan")
        text.append(f"Grade: {self.scorecard.grade if self.scorecard else 'N/A'} | ", style="bold")
        text.append(f"Score: {self.scorecard.total_score:.0f}/100\n" if self.scorecard else "")
        text.append(f"Sources: {len(self.source_results)} collected\n")

        for section_num in sorted(self.sections):
            name = SECTION_NAMES.get(section_num, f"Section {section_num}")
            text.append(f"\n[{section_num}] {name}\n", style="bold yellow")

        return Panel(text, title="Analysis Report", border_style="green")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisReport":
        scorecard_payload = payload.get("scorecard") or {}
        scorecard = None
        dimensions_payload = scorecard_payload.get("dimensions", [])
        if dimensions_payload:
            dimensions = [
                ScoreDimension(
                    name=d.get("name", ""),
                    label=d.get("label", ""),
                    weight=float(d.get("weight", 0.0)),
                    score=float(d.get("score", 0.0)),
                    evidence=d.get("evidence", ""),
                    source=d.get("source", ""),
                    confidence=d.get("confidence", ""),
                )
                for d in dimensions_payload
            ]
            scorecard = Scorecard(
                company=payload.get("company", ""),
                dimensions=dimensions,
            )

        source_results = [
            SourceResult(
                source_name=s.get("name", ""),
                section=s.get("section", ""),
                url=s.get("url", ""),
                collected_at=s.get("collected_at", ""),
                effective_at=s.get("effective_at", ""),
                evidence_id=s.get("evidence_id", ""),
                confidence=float(s.get("confidence", 1.0)),
                trust_label=s.get("trust_label", "verified"),
                publication_boundary=s.get("publication_boundary", "internal_only"),
            )
            for s in payload.get("sources", [])
        ]

        return cls(
            company=payload.get("company", ""),
            region=payload.get("region", "kr"),
            tier=int(payload.get("tier", 1)),
            sections=payload.get("sections", {}),
            source_results=source_results,
            scorecard=scorecard,
        )


class CompanyAnalyzer:
    """Main orchestrator for company analysis."""

    def __init__(self, config: HireKitConfig, use_llm: bool = True):
        self.config = config
        self.cache = Cache(ttl_hours=config.analysis.cache_ttl_hours)
        self.llm: BaseLLM = self._init_llm() if use_llm else NoLLM()

    @staticmethod
    def _ensure_sources_registered() -> None:
        """Import all built-in source modules to trigger @register decorators."""
        try:
            from hirekit.sources.global_ import (  # noqa: F401
                brave_search,
                company_website,
                credible_news,
                exa_search,
                github,
                google_news,
                medium_velog,
            )
            from hirekit.sources.kr import (  # noqa: F401
                dart,
                job_postings,
                military_service,
                naver_news,
                naver_search,
                pension,
                tech_blog,
            )
        except ImportError:
            pass

    def _init_llm(self) -> BaseLLM:
        """Initialize LLM based on config."""
        provider = self.config.llm.provider
        if provider == "none":
            return NoLLM()

        try:
            if provider == "openai":
                from hirekit.llm.openai import OpenAIAdapter
                return OpenAIAdapter(model=self.config.llm.model)
            elif provider == "anthropic":
                from hirekit.llm.anthropic import AnthropicAdapter
                return AnthropicAdapter(model=self.config.llm.model)
            elif provider == "ollama":
                adapter_module = import_module("hirekit.llm.ollama")
                return adapter_module.OllamaAdapter(model=self.config.llm.model)
        except ImportError:
            pass

        return NoLLM()

    def analyze(self, company: str, region: str = "kr", tier: int = 1) -> AnalysisReport:
        """Run full analysis pipeline for a company."""
        # 1. Discover and register all built-in sources
        self._ensure_sources_registered()
        SourceRegistry.discover_plugins()
        sources = SourceRegistry.get_available(region=region)
        # Also include global sources regardless of region
        if region != "global":
            global_sources = SourceRegistry.get_available(region="global")
            seen = {s.name for s in sources}
            sources.extend(s for s in global_sources if s.name not in seen)

        disabled = set(self.config.sources.disabled)
        sources = [s for s in sources if s.name not in disabled]

        # 2. Check cache (key includes source hash so config changes bust the cache)
        source_hash = _source_hash(sources)
        cache_key = f"analysis:{company}:{region}:{tier}:{source_hash}"
        cached = self.cache.get(cache_key)
        if cached:
            return AnalysisReport.from_dict(cached)

        # 3. Collect data in parallel
        results = collect_parallel(
            sources=sources,
            company=company,
            max_workers=self.config.analysis.parallel_workers,
        )

        # 4. Build report sections from collected data
        report = AnalysisReport(
            company=company,
            region=region,
            tier=tier,
            source_results=results,
        )

        # Group results by section
        section_data: dict[str, list[SourceResult]] = {}
        for r in results:
            section_data.setdefault(r.section, []).append(r)

        # Map source sections to report sections
        section_mapping = {
            "overview": 1, "financials": 1,
            "industry": 2, "competition": 2,
            "leadership": 3, "strategy": 3,
            "vision": 3, "future": 3, "direction": 3,
            "culture": 4, "values": 4,
            "role": 5, "job": 5,
            "privacy": 6, "compliance": 6,
            "ai": 7, "tech": 7, "ai_strategy": 7,
            "regulation": 8, "policy": 8,
        }

        for section_key, section_results in section_data.items():
            section_num = section_mapping.get(section_key, 12)
            if section_num not in report.sections:
                report.sections[section_num] = {}
            for r in section_results:
                report.sections[section_num].update(r.data)

        # 5. Create scorecard with data-driven scoring
        report.scorecard = create_default_scorecard(company)
        self._score_from_data(report)

        # 6. LLM enhancement (if available)
        if self.llm.is_available():
            self._enhance_with_llm(report)

        # 7. Cache the result for future calls
        self.cache.set(cache_key, report.to_dict())

        return report

    # ------------------------------------------------------------------
    # Content-based scoring helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _confidence_from_sources(
        expected_sources: list[str],
        source_data: Mapping[str, object],
        source_results: list[SourceResult] | None = None,
    ) -> str:
        if source_results is not None:
            confidence_rules = import_module("hirekit.engine.confidence_rules")
            return confidence_rules.derive_confidence(expected_sources, source_results)
        matched = sum(1 for s in expected_sources if s in source_data)
        if matched >= 3:
            return "high"
        if matched >= 1:
            return "medium"
        return "low"

    @staticmethod
    def _parse_financial_amount(s: str | int | float) -> int:
        """Parse raw financial string (e.g. '1,234,567') to int."""
        if isinstance(s, (int, float)):
            return int(s)
        if not s or not isinstance(s, str):
            return 0
        try:
            return int(s.replace(",", "").strip())
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _growth_rate(current: int, previous: int) -> float | None:
        """Calculate YoY growth rate. Returns None if not computable."""
        if previous == 0:
            return None
        return (current - previous) / abs(previous)

    def _score_from_data(self, report: AnalysisReport) -> None:
        """Fill scorecard from collected data — content-based scoring."""
        if not report.scorecard:
            return

        def evidence_refs(expected_sources: list[str]) -> str:
            return ", ".join(
                r.evidence_id for r in report.source_results if r.source_name in expected_sources
            )

        overview = report.sections.get(1, {})
        source_data: dict[str, object] = {r.source_name: r.data for r in report.source_results}
        sections_filled = set(report.sections.keys())
        n_sources = len(report.source_results)

        for dim in report.scorecard.dimensions:
            if dim.name == "growth":
                dim.score, dim.evidence = self._score_growth(overview)
                dim.source = evidence_refs(["dart", "ir_report"])
                dim.confidence = self._confidence_from_sources(
                    ["dart", "ir_report"], source_data, report.source_results,
                )
            elif dim.name == "compensation":
                dim.score, dim.evidence = self._score_compensation(overview)
                dim.source = evidence_refs(["dart", "pension", "nts_biz"])
                dim.confidence = self._confidence_from_sources(
                    ["dart", "pension", "nts_biz"], source_data, report.source_results,
                )
            elif dim.name == "culture_fit":
                dim.score, dim.evidence = self._score_culture(
                    sections_filled, source_data, report.source_results,
                )
                dim.source = evidence_refs(["naver_search", "exa_search", "community_review"])
                dim.confidence = self._confidence_from_sources(
                    ["naver_search", "exa_search", "community_review"], source_data, report.source_results,
                )
            elif dim.name == "job_fit":
                dim.score, dim.evidence = self._score_job_fit(
                    sections_filled, source_data,
                )
                dim.source = evidence_refs(["github", "tech_blog", "medium_velog"])
                dim.confidence = self._confidence_from_sources(
                    ["github", "tech_blog", "medium_velog"], source_data, report.source_results,
                )
            elif dim.name == "career_leverage":
                dim.score, dim.evidence = self._score_career_leverage(
                    overview, n_sources, source_data,
                )
                dim.source = evidence_refs(["dart", "google_news", "credible_news", "naver_news"])
                dim.confidence = self._confidence_from_sources(
                    ["dart", "google_news", "credible_news", "naver_news"], source_data, report.source_results,
                )

    def _score_growth(self, overview: dict[str, Any]) -> tuple[float, str]:
        """Score growth from actual revenue/profit growth rates."""
        score = 2.5  # baseline when no data
        evidence_parts: list[str] = []

        financials = overview.get("financials", [])
        if not isinstance(financials, list) or not financials:
            return score, "재무 데이터 없음"

        # Find revenue and operating profit
        for item in financials:
            if not isinstance(item, dict):
                continue
            account = item.get("account", "")
            cur = self._parse_financial_amount(
                item.get("current_amount", item.get("current", "")),
            )
            prev = self._parse_financial_amount(
                item.get("previous_amount", item.get("previous", "")),
            )

            rate = self._growth_rate(cur, prev)
            if rate is None:
                continue

            pct = rate * 100
            if "매출" in account:
                # Revenue growth scoring
                if pct > 30:
                    score = max(score, 4.5)
                elif pct > 15:
                    score = max(score, 4.0)
                elif pct > 5:
                    score = max(score, 3.5)
                elif pct > 0:
                    score = max(score, 3.0)
                else:
                    score = max(score, 2.0)
                evidence_parts.append(f"매출 성장률 {pct:+.1f}%")

            elif "영업이익" in account:
                if pct > 20:
                    score = min(5.0, score + 0.5)
                elif pct < -20:
                    score = max(1.0, score - 0.5)
                evidence_parts.append(f"영업이익 성장률 {pct:+.1f}%")

        if not evidence_parts:
            return 2.5, "성장률 계산 불가 (데이터 형식 불일치)"

        return min(5.0, score), "; ".join(evidence_parts)

    def _score_compensation(self, overview: dict[str, Any]) -> tuple[float, str]:
        """Score compensation from actual salary/tenure data."""
        employees = overview.get("employees", [])
        evidence_parts: list[str] = []

        if not isinstance(employees, list) or not employees:
            return 2.5, "급여 데이터 없음"

        total_salary = 0
        total_headcount = 0
        max_tenure = 0.0

        for emp in employees:
            if not isinstance(emp, dict):
                continue
            salary = self._parse_financial_amount(emp.get("avg_salary", "0"))
            headcount = self._parse_financial_amount(emp.get("headcount", "0"))
            total_salary += salary * headcount
            total_headcount += headcount

            tenure_str = emp.get("avg_tenure_year", "")
            try:
                tenure = float(str(tenure_str).replace("년", "").strip()) if tenure_str else 0
                max_tenure = max(max_tenure, tenure)
            except (ValueError, TypeError):
                pass

        # Average annual salary (DART reports in 백만원)
        if total_headcount > 0 and total_salary > 0:
            avg_salary_m = total_salary / total_headcount  # 백만원
            if avg_salary_m > 80:  # > 8천만원
                score = 4.5
            elif avg_salary_m > 60:  # > 6천만원
                score = 4.0
            elif avg_salary_m > 45:  # > 4500만원
                score = 3.5
            elif avg_salary_m > 30:  # > 3천만원
                score = 3.0
            else:
                score = 2.5
            evidence_parts.append(f"평균 연봉 {avg_salary_m:.0f}백만원")
        else:
            score = 3.0  # data exists but salary not parseable

        # Tenure bonus
        if max_tenure > 7:
            score = min(5.0, score + 0.3)
            evidence_parts.append(f"평균 근속 {max_tenure:.1f}년 (장기)")
        elif max_tenure > 4:
            evidence_parts.append(f"평균 근속 {max_tenure:.1f}년")
        elif max_tenure > 0:
            score = max(1.0, score - 0.2)
            evidence_parts.append(f"평균 근속 {max_tenure:.1f}년 (단기)")

        if total_headcount > 0:
            evidence_parts.append(f"직원 {total_headcount:,}명")

        return min(5.0, score), "; ".join(evidence_parts) if evidence_parts else "급여 데이터 파싱 불가"

    def _score_culture(
        self, sections_filled: set[int], source_data: dict[str, object],
        source_results: list[SourceResult],
    ) -> tuple[float, str]:
        """Score culture from review volume and diversity."""
        score = 2.5
        evidence_parts: list[str] = []

        # Count review sources that returned data
        review_sources = {
            "naver_search": "네이버 블로그/카페",
            "exa_search": "Exa 딥서치",
            "community_review": "커뮤니티 리뷰",
        }
        review_count = 0
        for src, label in review_sources.items():
            if src in source_data:
                review_count += 1
                evidence_parts.append(label)

        # More diverse review sources = higher confidence
        if review_count >= 3:
            score = 4.0
        elif review_count >= 2:
            score = 3.5
        elif review_count >= 1:
            score = 3.0

        # Culture section filled (section 4)
        if 4 in sections_filled:
            culture_data = source_data.get("naver_search", {})
            if isinstance(culture_data, dict):
                for key in ("naver_blog", "naver_cafe"):
                    items = culture_data.get(key, [])
                    if isinstance(items, list) and len(items) >= 3:
                        score = min(5.0, score + 0.3)
                        evidence_parts.append(f"{key} {len(items)}건")

        confidence_rules = import_module("hirekit.engine.confidence_rules")
        labels = confidence_rules.culture_signal_labels(source_results)
        if labels:
            evidence_parts.append("문화 신호: " + ", ".join(labels))

        if not evidence_parts:
            return 2.5, "문화 리뷰 데이터 없음"

        return min(5.0, score), "; ".join(evidence_parts)

    def _score_job_fit(
        self, sections_filled: set[int], source_data: dict[str, object],
    ) -> tuple[float, str]:
        """Score job fit from GitHub score and tech data."""
        score = 2.5
        evidence_parts: list[str] = []

        # GitHub tech maturity score (0-100)
        gh_data = source_data.get("github", {})
        gh_score = gh_data.get("total_score", 0) if isinstance(gh_data, dict) else 0
        if gh_score:
            if gh_score >= 70:
                score = 4.5
            elif gh_score >= 50:
                score = 4.0
            elif gh_score >= 30:
                score = 3.5
            else:
                score = 3.0
            evidence_parts.append(f"GitHub 기술 성숙도 {gh_score}/100")

            # Bonus details
            repos = gh_data.get("public_repos", 0) if isinstance(gh_data, dict) else 0
            if repos:
                evidence_parts.append(f"공개 레포 {repos}개")

        # Tech section data (section 7)
        if 7 in sections_filled:
            score = min(5.0, score + 0.3)
            evidence_parts.append("기술 스택 데이터 수집됨")

        # Tech blog presence
        if "tech_blog" in source_data:
            score = min(5.0, score + 0.3)
            evidence_parts.append("기술 블로그 운영 중")

        if not evidence_parts:
            return 2.5, "기술 데이터 없음"

        return min(5.0, score), "; ".join(evidence_parts)

    def _score_career_leverage(
        self, overview: dict[str, Any], n_sources: int, source_data: dict[str, object],
    ) -> tuple[float, str]:
        """Score career leverage from company size, brand, and tech reputation."""
        score = 2.5
        evidence_parts: list[str] = []

        # Company size from employee data
        employees = overview.get("employees", [])
        total_headcount = 0
        if isinstance(employees, list):
            for emp in employees:
                if isinstance(emp, dict):
                    total_headcount += self._parse_financial_amount(
                        emp.get("headcount", "0"),
                    )

        if total_headcount > 5000:
            score = 4.0
            evidence_parts.append(f"대기업 ({total_headcount:,}명)")
        elif total_headcount > 1000:
            score = 3.5
            evidence_parts.append(f"중견기업 ({total_headcount:,}명)")
        elif total_headcount > 200:
            score = 3.0
            evidence_parts.append(f"중소기업 ({total_headcount:,}명)")
        elif total_headcount > 0:
            evidence_parts.append(f"소규모 ({total_headcount:,}명)")

        # Brand recognition: news coverage volume
        news_count = 0
        for src in ("google_news", "credible_news", "naver_news"):
            data = source_data.get(src, {})
            if isinstance(data, dict):
                for key in ("articles", "results", "items"):
                    items = data.get(key, [])
                    if isinstance(items, list):
                        news_count += len(items)

        if news_count > 10:
            score = min(5.0, score + 0.5)
            evidence_parts.append(f"뉴스 {news_count}건 (높은 인지도)")
        elif news_count > 3:
            score = min(5.0, score + 0.3)
            evidence_parts.append(f"뉴스 {news_count}건")

        # GitHub presence = tech brand
        if "github" in source_data:
            github_data = source_data["github"]
            gh_score = github_data.get("total_score", 0) if isinstance(github_data, dict) else 0
            if gh_score >= 50:
                score = min(5.0, score + 0.3)
                evidence_parts.append("오픈소스 활동 활발")

        # Data coverage breadth
        if n_sources >= 8:
            score = min(5.0, score + 0.3)
            evidence_parts.append(f"데이터 {n_sources}개 소스 수집")

        if not evidence_parts:
            return 2.5, f"데이터 {n_sources}개 소스"

        return min(5.0, score), "; ".join(evidence_parts)

    def _enhance_with_llm(self, report: AnalysisReport) -> None:
        """Run sectioned LLM pipeline and merge results into report sections."""
        from hirekit.engine.llm_pipeline import LLMPipeline

        pipeline = LLMPipeline(self.llm)
        llm_sections = pipeline.analyze(report.source_results, report.company)
        for num, content in llm_sections.items():
            report.sections.setdefault(num, {})
            report.sections[num]["analysis"] = content
