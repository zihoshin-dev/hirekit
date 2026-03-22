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

app = typer.Typer(
    name="hirekit",
    help="AI 기반 기업 분석 및 면접 준비 CLI.",
    no_args_is_help=True,
)
# stderr for human messages (status/progress), stdout for machine-parseable data
console = Console(stderr=True)


def _load_env() -> None:
    """Load .env files — called at CLI invocation, not at import time."""
    load_dotenv(DEFAULT_CONFIG_DIR / ".env")  # HireKit dedicated keys first
    load_dotenv()  # CWD .env can override


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
    """HireKit — 기업 조사, 공고 매칭, 면접 준비를 한 번에."""
    _load_env()


@app.command()
def analyze(
    company: str = typer.Argument(help="기업명 (예: '카카오', 'toss')"),
    region: str = typer.Option("kr", "--region", "-r", help="지역: kr, us, global"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식: markdown, json, terminal"),
    no_llm: bool = typer.Option(False, "--no-llm", help="LLM 생략, 템플릿 기반만 사용"),
    tier: int = typer.Option(1, "--tier", "-t", help="수집 깊이: 1(전체), 2(핵심), 3(최소)"),
) -> None:
    """기업 분석 — 여러 소스에서 데이터를 수집하고 리포트를 생성해요."""
    config = load_config()

    llm_label = "off" if no_llm else config.llm.provider
    console.print(Panel(
        f"[bold]분석 대상:[/bold] {company}\n"
        f"[bold]지역:[/bold] {region}  [bold]티어:[/bold] {tier}  "
        f"[bold]LLM:[/bold] {llm_label}",
        title="[bold blue]HireKit 기업 분석[/bold blue]",
        border_style="blue",
    ))

    # LLM 미설정 안내
    if not no_llm and config.llm.provider == "none":
        console.print(
            "[yellow]LLM 없이 데이터 기반 분석만 제공해요. "
            "LLM 분석을 원하면 [bold]hirekit configure[/bold]로 설정하세요.[/yellow]"
        )

    # Import here to avoid circular imports and speed up CLI startup
    from hirekit.engine.company_analyzer import CompanyAnalyzer

    analyzer = CompanyAnalyzer(config=config, use_llm=not no_llm)

    with console.status("[bold green]소스에서 데이터 수집 중..."):
        report = analyzer.analyze(company=company, region=region, tier=tier)

    console.print("[green]✓[/green] 데이터 수집 완료")

    if output == "terminal":
        console.print(report.to_rich())
    elif output == "json":
        import json
        import sys
        sys.stdout.write(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n")
    else:
        out_path = Path(config.output.directory) / f"{company}_analysis.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report.to_markdown(), encoding="utf-8")
        console.print(f"\n[green]리포트 저장:[/green] {out_path}")

    # Show scorecard summary
    if report.scorecard:
        table = Table(title=f"{company} 스코어카드")
        table.add_column("항목", style="cyan")
        table.add_column("가중치", justify="right")
        table.add_column("점수", justify="right")
        table.add_column("근거")

        for d in report.scorecard.dimensions:
            score_str = f"{d.score:.1f}/5" if d.score > 0 else "-"
            table.add_row(d.label, f"{d.weight:.0%}", score_str, d.evidence[:60])

        table.add_row(
            "[bold]종합[/bold]", "", f"[bold]{report.scorecard.total_score:.0f}/100[/bold]",
            f"등급 [bold]{report.scorecard.grade}[/bold]",
        )
        console.print(table)


@app.command()
def configure() -> None:
    """HireKit 설정 초기화 (API 키, 기본값 등)."""
    config_dir = ensure_config_dir()
    config_file = config_dir / "config.toml"

    if config_file.exists():
        console.print(f"[yellow]설정 파일이 이미 존재해요:[/yellow] {config_file}")
        console.print("직접 편집하거나 삭제 후 재실행하세요.")
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
    console.print(f"[green]설정 파일 생성:[/green] {config_file}")

    # Create .env template
    env_file = config_dir / ".env"
    if not env_file.exists():
        env_file.write_text(
            "# HireKit API 키\n"
            "# DART_API_KEY=your_dart_api_key_here\n"
            "# OPENAI_API_KEY=your_openai_key_here\n"
            "# ANTHROPIC_API_KEY=your_anthropic_key_here\n",
            encoding="utf-8",
        )
        console.print(f"[green]환경변수 템플릿 생성:[/green] {env_file}")

    console.print("\n[bold]다음 단계:[/bold]")
    console.print("  1. DART API 키 발급: https://opendart.fss.or.kr/")
    console.print("  2. ~/.hirekit/.env 에 API 키 입력")
    console.print("  3. 실행: [cyan]hirekit analyze 카카오[/cyan]")


@app.command()
def sources() -> None:
    """사용 가능한 데이터 소스와 설정 상태를 조회해요."""
    from hirekit.sources.base import SourceRegistry

    SourceRegistry.discover_plugins()
    all_sources = SourceRegistry.get_all()

    table = Table(title="데이터 소스 목록")
    table.add_column("이름", style="cyan")
    table.add_column("지역")
    table.add_column("섹션")
    table.add_column("API 키 환경변수")
    table.add_column("상태")

    for name, source_cls in sorted(all_sources.items()):
        source = source_cls()
        available = source.is_available()
        if available:
            status = "[green]사용 가능[/green]"
        elif source.api_key_env_var:
            status = f"[red]미설정[/red] — .env에 {source.api_key_env_var} 입력 필요"
        else:
            status = "[red]사용 불가[/red]"
        table.add_row(
            name,
            source.region.upper(),
            ", ".join(source.sections),
            source.api_key_env_var or "-",
            status,
        )

    console.print(table)


@app.command()
def match(
    jd_source: str = typer.Argument(help="채용공고 URL 또는 텍스트 파일 경로"),
    profile: str = typer.Option("", "--profile", "-p", help="커리어 프로필 YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식: markdown, terminal"),
) -> None:
    """채용공고와 커리어 프로필의 매칭도를 분석해요."""
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

    with console.status("[bold green]채용공고 분석 중..."):
        analysis = matcher.analyze(jd_source=jd_source, profile=user_profile)

    if output == "terminal":
        console.print(Panel(
            f"[bold]{analysis.title}[/bold] — {analysis.company}\n"
            f"매칭 점수: [bold]{analysis.match_score:.0f}/100[/bold] "
            f"(등급 {analysis.match_grade})",
            title="[bold blue]JD 매칭[/bold blue]",
            border_style="blue",
        ))
        if analysis.gaps:
            console.print("\n[red]부족한 부분:[/red]")
            for g in analysis.gaps[:5]:
                console.print(f"  - {g}")
        if analysis.strengths:
            console.print("\n[green]강점:[/green]")
            for s in analysis.strengths[:5]:
                console.print(f"  - {s}")
    else:
        out_path = Path(config.output.directory) / "jd_match.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(analysis.to_markdown(), encoding="utf-8")
        console.print(f"[green]리포트 저장:[/green] {out_path}")


@app.command()
def interview(
    company: str = typer.Argument(help="기업명"),
    position: str = typer.Option("", "--position", "-p", help="지원 포지션"),
    profile: str = typer.Option("", "--profile", help="커리어 프로필 YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식: markdown, terminal"),
) -> None:
    """면접 준비 가이드를 생성해요."""
    from hirekit.engine.interview_prep import InterviewPrep

    config = load_config()
    llm = _get_llm(config)
    prep = InterviewPrep(llm=llm)

    user_profile = _load_profile(profile)

    with console.status(f"[bold green]{company} 면접 가이드 생성 중..."):
        guide = prep.prepare(
            company=company,
            position=position,
            profile=user_profile,
        )

    if output == "terminal":
        console.print(Panel(
            f"[bold]{company}[/bold] — {position or '공통'}\n"
            f"질문 수: 공통 {len(guide.common_questions)}개, "
            f"기술 {len(guide.technical_questions)}개, "
            f"행동 {len(guide.behavioral_questions)}개\n"
            f"역질문: {len(guide.reverse_questions)}개",
            title="[bold blue]면접 준비[/bold blue]",
            border_style="blue",
        ))
        for q in guide.common_questions:
            console.print(f"\n[cyan]Q:[/cyan] {q['question']}")
            console.print(f"  [dim]{q.get('answer', '')}[/dim]")
    else:
        out_path = Path(config.output.directory) / f"{company}_interview.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(guide.to_markdown(), encoding="utf-8")
        console.print(f"[green]리포트 저장:[/green] {out_path}")


@app.command()
def coverletter(
    company: str = typer.Argument(help="기업명 (예: '카카오', 'toss')"),
    position: str = typer.Option("", "--position", "-p", help="지원 포지션 (예: PM)"),
    profile: str = typer.Option("", "--profile", help="커리어 프로필 YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식: markdown, terminal"),
    no_llm: bool = typer.Option(False, "--no-llm", help="LLM 생략, 규칙 기반만 사용"),
) -> None:
    """한국어 자기소개서 초안을 작성하고 코칭 피드백을 제공해요."""
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
            f"(등급 {draft.grade})\n"
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
    company: str = typer.Argument(help="기업명"),
    jd: str = typer.Option("", "--jd", help="채용공고 URL 또는 텍스트 파일"),
    resume_file: str = typer.Option("", "--resume", help="이력서 파일 (md/txt/pdf)"),
    position: str = typer.Option("", "--position", "-p", help="지원 포지션"),
    profile: str = typer.Option("", "--profile", help="커리어 프로필 YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식"),
    no_llm: bool = typer.Option(False, "--no-llm", help="LLM 생략"),
) -> None:
    """전체 파이프라인 실행: 기업 분석 → JD 매칭 → 이력서 리뷰 → 면접 준비 → 자기소개서."""
    from hirekit.engine.company_analyzer import CompanyAnalyzer
    from hirekit.engine.cover_letter import CoverLetterCoach
    from hirekit.engine.interview_prep import InterviewPrep
    from hirekit.engine.jd_matcher import JDMatcher
    from hirekit.engine.resume_advisor import ResumeAdvisor

    config = load_config()
    llm = _get_llm(config) if not no_llm else None
    user_profile = _load_profile(profile)

    console.print(Panel(
        f"[bold]기업:[/bold] {company}\n"
        f"[bold]포지션:[/bold] {position or '미지정'}  "
        f"[bold]LLM:[/bold] {'off' if no_llm else config.llm.provider}",
        title="[bold blue]HireKit 파이프라인[/bold blue]",
        border_style="blue",
    ))

    # Step 1: Company analysis
    console.print("\n[bold cyan][1/5] 기업 분석 중...[/bold cyan]")
    analyzer = CompanyAnalyzer(config=config, use_llm=not no_llm)
    with console.status("[bold green]기업 데이터 수집 중..."):
        report = analyzer.analyze(company=company)
    console.print("[green]✓[/green] 기업 분석 완료")

    # Step 2: JD analysis (optional)
    jd_analysis = None
    jd_text = ""
    if jd:
        console.print("[bold cyan][2/5] JD 분석 중...[/bold cyan]")
        jd_path = Path(jd)
        jd_source = jd_path.read_text(encoding="utf-8") if jd_path.exists() else jd
        jd_text = jd_source
        matcher = JDMatcher(llm=llm)
        with console.status("[bold green]채용공고 분석 중..."):
            jd_analysis = matcher.analyze(jd_source=jd_source, profile=user_profile)
        console.print("[green]✓[/green] JD 분석 완료")
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
        with console.status("[bold green]이력서 리뷰 중..."):
            resume_feedback = advisor.review(
                resume_path=resume_file, jd_text=jd_text, profile=user_profile
            )
        console.print("[green]✓[/green] 이력서 리뷰 완료")
    else:
        console.print("[dim][3/5] 이력서 리뷰 건너뜀 (--resume 미지정)[/dim]")

    # Step 4: Interview prep
    console.print("[bold cyan][4/5] 면접 준비 가이드 생성 중...[/bold cyan]")
    prep = InterviewPrep(llm=llm)
    with console.status("[bold green]면접 가이드 생성 중..."):
        guide = prep.prepare(
            company=company,
            position=position,
            report=report,
            profile=user_profile,
        )
    console.print("[green]✓[/green] 면접 가이드 완료")

    # Step 5: Cover letter
    console.print("[bold cyan][5/5] 자기소개서 초안 작성 중...[/bold cyan]")
    coach = CoverLetterCoach(llm=llm)
    with console.status("[bold green]자기소개서 작성 중..."):
        cover_draft = coach.draft(
            company=company,
            position=position,
            profile=user_profile,
            company_report=report.to_dict(),
        )
    console.print("[green]✓[/green] 자기소개서 초안 완료")

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
            f"(등급 {report.scorecard.grade})\n"
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
            + f"[{verdict_style}]최종 판정: {verdict}[/{verdict_style}]",
            title="[bold blue]파이프라인 결과[/bold blue]",
            border_style="blue",
        ))
    else:
        # Build integrated markdown report
        lines = [
            f"# HireKit 파이프라인 리포트: {company}",
            f"**포지션:** {position or '미지정'}",
            f"**최종 판정:** {verdict} (종합 점수: {combined:.0f}/100)",
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
        console.print(f"\n[green]파이프라인 리포트 저장:[/green] {out_path}")

        # Summary table
        table = Table(title=f"{company} 파이프라인 요약")
        table.add_column("단계", style="cyan")
        table.add_column("결과", justify="right")
        table.add_column("비고")

        table.add_row(
            "기업 분석",
            f"{report.scorecard.total_score:.0f}/100" if report.scorecard else "-",
            f"등급 {report.scorecard.grade}" if report.scorecard else "",
        )
        if jd_analysis:
            table.add_row(
                "JD 매칭",
                f"{jd_analysis.match_score:.0f}/100",
                f"등급 {jd_analysis.match_grade}",
            )
        if resume_feedback:
            table.add_row(
                "이력서",
                f"{resume_feedback.overall_score:.0f}/100",
                f"등급 {resume_feedback.grade}",
            )
        table.add_row("면접 질문", f"{len(guide.common_questions)}개", "")
        table.add_row(
            "자기소개서",
            f"{cover_draft.overall_score:.0f}/100",
            f"등급 {cover_draft.grade}",
        )
        table.add_row(
            "[bold]최종 판정[/bold]",
            f"[{verdict_style}]{verdict}[/{verdict_style}]",
            f"종합 {combined:.0f}/100",
        )
        console.print(table)


@app.command()
def resume(
    file: str = typer.Argument(help="이력서 파일 경로 (md, txt, pdf)"),
    jd: str = typer.Option("", "--jd", help="타겟 JD URL 또는 텍스트"),
    profile: str = typer.Option("", "--profile", "-p", help="커리어 프로필 YAML"),
    output: str = typer.Option("markdown", "--output", "-o", help="출력 형식: markdown, terminal"),
) -> None:
    """이력서를 검토하고 개선 피드백을 제공해요."""
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
                console.print(f"[yellow]JD URL에서 내용을 가져오지 못했어요: {jd}[/yellow]")
        else:
            jd_text = jd

    with console.status("[bold green]이력서 검토 중..."):
        feedback = advisor.review(
            resume_path=file, jd_text=jd_text, profile=user_profile
        )

    if output == "terminal":
        console.print(Panel(
            f"[bold]점수:[/bold] {feedback.overall_score:.0f}/100 "
            f"(등급 {feedback.grade})",
            title="[bold blue]이력서 리뷰[/bold blue]",
            border_style="blue",
        ))
        if feedback.strengths:
            console.print("\n[green]강점:[/green]")
            for s in feedback.strengths:
                console.print(f"  + {s}")
        if feedback.improvements:
            console.print("\n[yellow]개선 사항:[/yellow]")
            for i in feedback.improvements:
                console.print(f"  - {i}")
        if feedback.keyword_gaps:
            console.print("\n[red]JD 대비 부족한 키워드:[/red]")
            console.print(f"  {', '.join(feedback.keyword_gaps[:10])}")
    else:
        out_path = Path(config.output.directory) / "resume_review.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(feedback.to_markdown(), encoding="utf-8")
        console.print(f"[green]리포트 저장:[/green] {out_path}")


@app.command()
def strategy(
    target: str = typer.Argument(help="목표 기업명"),
    current: str = typer.Option(None, "--current", "-c", help="현재 재직 회사"),
    role: str = typer.Option(None, "--role", "-r", help="목표 직군 (예: 백엔드, PM)"),
    experience: int = typer.Option(0, "--experience", "-e", help="경력 연차"),
    skills: str = typer.Option("", "--skills", "-s", help="보유 기술 (쉼표 구분, 예: python,aws,react)"),
    output: str = typer.Option("terminal", "--output", "-o", help="출력 형식: terminal, markdown"),
) -> None:
    """커리어 전략 분석 — 목표 기업에 맞는 이직/취업 전략을 제안해요."""
    from hirekit.engine.career_strategy import CareerProfile, CareerStrategyEngine
    from hirekit.core.config import load_config

    config = load_config()

    skills_list = [s.strip() for s in skills.split(",") if s.strip()] if skills else []

    profile = CareerProfile(
        target_company=target,
        current_company=current,
        years_of_experience=experience,
        current_role="",
        target_role=role or "",
        skills=skills_list,
    )

    console.print(Panel(
        f"[bold]목표 기업:[/bold] {target}\n"
        f"[bold]현재 회사:[/bold] {current or '미지정'}  "
        f"[bold]목표 직군:[/bold] {role or '미지정'}  "
        f"[bold]경력:[/bold] {experience}년",
        title="[bold blue]HireKit 커리어 전략[/bold blue]",
        border_style="blue",
    ))

    engine = CareerStrategyEngine()
    with console.status("[bold green]전략 분석 중..."):
        result = engine.analyze(profile)

    if output == "markdown":
        from hirekit.core.config import load_config as _lc
        out_path = Path(config.output.directory) / f"{target}_strategy.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# 커리어 전략: {target}",
            f"**적합도:** {result.fit_score:.0f}/100",
            "",
            f"## 접근 전략\n{result.approach_strategy}",
            "",
            "## 이력서 강조 포인트",
            *[f"- {f}" for f in result.resume_focus],
            "",
            "## 면접 준비",
            *[f"- {p}" for p in result.interview_prep],
            "",
            f"## 준비 기간\n{result.timeline}",
            "",
            f"## 커리어 경로\n{result.career_path}",
            "",
            f"## 리스크 평가\n{result.risk_assessment}",
        ]
        if result.gap_analysis:
            lines += [
                "",
                "## 스킬 갭 분석",
                "| 기술 | 카테고리 | 중요도 | 학습 제안 |",
                "|------|----------|--------|-----------|",
                *[
                    f"| {g.skill} | {g.category} | {g.importance} | {g.learning_suggestion} |"
                    for g in result.gap_analysis
                ],
            ]
        if result.alternative_companies:
            lines += [
                "",
                f"## 대안 기업\n{', '.join(result.alternative_companies)}",
            ]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"[green]전략 리포트 저장:[/green] {out_path}")
    else:
        # Terminal output
        console.print(f"\n[bold cyan]적합도 점수:[/bold cyan] {result.fit_score:.0f}/100")
        console.print(f"\n[bold]접근 전략:[/bold]\n{result.approach_strategy}")

        if result.gap_analysis:
            console.print("\n[bold red]스킬 갭:[/bold red]")
            for g in result.gap_analysis:
                importance_style = "red" if g.importance == "required" else "yellow"
                console.print(
                    f"  [{importance_style}]•[/{importance_style}] "
                    f"[bold]{g.skill}[/bold] ({g.category}) — {g.learning_suggestion}"
                )

        console.print("\n[bold green]이력서 강조 포인트:[/bold green]")
        for f in result.resume_focus:
            console.print(f"  • {f}")

        console.print("\n[bold blue]면접 준비:[/bold blue]")
        for p in result.interview_prep:
            console.print(f"  • {p}")

        console.print(f"\n[bold]준비 기간:[/bold] {result.timeline}")
        console.print(f"\n[bold]커리어 경로:[/bold] {result.career_path}")
        console.print(f"\n[bold]리스크 평가:[/bold]\n{result.risk_assessment}")

        if result.alternative_companies:
            console.print(
                f"\n[bold]대안 기업:[/bold] {', '.join(result.alternative_companies)}"
            )


