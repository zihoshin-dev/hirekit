"""Company analysis orchestrator — collects data, scores, and generates reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rich.panel import Panel
from rich.text import Text

from hirekit.core.cache import Cache
from hirekit.core.config import HireKitConfig
from hirekit.core.parallel import collect_parallel
from hirekit.engine.scorer import Scorecard, create_default_scorecard
from hirekit.llm.base import BaseLLM, NoLLM
from hirekit.sources.base import SourceRegistry, SourceResult


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

    def to_markdown(self) -> str:
        """Render report as Markdown."""
        lines = [f"# {self.company} — Company Analysis Report\n"]
        lines.append(f"**Region:** {self.region.upper()} | **Tier:** {self.tier} | "
                      f"**Grade:** {self.scorecard.grade if self.scorecard else 'N/A'}\n")
        lines.append("---\n")

        for section_num in sorted(self.sections):
            section_name = SECTION_NAMES.get(section_num, f"Section {section_num}")
            content = self.sections[section_num]

            lines.append(f"## {section_num}. {section_name}\n")

            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, list):
                        lines.append(f"### {key}\n")
                        for item in value:
                            lines.append(f"- {item}")
                    elif isinstance(value, dict):
                        lines.append(f"### {key}\n")
                        for k, v in value.items():
                            lines.append(f"- **{k}**: {v}")
                    else:
                        lines.append(f"**{key}**: {value}\n")
            else:
                lines.append(str(content))

            lines.append("\n---\n")

        # References section
        if self.source_results:
            lines.append("## References\n")
            seen_urls: set[str] = set()
            for result in self.source_results:
                if result.url and result.url not in seen_urls:
                    lines.append(f"- [{result.source_name}]({result.url})")
                    seen_urls.add(result.url)

        return "\n".join(lines)

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
                     "score": d.score, "evidence": d.evidence}
                    for d in (self.scorecard.dimensions if self.scorecard else [])
                ],
            },
            "sources": [
                {"name": r.source_name, "section": r.section, "url": r.url}
                for r in self.source_results
            ],
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


class CompanyAnalyzer:
    """Main orchestrator for company analysis."""

    def __init__(self, config: HireKitConfig, use_llm: bool = True):
        self.config = config
        self.cache = Cache(ttl_hours=config.analysis.cache_ttl_hours)
        self.llm: BaseLLM = self._init_llm() if use_llm else NoLLM()

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
                from hirekit.llm.ollama import OllamaAdapter
                return OllamaAdapter(model=self.config.llm.model)
        except ImportError:
            pass

        return NoLLM()

    def analyze(self, company: str, region: str = "kr", tier: int = 1) -> AnalysisReport:
        """Run full analysis pipeline for a company."""
        # 1. Discover and filter sources
        SourceRegistry.discover_plugins()
        sources = SourceRegistry.get_available(region=region)
        enabled = set(self.config.sources.enabled)
        disabled = set(self.config.sources.disabled)
        sources = [s for s in sources if s.name in enabled and s.name not in disabled]

        # 2. Check cache
        cache_key = f"analysis:{company}:{region}:{tier}"
        cached = self.cache.get(cache_key)
        if cached:
            return AnalysisReport(**cached)

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
            "culture": 4, "values": 4,
            "role": 5, "job": 5,
            "privacy": 6, "compliance": 6,
            "ai": 7, "tech": 7,
            "regulation": 8, "policy": 8,
        }

        for section_key, section_results in section_data.items():
            section_num = section_mapping.get(section_key, 12)
            if section_num not in report.sections:
                report.sections[section_num] = {}
            for r in section_results:
                report.sections[section_num].update(r.data)

        # 5. Create scorecard
        report.scorecard = create_default_scorecard(company)

        # 6. LLM enhancement (if available)
        if self.llm.is_available() and not isinstance(self.llm, NoLLM):
            self._enhance_with_llm(report)

        return report

    def _enhance_with_llm(self, report: AnalysisReport) -> None:
        """Use LLM to generate analysis, fill scorecard, and create insights."""
        raw_data = "\n".join(r.raw for r in report.source_results if r.raw)
        if not raw_data:
            return

        prompt = (
            f"다음은 '{report.company}'에 대해 수집된 데이터입니다.\n\n"
            f"{raw_data[:8000]}\n\n"
            "위 데이터를 바탕으로:\n"
            "1. 각 스코어카드 차원(직무 적합도, 경력 레버리지, 성장성, 연봉/복지, 문화 Fit)에 "
            "1-5점 점수와 근거를 제시하세요.\n"
            "2. 이 기업의 핵심 강점과 리스크를 각 3개씩 제시하세요.\n"
            "3. 면접 시 활용할 수 있는 핵심 인사이트 3개를 제시하세요."
        )

        response = self.llm.generate(prompt=prompt, temperature=0.3)
        if response.text:
            report.sections.setdefault(11, {})["AI Analysis"] = response.text
