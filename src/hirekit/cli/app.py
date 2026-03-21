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
    """Initialize LLM from config."""
    from hirekit.llm.base import NoLLM
    if config.llm.provider == "none":
        return NoLLM()
    try:
        if config.llm.provider == "openai":
            from hirekit.llm.openai import OpenAIAdapter
            return OpenAIAdapter(model=config.llm.model)
        if config.llm.provider == "anthropic":
            from hirekit.llm.anthropic import AnthropicAdapter
            return AnthropicAdapter(model=config.llm.model)
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