@app.command()
def compare(
    companies: list[str] = typer.Argument(help="비교할 기업 2-3개 (예: 토스 카카오 네이버)"),
    output: str = typer.Option("terminal", "--output", "-o", help="출력 형식: terminal, markdown"),
) -> None:
    """기업 비교 — 여러 기업을 나란히 비교해요."""
    from hirekit.engine.company_comparator import CompanyComparator
    from hirekit.core.config import load_config

    if len(companies) < 2:
        console.print("[red]최소 2개 기업을 입력해주세요.[/red]")
        raise typer.Exit(1)

    config = load_config()
    comparator = CompanyComparator()

    console.print(Panel(
        f"[bold]비교 기업:[/bold] {' vs '.join(companies)}",
        title="[bold blue]HireKit 기업 비교[/bold blue]",
        border_style="blue",
    ))

    with console.status("[bold green]기업 비교 중..."):
        result = comparator.compare_many(companies)

    if output == "markdown":
        out_path = Path(config.output.directory) / f"{'_vs_'.join(companies)}_compare.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result.to_markdown(), encoding="utf-8")
        console.print(f"[green]비교 리포트 저장:[/green] {out_path}")
    else:
        from hirekit.engine.company_comparator import _DIMENSION_LABELS
        from hirekit.core.scoring import score_to_grade

        table = Table(title=f"기업 비교: {' vs '.join(result.companies)}")
        table.add_column("차원", style="cyan")
        for name in result.companies:
            table.add_column(name, justify="right")
        table.add_column("승자", style="green")

        for dim_key, label in _DIMENSION_LABELS.items():
            scores = result.dimensions.get(dim_key, [])
            score_cells = [f"{s:.1f}/5" for s in scores]
            winner = result.winner_by_dimension.get(dim_key, "-")
            table.add_row(label, *score_cells, winner)

        # Overall row
        overall_cells = [
            f"[bold]{result.overall_scores.get(n, 0):.0f}/100[/bold] "
            f"(등급 {score_to_grade(result.overall_scores.get(n, 0))})"
            for n in result.companies
        ]
        table.add_row("[bold]종합[/bold]", *overall_cells, f"[bold]{result.winner}[/bold]")
        console.print(table)

        console.print(f"\n[bold]추천:[/bold]\n{result.overall_recommendation}")


# --- Helpers ---

def _get_llm(config: HireKitConfig) -> BaseLLM:  # noqa: F821
    """Initialize LLM from config.

    Supported providers: openai, anthropic, none.
    Falls back to NoLLM with a user-visible notice on misconfiguration.
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
    except ImportError:
        console.print(
            f"[yellow]LLM 패키지({provider})를 불러오지 못했어요. "
            "데이터 기반 분석만 제공해요. "
            f"패키지 설치: [bold]pip install hirekit[{provider}][/bold][/yellow]"
        )
    except Exception:
        console.print(
            f"[yellow]LLM({provider}) 초기화에 실패했어요. 데이터 기반 분석으로 전환해요. "
            "API 키를 확인하거나 [bold]hirekit configure[/bold]로 재설정하세요.[/yellow]"
        )
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
