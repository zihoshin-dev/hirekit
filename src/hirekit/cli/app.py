"""HireKit CLI — main entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hirekit import __version__
from hirekit.core.config import ensure_config_dir, load_config

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
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
) -> None:
    """HireKit — Research companies. Match jobs. Ace interviews."""


@app.command()
def analyze(
    company: str = typer.Argument(help="Company name to analyze (e.g., '카카오', 'toss')"),
    region: str = typer.Option("kr", "--region", "-r", help="Region: kr, us, global"),
    output: str = typer.Option("markdown", "--output", "-o", help="Output format: markdown, json, terminal"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM analysis, use template-only mode"),
    tier: int = typer.Option(1, "--tier", "-t", help="Analysis depth: 1 (full), 2 (key sections), 3 (minimal)"),
) -> None:
    """Analyze a company — collect data from multiple sources and generate a report."""
    config = load_config()

    console.print(Panel(
        f"[bold]Analyzing:[/bold] {company}\n"
        f"[bold]Region:[/bold] {region}  [bold]Tier:[/bold] {tier}  [bold]LLM:[/bold] {'off' if no_llm else config.llm.provider}",
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


if __name__ == "__main__":
    app()
