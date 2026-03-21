"""HireKit CLI — main entry point."""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hirekit import __version__
from hirekit.core.config import DEFAULT_CONFIG_DIR, ensure_config_dir, load_config

# Auto-load .env from project dir and ~/.hirekit/.env
load_dotenv()
load_dotenv(DEFAULT_CONFIG_DIR / ".env")

app = typer.Typer(
    name="hirekit",
    help="AI-powered company analysis and interview preparation CLI.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold]HireKit[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
) -> None:
    """HireKit — Research companies. Match jobs. Ace interviews."""


@app.command()
def analyze(
    company: str = typer.Argument(help="Company name (e.g., '카카오', 'toss')"),
    region: str = typer.Option("kr", "--region", "-r", help="Region: kr, us, global"),
    output: str = typer.Option("markdown", "--output", "-o", help="markdown, json, terminal"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM, template-only"),
    tier: int = typer.Option(1, "--tier", "-t", help="Depth: 1 (full), 2 (key), 3 (min)"),
) -> None:
    """Analyze a company — collect data from multiple sources and generate a report."""
    config = load_config()

    console.print(Panel(
        f"[bold]Analyzing:[/bold] {company}\n"
        f"[bold]Region:[/bold] {region}  [bold]Tier:[/bold] {tier}  "
        f"[bold]LLM:[/bold] {'off' if no_llm else config.llm.provider}",
        title="[bold blue]HireKit Analysis[/bold blue]",
        border_style="blue",
    ))

    # Import here to avoid circular imports and speed up CLI startup
    from hirekit.engine.company_analyzer import CompanyAnalyzer

    analyzer = CompanyAnalyzer(config=config, use_llm=not no_llm)

    with console.status("[bold green]Collecting data from sources..."):
        report = analyzer.analyze(company=company, region=region, tier=tier)

    if output == "terminal":
        console.print(report.to_rich())
    elif output == "json":
        import json
        console.print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        out_path = Path(config.output.directory) / f"{company}_analysis.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report.to_markdown(), encoding="utf-8")
        console.print(f"\n[green]Report saved:[/green] {out_path}")

    # Show scorecard summary
    if report.scorecard:
        table = Table(title=f"{company} Scorecard")
        table.add_column("Dimension", style="cyan")
        table.add_column("Weight", justify="right")
        table.add_column("Score", justify="right")
        table.add_column("Evidence")

        for d in report.scorecard.dimensions:
            score_str = f"{d.score:.1f}/5" if d.score > 0 else "-"
            table.add_row(d.label, f"{d.weight:.0%}", score_str, d.evidence[:60])

        table.add_row(
            "[bold]Total[/bold]", "", f"[bold]{report.scorecard.total_score:.0f}/100[/bold]",
            f"Grade [bold]{report.scorecard.grade}[/bold]",
        )
        console.print(table)


@app.command()
def configure() -> None:
    """Set up HireKit configuration (API keys, preferences)."""
    config_dir = ensure_config_dir()
    config_file = config_dir / "config.toml"

    if config_file.exists():
        console.print(f"[yellow]Config already exists:[/yellow] {config_file}")
        console.print("Edit it directly or delete to re-initialize.")
        return

    # Create default config
    default_config = """\
[analysis]
default_region = "kr"
cache_ttl_hours = 168
parallel_workers = 5

[llm]
provider = "none"  # openai, anthropic, ollama, none
model = "gpt-4o-mini"
temperature = 0.3

[sources]
enabled = ["dart", "github", "naver_news"]

[output]
format = "markdown"
directory = "./reports"
"""
    config_file.write_text(default_config, encoding="utf-8")
    console.print(f"[green]Config created:[/green] {config_file}")

    # Create .env template
    env_file = config_dir / ".env"
    if not env_file.exists():
        env_file.write_text(
            "# HireKit API Keys\n"
            "# DART_API_KEY=your_dart_api_key_here\n"
            "# OPENAI_API_KEY=your_openai_key_here\n"
            "# ANTHROPIC_API_KEY=your_anthropic_key_here\n",
            encoding="utf-8",
        )
        console.print(f"[green]Env template:[/green] {env_file}")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Get a DART API key: https://opendart.fss.or.kr/")
    console.print("  2. Edit ~/.hirekit/.env with your API keys")
    console.print("  3. Run: [cyan]hirekit analyze 카카오[/cyan]")


@app.command()
def sources() -> None:
    """List available data sources and their status."""
    from hirekit.sources.base import SourceRegistry

    SourceRegistry.discover_plugins()
    all_sources = SourceRegistry.get_all()

    table = Table(title="Data Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Region")
    table.add_column("Sections")
    table.add_column("API Key")
    table.add_column("Status")

    for name, source_cls in sorted(all_sources.items()):
        source = source_cls()
        available = source.is_available()
        table.add_row(
            name,
            source.region.upper(),
            ", ".join(source.sections),
            source.api_key_env_var or "-",
            "[green]Ready[/green]" if available else "[red]Not configured[/red]",
        )

    console.print(table)


@app.command()
def match(
    jd_source: str = typer.Argument(help="JD URL or text file path"),
    profile: str = typer.Option("", "--profile", "-p", help="Career profile YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="markdown, terminal"),
) -> None:
    """Match a job description against your career profile."""
    from hirekit.engine.jd_matcher import JDMatcher

    config = load_config()
    llm = _get_llm(config)
    matcher = JDMatcher(llm=llm)

    # Load profile if provided
    user_profile = _load_profile(profile)

    # Check if jd_source is a file
    jd_path = Path(jd_source)
    if jd_path.exists():
        jd_source = jd_path.read_text(encoding="utf-8")

    with console.status("[bold green]Analyzing job description..."):
        analysis = matcher.analyze(jd_source=jd_source, profile=user_profile)

    if output == "terminal":
        console.print(Panel(
            f"[bold]{analysis.title}[/bold] at {analysis.company}\n"
            f"Match: [bold]{analysis.match_score:.0f}/100[/bold] "
            f"(Grade {analysis.match_grade})",
            title="[bold blue]JD Match[/bold blue]",
            border_style="blue",
        ))
        if analysis.gaps:
            console.print("\n[red]Gaps:[/red]")
            for g in analysis.gaps[:5]:
                console.print(f"  - {g}")
        if analysis.strengths:
            console.print("\n[green]Strengths:[/green]")
            for s in analysis.strengths[:5]:
                console.print(f"  - {s}")
    else:
        out_path = Path(config.output.directory) / "jd_match.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(analysis.to_markdown(), encoding="utf-8")
        console.print(f"[green]Report saved:[/green] {out_path}")


@app.command()
def interview(
    company: str = typer.Argument(help="Company name"),
    position: str = typer.Option("", "--position", "-p", help="Target position"),
    profile: str = typer.Option("", "--profile", help="Career profile YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="markdown, terminal"),
) -> None:
    """Generate interview preparation guide for a company."""
    from hirekit.engine.interview_prep import InterviewPrep

    config = load_config()
    llm = _get_llm(config)
    prep = InterviewPrep(llm=llm)

    user_profile = _load_profile(profile)

    with console.status(f"[bold green]Preparing interview guide for {company}..."):
        guide = prep.prepare(
            company=company,
            position=position,
            profile=user_profile,
        )

    if output == "terminal":
        console.print(Panel(
            f"[bold]{company}[/bold] — {position or 'General'}\n"
            f"Questions: {len(guide.common_questions)} common, "
            f"{len(guide.technical_questions)} technical, "
            f"{len(guide.behavioral_questions)} behavioral\n"
            f"Reverse questions: {len(guide.reverse_questions)}",
            title="[bold blue]Interview Prep[/bold blue]",
            border_style="blue",
        ))
        for q in guide.common_questions:
            console.print(f"\n[cyan]Q:[/cyan] {q['question']}")
            console.print(f"  [dim]{q.get('answer', '')}[/dim]")
    else:
        out_path = Path(config.output.directory) / f"{company}_interview.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(guide.to_markdown(), encoding="utf-8")
        console.print(f"[green]Report saved:[/green] {out_path}")


@app.command()
def coverletter(
    company: str = typer.Argument(help="Company name (e.g., '카카오', 'toss')"),
    position: str = typer.Option("", "--position", "-p", help="Target position (e.g., PM)"),
    profile: str = typer.Option("", "--profile", help="Career profile YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="markdown, terminal"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM, rule-based only"),
) -> None:
    """Generate a Korean 자기소개서 (cover letter) draft with coaching feedback."""
    from hirekit.engine.cover_letter import CoverLetterCoach

    config = load_config()
    llm = _get_llm(config) if not no_llm else None
    coach = CoverLetterCoach(llm=llm)

    user_profile = _load_profile(profile)

    with console.status(f"[bold green]{company} 자기소개서 초안 작성 중..."):
        draft = coach.draft(
            company=company,
            position=position,
            profile=user_profile,
        )

    if output == "terminal":
        console.print(Panel(
            f"[bold]{company}[/bold] — {position or '미지정'}\n"
            f"종합 점수: [bold]{draft.overall_score:.0f}/100[/bold] "
            f"(Grade {draft.grade})\n"
            f"섹션 수: {len(draft.sections)}개",
            title="[bold blue]자기소개서 코치[/bold blue]",
            border_style="blue",
        ))
        for section in draft.sections:
            console.print(f"\n[cyan]## {section.title}[/cyan]")
            console.print(section.content)
            console.print(
                f"[dim]점수: {section.score:.0f}/100 | "
                f"글자 수: {section.word_count}자[/dim]"
            )
            if section.feedback:
                console.print("[yellow]피드백:[/yellow]")
                for fb in section.feedback:
                    console.print(f"  - {fb}")
    else:
        out_path = Path(config.output.directory) / f"{company}_coverletter.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(draft.to_markdown(), encoding="utf-8")
        console.print(f"[green]자기소개서 저장:[/green] {out_path}")

        table = Table(title=f"{company} 자기소개서 점수")
        table.add_column("항목", style="cyan")
        table.add_column("글자 수", justify="right")
        table.add_column("점수", justify="right")
        table.add_column("등급", justify="center")

        for s in draft.sections:
            table.add_row(s.title, str(s.word_count), f"{s.score:.0f}/100", s.grade)

        table.add_row(
            "[bold]종합[/bold]", "", f"[bold]{draft.overall_score:.0f}/100[/bold]",
            f"[bold]{draft.grade}[/bold]",
        )
        console.print(table)


@app.command()
def pipeline(
    company: str = typer.Argument(help="Company name"),
    jd: str = typer.Option("", "--jd", help="JD URL or text file"),
    resume_file: str = typer.Option("", "--resume", help="Resume file (md/txt/pdf)"),
    position: str = typer.Option("", "--position", "-p", help="Target position"),
    profile: str = typer.Option("", "--profile", help="Career profile YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="Output format"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM"),
) -> None:
    """Run full analysis pipeline: analyze + match + interview + coverletter + strategy."""
    from hirekit.engine.company_analyzer import CompanyAnalyzer
    from hirekit.engine.cover_letter import CoverLetterCoach
    from hirekit.engine.interview_prep import InterviewPrep
    from hirekit.engine.jd_matcher import JDMatcher
    from hirekit.engine.resume_advisor import ResumeAdvisor

    config = load_config()
    llm = _get_llm(config) if not no_llm else None
    user_profile = _load_profile(profile)

    console.print(Panel(
        f"[bold]Company:[/bold] {company}\n"
        f"[bold]Position:[/bold] {position or '미지정'}  "
        f"[bold]LLM:[/bold] {'off' if no_llm else config.llm.provider}",
        title="[bold blue]HireKit Pipeline[/bold blue]",
        border_style="blue",
    ))

    # Step 1: Company analysis
    console.print("\n[bold cyan][1/5] 기업 분석 중...[/bold cyan]")
    analyzer = CompanyAnalyzer(config=config, use_llm=not no_llm)
    with console.status("[bold green]Collecting company data..."):
        report = analyzer.analyze(company=company)

    # Step 2: JD analysis (optional)
    jd_analysis = None
    jd_text = ""
    if jd:
        console.print("[bold cyan][2/5] JD 분석 중...[/bold cyan]")
        jd_path = Path(jd)
        jd_source = jd_path.read_text(encoding="utf-8") if jd_path.exists() else jd
        jd_text = jd_source
        matcher = JDMatcher(llm=llm)
        with console.status("[bold green]Analyzing job description..."):
            jd_analysis = matcher.analyze(jd_source=jd_source, profile=user_profile)
        # Try to override company name from JD if found
        if jd_analysis.company and not company:
            company = jd_analysis.company
    else:
        console.print("[dim][2/5] JD 분석 건너뜀 (--jd 미지정)[/dim]")

    # Step 3: Resume review (optional)
    resume_feedback = None
    if resume_file:
        console.print("[bold cyan][3/5] 이력서 리뷰 중...[/bold cyan]")
        advisor = ResumeAdvisor(llm=llm)
        with console.status("[bold green]Reviewing resume..."):
            resume_feedback = advisor.review(
                resume_path=resume_file, jd_text=jd_text, profile=user_profile
            )
    else:
        console.print("[dim][3/5] 이력서 리뷰 건너뜀 (--resume 미지정)[/dim]")

    # Step 4: Interview prep
    console.print("[bold cyan][4/5] 면접 준비 가이드 생성 중...[/bold cyan]")
    prep = InterviewPrep(llm=llm)
    with console.status("[bold green]Generating interview guide..."):
        guide = prep.prepare(
            company=company,
            position=position,
            report=report,
            profile=user_profile,
        )

    # Step 5: Cover letter
    console.print("[bold cyan][5/5] 자기소개서 초안 작성 중...[/bold cyan]")
    coach = CoverLetterCoach(llm=llm)
    with console.status("[bold green]Drafting cover letter..."):
        cover_draft = coach.draft(
            company=company,
            position=position,
            profile=user_profile,
            company_report=report.to_dict(),
        )

    # Go/Hold/Pass verdict
    combined = report.scorecard.total_score * 0.6 if report.scorecard else 0.0
    if jd_analysis:
        combined += jd_analysis.match_score * 0.4
    if combined >= 65:
        verdict = "Go"
        verdict_style = "bold green"
    elif combined >= 40:
        verdict = "Hold"
        verdict_style = "bold yellow"
    else:
        verdict = "Pass"
        verdict_style = "bold red"

    if output == "terminal":
        console.print(Panel(
            f"[bold]기업 점수:[/bold] {report.scorecard.total_score:.0f}/100 "
            f"(Grade {report.scorecard.grade})\n"
            + (
                f"[bold]JD 매칭:[/bold] {jd_analysis.match_score:.0f}/100\n"
                if jd_analysis else ""
            )
            + (
                f"[bold]이력서 점수:[/bold] {resume_feedback.overall_score:.0f}/100\n"
                if resume_feedback else ""
            )
            + f"[bold]면접 질문:[/bold] {len(guide.common_questions)}개\n"
            + f"[bold]자소서 점수:[/bold] {cover_draft.overall_score:.0f}/100\n"
            + f"[{verdict_style}]Verdict: {verdict}[/{verdict_style}]",
            title="[bold blue]Pipeline Result[/bold blue]",
            border_style="blue",
        ))
    else:
        # Build integrated markdown report
        lines = [
            f"# HireKit Pipeline Report: {company}",
            f"**Position:** {position or '미지정'}",
            f"**Verdict:** {verdict} (combined score: {combined:.0f}/100)",
            "",
            "---",
            "",
            "## 1. 기업 분석",
            report.to_markdown(),
            "",
            "---",
            "",
        ]

        if jd_analysis:
            lines += [
                "## 2. JD 매칭",
                jd_analysis.to_markdown(),
                "",
                "---",
                "",
            ]

        if resume_feedback:
            lines += [
                "## 3. 이력서 리뷰",
                resume_feedback.to_markdown(),
                "",
                "---",
                "",
            ]

        lines += [
            "## 4. 면접 준비",
            guide.to_markdown(),
            "",
            "---",
            "",
            "## 5. 자기소개서",
            cover_draft.to_markdown(),
        ]

        out_path = Path(config.output.directory) / f"{company}_pipeline.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"\n[green]Pipeline report saved:[/green] {out_path}")

        # Summary table
        table = Table(title=f"{company} Pipeline Summary")
        table.add_column("단계", style="cyan")
        table.add_column("결과", justify="right")
        table.add_column("비고")

        table.add_row(
            "기업 분석",
            f"{report.scorecard.total_score:.0f}/100" if report.scorecard else "-",
            f"Grade {report.scorecard.grade}" if report.scorecard else "",
        )
        if jd_analysis:
            table.add_row(
                "JD 매칭",
                f"{jd_analysis.match_score:.0f}/100",
                f"Grade {jd_analysis.match_grade}",
            )
        if resume_feedback:
            table.add_row(
                "이력서",
                f"{resume_feedback.overall_score:.0f}/100",
                f"Grade {resume_feedback.grade}",
            )
        table.add_row("면접 질문", f"{len(guide.common_questions)}개", "")
        table.add_row(
            "자기소개서",
            f"{cover_draft.overall_score:.0f}/100",
            f"Grade {cover_draft.grade}",
        )
        table.add_row(
            "[bold]Verdict[/bold]",
            f"[{verdict_style}]{verdict}[/{verdict_style}]",
            f"Combined {combined:.0f}/100",
        )
        console.print(table)


@app.command()
def resume(
    file: str = typer.Argument(help="Resume file path (md, txt, pdf)"),
    jd: str = typer.Option("", "--jd", help="JD URL or text for targeted review"),
    profile: str = typer.Option("", "--profile", "-p", help="Career profile YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="markdown, terminal"),
) -> None:
    """Review and provide feedback on your resume."""
    from hirekit.engine.resume_advisor import ResumeAdvisor

    config = load_config()
    llm = _get_llm(config)
    advisor = ResumeAdvisor(llm=llm)

    user_profile = _load_profile(profile)

    # Resolve JD text
    jd_text = ""
    if jd:
        jd_path = Path(jd)
        if jd_path.exists():
            jd_text = jd_path.read_text(encoding="utf-8")
        elif jd.startswith("http"):
            import httpx
            try:
                resp = httpx.get(jd, timeout=10, follow_redirects=True)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                jd_text = soup.get_text(separator="\n", strip=True)[:5000]
            except Exception:
                console.print(f"[yellow]Could not fetch JD from {jd}[/yellow]")
        else:
            jd_text = jd

    with console.status("[bold green]Reviewing resume..."):
        feedback = advisor.review(
            resume_path=file, jd_text=jd_text, profile=user_profile
        )

    if output == "terminal":
        console.print(Panel(
            f"[bold]Score:[/bold] {feedback.overall_score:.0f}/100 "
            f"(Grade {feedback.grade})",
            title="[bold blue]Resume Review[/bold blue]",
            border_style="blue",
        ))
        if feedback.strengths:
            console.print("\n[green]Strengths:[/green]")
            for s in feedback.strengths:
                console.print(f"  + {s}")
        if feedback.improvements:
            console.print("\n[yellow]Improvements:[/yellow]")
            for i in feedback.improvements:
                console.print(f"  - {i}")
        if feedback.keyword_gaps:
            console.print("\n[red]Keyword gaps vs JD:[/red]")
            console.print(f"  {', '.join(feedback.keyword_gaps[:10])}")
    else:
        out_path = Path(config.output.directory) / "resume_review.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(feedback.to_markdown(), encoding="utf-8")
        console.print(f"[green]Report saved:[/green] {out_path}")


# --- Helpers ---

def _get_llm(config: HireKitConfig) -> BaseLLM:  # noqa: F821
    """Initialize LLM from config.

    Supported providers: openai, anthropic, gemini, ollama, none.
    """
    from hirekit.llm.base import NoLLM

    provider = config.llm.provider
    model = config.llm.model

    if provider == "none":
        return NoLLM()
    try:
        if provider == "openai":
            from hirekit.llm.openai import OpenAIAdapter
            return OpenAIAdapter(model=model)
        if provider == "anthropic":
            from hirekit.llm.anthropic import AnthropicAdapter
            return AnthropicAdapter(model=model)
        if provider == "gemini":
            from hirekit.llm.gemini import GeminiAdapter
            return GeminiAdapter(model=model)
        if provider == "ollama":
            from hirekit.llm.ollama import OllamaAdapter
            return OllamaAdapter(model=model)
    except ImportError:
        pass
    return NoLLM()


def _load_profile(path: str) -> dict | None:
    """Load career profile from YAML file."""
    if not path:
        # Check default location
        default = Path.home() / ".hirekit" / "profile.yaml"
        if default.exists():
            path = str(default)
        else:
            return None

    p = Path(path)
    if not p.exists():
        return None

    try:
        import yaml
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    except ImportError:
        # Fallback: basic YAML parsing without pyyaml
        return None


if __name__ == "__main__":
    app()
