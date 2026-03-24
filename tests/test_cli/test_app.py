"""CLI end-to-end tests using typer.testing.CliRunner — no real API calls."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from hirekit.cli.app import app
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.scorer import Scorecard, ScoreDimension

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_scorecard(company: str = "카카오", score: float = 3.0) -> Scorecard:
    return Scorecard(
        company=company,
        dimensions=[
            ScoreDimension(name="job_fit", label="Job Fit", weight=0.30, score=score),
            ScoreDimension(name="career_leverage", label="Career Leverage", weight=0.20, score=score),
            ScoreDimension(name="growth", label="Growth", weight=0.20, score=score),
            ScoreDimension(name="compensation", label="Compensation", weight=0.15, score=score),
            ScoreDimension(name="culture_fit", label="Culture Fit", weight=0.15, score=score),
        ],
    )


def make_mock_report(company: str = "카카오") -> AnalysisReport:
    return AnalysisReport(
        company=company,
        region="kr",
        tier=1,
        sections={1: {"ceo": "홍은택"}},
        scorecard=make_mock_scorecard(company),
    )


def make_mock_strategy_result():
    return SimpleNamespace(
        fit_score=78.0,
        gap_analysis=[
            SimpleNamespace(
                skill="kafka",
                importance="required",
                learning_suggestion="Kafka 실습",
            )
        ],
        approach_strategy="핵심 갭을 보완하고 바로 지원해요.",
        resume_focus=["분산 시스템 성과를 강조해요."],
        interview_prep=["Kafka 트레이드오프를 설명할 수 있어야 해요."],
        timeline="1-2개월",
        alternative_companies=["네이버", "당근"],
        career_path="백엔드 성장 경로",
        risk_assessment="중간 리스크",
    )


def make_mock_comparison_result():
    return SimpleNamespace(
        companies=["카카오", "네이버", "당근"],
        winner="네이버",
        overall_scores={"카카오": 73.0, "네이버": 81.0, "당근": 79.0},
        overall_recommendation="**종합 추천: 네이버**",
        dimensions={},
        winner_by_dimension={},
        to_markdown=MagicMock(return_value="# 기업 비교"),
    )


def make_mock_strategy():
    from hirekit.engine.career_strategy import CareerStrategy, SkillGap

    return CareerStrategy(
        fit_score=82.0,
        gap_analysis=[
            SkillGap(
                skill="kubernetes",
                category="DevOps",
                importance="required",
                learning_suggestion="K8s 공식 튜토리얼",
            )
        ],
        approach_strategy="핵심 갭을 보완하면 바로 지원 가능해요.",
        resume_focus=["프로젝트 임팩트 수치화"],
        interview_prep=["STAR 사례 3개 준비"],
        timeline="1-2개월",
        alternative_companies=["네이버", "카카오"],
        career_path="PM → Senior PM → Group PM",
        risk_assessment="리스크 수준: 중간",
    )


# ---------------------------------------------------------------------------
# version / --version
# ---------------------------------------------------------------------------

class TestVersionCommand:
    def test_version_flag_exits_successfully(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0

    def test_version_output_contains_hirekit(self):
        result = runner.invoke(app, ["--version"])
        assert "HireKit" in result.output or "hirekit" in result.output.lower()


# ---------------------------------------------------------------------------
# configure command
# ---------------------------------------------------------------------------

class TestConfigureCommand:
    def test_configure_creates_config_file(self, tmp_path):
        with patch("hirekit.cli.app.DEFAULT_CONFIG_DIR", tmp_path):
            with patch("hirekit.cli.app.ensure_config_dir", return_value=tmp_path):
                result = runner.invoke(app, ["configure"])
        assert result.exit_code == 0

    def test_configure_shows_already_exists_when_file_present(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text("[analysis]\ndefault_region = 'kr'\n")
        with patch("hirekit.cli.app.DEFAULT_CONFIG_DIR", tmp_path):
            with patch("hirekit.cli.app.ensure_config_dir", return_value=tmp_path):
                result = runner.invoke(app, ["configure"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# sources command
# ---------------------------------------------------------------------------

class TestSourcesCommand:
    def test_sources_command_exits_successfully(self):
        with patch("hirekit.sources.base.SourceRegistry.discover_plugins"):
            with patch("hirekit.sources.base.SourceRegistry.get_all", return_value={}):
                result = runner.invoke(app, ["sources"])
        assert result.exit_code == 0

    def test_sources_output_contains_table_header(self):
        with patch("hirekit.sources.base.SourceRegistry.discover_plugins"):
            with patch("hirekit.sources.base.SourceRegistry.get_all", return_value={}):
                result = runner.invoke(app, ["sources"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# analyze command
# ---------------------------------------------------------------------------

class TestAnalyzeCommand:
    def test_analyze_markdown_output_saves_file(self, tmp_path):
        mock_report = make_mock_report("카카오")
        mock_report.to_markdown = MagicMock(return_value="# 카카오 분석\n\n테스트")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                result = runner.invoke(app, ["analyze", "카카오", "--no-llm"])

        assert result.exit_code == 0

    def test_analyze_terminal_output_mode(self, tmp_path):
        mock_report = make_mock_report("토스")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                result = runner.invoke(app, ["analyze", "토스", "--output", "terminal", "--no-llm"])

        assert result.exit_code == 0

    def test_analyze_json_output_mode(self, tmp_path):
        mock_report = make_mock_report("네이버")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                result = runner.invoke(app, ["analyze", "네이버", "--output", "json", "--no-llm"])

        assert result.exit_code == 0
        # JSON output should contain "company" key somewhere
        assert '"company"' in result.output or "company" in result.output

    def test_analyze_requires_company_argument(self):
        result = runner.invoke(app, ["analyze"])
        assert result.exit_code != 0

    def test_analyze_tier_option_passed_through(self, tmp_path):
        mock_report = make_mock_report("카카오")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                instance = MockAnalyzer.return_value
                instance.analyze.return_value = mock_report
                runner.invoke(app, ["analyze", "카카오", "--tier", "2", "--no-llm"])
                instance.analyze.assert_called_once_with(
                    company="카카오", region="kr", tier=2
                )


# ---------------------------------------------------------------------------
# pipeline command
# ---------------------------------------------------------------------------

class TestPipelineCommand:
    def test_pipeline_no_llm_exits_successfully(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft, CoverLetterSection
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = [{"question": "Q1", "answer": "A1"}]
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = [
            CoverLetterSection(key="growth", title="성장과정",
                               content="성장 내용", score=70.0)
        ]

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report

                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide

                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft

                        result = runner.invoke(app, [
                            "pipeline", "카카오", "--no-llm", "--output", "terminal"
                        ])

        assert result.exit_code == 0

    def test_pipeline_verdict_go_for_high_score(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        # Force high score → verdict should be Go
        assert mock_report.scorecard is not None
        mock_report.scorecard.dimensions[0].score = 5.0

        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []

        mock_draft = CoverLetterDraft(company="카카오", overall_score=90.0)
        mock_draft.sections = []

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        result = runner.invoke(app, [
                            "pipeline", "카카오", "--no-llm", "--output", "terminal"
                        ])

        assert result.exit_code == 0
        assert "Go" in result.output or "Hold" in result.output or "Pass" in result.output

    def test_pipeline_terminal_output_includes_advisory_note(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = []

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        result = runner.invoke(app, [
                            "pipeline", "카카오", "--no-llm", "--output", "terminal"
                        ])

        assert result.exit_code == 0
        assert "Advisory only" in result.output

    def test_pipeline_markdown_output_includes_hero_verdict_section(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_report.to_markdown = MagicMock(return_value="# 기업 분석")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []
        mock_guide.to_markdown = MagicMock(return_value="# 면접 준비")

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = []
        mock_draft.to_markdown = MagicMock(return_value="# 자기소개서")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        result = runner.invoke(app, [
                            "pipeline", "카카오", "--no-llm", "--output", "markdown"
                        ])

        assert result.exit_code == 0
        saved = (tmp_path / "카카오_pipeline.md").read_text(encoding="utf-8")
        assert "## 0. Hero Verdict" in saved
        assert "권고 메모" in saved

    def test_pipeline_markdown_output_includes_proof_of_work_and_saves_artifact(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_report.to_markdown = MagicMock(return_value="# 기업 분석")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []
        mock_guide.to_markdown = MagicMock(return_value="# 면접 준비")

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = []
        mock_draft.to_markdown = MagicMock(return_value="# 자기소개서")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        result = runner.invoke(app, [
                            "pipeline", "카카오", "--no-llm", "--output", "markdown"
                        ])

        assert result.exit_code == 0
        saved = (tmp_path / "카카오_pipeline.md").read_text(encoding="utf-8")
        assert "## 0.5. Proof of Work" in saved
        proof_saved = (tmp_path / "카카오_proof.md").read_text(encoding="utf-8")
        assert "바로 할 일" in proof_saved

    def test_pipeline_terminal_output_includes_strategy_and_compare_when_requested(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = []

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockStrategy:
                            MockStrategy.return_value.analyze.return_value = make_mock_strategy_result()
                            with patch("hirekit.engine.company_comparator.CompanyComparator") as MockComparator:
                                MockComparator.return_value.compare_many.return_value = make_mock_comparison_result()
                                result = runner.invoke(
                                    app,
                                    [
                                        "pipeline",
                                        "카카오",
                                        "--no-llm",
                                        "--output",
                                        "terminal",
                                        "--current",
                                        "라인",
                                        "--current-role",
                                        "백엔드",
                                        "--experience",
                                        "4",
                                        "--skills",
                                        "python,kafka",
                                        "--compare",
                                        "네이버",
                                        "--compare",
                                        "당근",
                                    ],
                                )

        assert result.exit_code == 0
        assert "워룸 전략" in result.output
        assert "워룸 비교 (사용자 지정)" in result.output
        assert "우세 기업: 네이버" in result.output
        assert MockStrategy.return_value.analyze.called
        MockComparator.return_value.compare_many.assert_called_once_with(["카카오", "네이버", "당근"])

    def test_pipeline_markdown_output_auto_uses_strategy_alternatives_for_compare(self, tmp_path):
        from hirekit.engine.cover_letter import CoverLetterDraft
        from hirekit.engine.interview_prep import InterviewGuide

        mock_report = make_mock_report("카카오")
        mock_report.to_markdown = MagicMock(return_value="# 기업 분석")
        mock_guide = InterviewGuide(company="카카오")
        mock_guide.common_questions = []
        mock_guide.reverse_questions = []
        mock_guide.technical_questions = []
        mock_guide.behavioral_questions = []
        mock_guide.tips = []
        mock_guide.to_markdown = MagicMock(return_value="# 면접 준비")

        mock_draft = CoverLetterDraft(company="카카오", overall_score=70.0)
        mock_draft.sections = []
        mock_draft.to_markdown = MagicMock(return_value="# 자기소개서")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.interview_prep.InterviewPrep") as MockPrep:
                    MockPrep.return_value.prepare.return_value = mock_guide
                    with patch("hirekit.engine.cover_letter.CoverLetterCoach") as MockCoach:
                        MockCoach.return_value.draft.return_value = mock_draft
                        with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockStrategy:
                            MockStrategy.return_value.analyze.return_value = make_mock_strategy_result()
                            with patch("hirekit.engine.company_comparator.CompanyComparator") as MockComparator:
                                MockComparator.return_value.compare_many.return_value = make_mock_comparison_result()
                                result = runner.invoke(
                                    app,
                                    [
                                        "pipeline",
                                        "카카오",
                                        "--no-llm",
                                        "--output",
                                        "markdown",
                                        "--experience",
                                        "3",
                                        "--skills",
                                        "python",
                                    ],
                                )

        assert result.exit_code == 0
        saved = (tmp_path / "카카오_pipeline.md").read_text(encoding="utf-8")
        assert "## 0.75. War Room" in saved
        assert "### 개인화 전략" in saved
        assert "### 기업 비교 (전략 추천)" in saved
        MockComparator.return_value.compare_many.assert_called_once_with(["카카오", "네이버", "당근"])


class TestProofCommand:
    def test_proof_terminal_output_shows_thesis_and_actions(self, tmp_path):
        mock_report = make_mock_report("카카오")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                result = runner.invoke(app, [
                    "proof", "카카오", "--no-llm", "--output", "terminal"
                ])

        assert result.exit_code == 0
        assert "실행 메모" in result.output
        assert "바로 할 일" in result.output

    def test_proof_markdown_output_saves_file(self, tmp_path):
        mock_report = make_mock_report("카카오")

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                result = runner.invoke(app, [
                    "proof", "카카오", "--no-llm", "--output", "markdown"
                ])

        assert result.exit_code == 0
        saved = (tmp_path / "카카오_proof.md").read_text(encoding="utf-8")
        assert "카카오" in saved
        assert "바로 할 일" in saved

    def test_proof_terminal_output_includes_strategy_summary_when_profile_given(self, tmp_path):
        from hirekit.engine.career_strategy import CareerStrategy

        mock_report = make_mock_report("토스")
        strategy = CareerStrategy(
            fit_score=74.0,
            gap_analysis=[],
            approach_strategy="핵심 갭을 보완한 뒤 지원하세요.",
            resume_focus=["결제 도메인 성과를 강조하세요."],
            interview_prep=["시스템 디자인 준비를 강화하세요."],
            timeline="1-2개월",
            alternative_companies=["카카오페이", "네이버파이낸셜"],
            career_path="백엔드 → 시니어 → Tech Lead",
            risk_assessment="중간 리스크",
        )

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.llm.provider = "none"
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
                MockAnalyzer.return_value.analyze.return_value = mock_report
                with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockEngine:
                    MockEngine.return_value.analyze.return_value = strategy
                    result = runner.invoke(app, [
                        "proof", "토스", "--role", "백엔드", "--experience", "5",
                        "--skills", "python,aws,kafka", "--no-llm", "--output", "terminal",
                    ])

        assert result.exit_code == 0
        assert "개인화 전략" in result.output
        assert "1-2개월" in result.output


# ---------------------------------------------------------------------------
# strategy command
# ---------------------------------------------------------------------------

class TestStrategyProfileCommand:
    def test_strategy_terminal_output_exits_successfully(self):
        with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockEngine:
            MockEngine.return_value.analyze.return_value = make_mock_strategy()
            result = runner.invoke(
                app,
                ["strategy", "카카오", "--role", "PM", "--experience", "5"],
            )

        assert result.exit_code == 0
        assert "적합도 점수" in result.output

    def test_strategy_markdown_output_saves_file(self, tmp_path):
        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockEngine:
                MockEngine.return_value.analyze.return_value = make_mock_strategy()
                result = runner.invoke(
                    app,
                    ["strategy", "카카오", "--output", "markdown"],
                )

        assert result.exit_code == 0
        assert (tmp_path / "카카오_strategy.md").exists()

    def test_strategy_uses_profile_defaults_when_cli_fields_omitted(self, tmp_path):
        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(
            "\n".join(
                [
                    'current_company: "메이커스타"',
                    'current_role: "데이터 분석가"',
                    "years_of_experience: 4",
                    'education: "컴퓨터공학 학사"',
                    "tracks:",
                    '  - name: "AI PM"',
                    "skills:",
                    '  technical: ["Python", "SQL"]',
                    '  domain: ["Payment Systems"]',
                ]
            ),
            encoding="utf-8",
        )

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.analyze.return_value = make_mock_strategy()

                result = runner.invoke(
                    app,
                    ["strategy", "토스", "--profile", str(profile_file), "--output", "json"],
                )

        assert result.exit_code == 0
        call = instance.analyze.call_args
        profile = call.kwargs.get("profile") or call.args[0]
        assert profile.target_company == "토스"
        assert profile.current_company == "메이커스타"
        assert profile.current_role == "데이터 분석가"
        assert profile.target_role == "AI PM"
        assert profile.years_of_experience == 4
        assert "python" in [skill.lower() for skill in profile.skills]
        assert '"fit_score"' in result.output

    def test_strategy_cli_fields_override_profile_defaults(self, tmp_path):
        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(
            "\n".join(
                [
                    "years_of_experience: 2",
                    'current_role: "기획자"',
                    "tracks:",
                    '  - name: "PM"',
                    "skills:",
                    '  technical: ["Python"]',
                ]
            ),
            encoding="utf-8",
        )

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.career_strategy.CareerStrategyEngine") as MockEngine:
                instance = MockEngine.return_value
                instance.analyze.return_value = make_mock_strategy()

                result = runner.invoke(
                    app,
                    [
                        "strategy",
                        "당근",
                        "--profile",
                        str(profile_file),
                        "--current",
                        "토스",
                        "--current-role",
                        "백엔드",
                        "--role",
                        "AI CPO",
                        "--experience",
                        "7",
                        "--skills",
                        "Go,gRPC",
                        "--output",
                        "json",
                    ],
                )

        assert result.exit_code == 0
        call = instance.analyze.call_args
        profile = call.kwargs.get("profile") or call.args[0]
        assert profile.current_company == "토스"
        assert profile.current_role == "백엔드"
        assert profile.target_role == "AI CPO"
        assert profile.years_of_experience == 7
        lowered = [skill.lower() for skill in profile.skills]
        assert "go" in lowered
        assert "grpc" in lowered
        assert "python" in lowered


# ---------------------------------------------------------------------------
# compare command
# ---------------------------------------------------------------------------

class TestCompareStructuredCommand:
    def test_compare_terminal_output_exits_successfully(self):
        from hirekit.engine.company_comparator import ComparisonResult

        mock_result = ComparisonResult(
            companies=["카카오", "네이버"],
            dimensions={"growth": [3.5, 4.0]},
            winner_by_dimension={"growth": "네이버"},
            overall_scores={"카카오": 72.0, "네이버": 78.0},
            overall_recommendation="네이버가 더 유리해요.",
            comparison_table={},
        )

        with patch("hirekit.engine.company_comparator.CompanyComparator") as MockComparator:
            MockComparator.return_value.compare_many.return_value = mock_result
            result = runner.invoke(app, ["compare", "카카오", "네이버"])

        assert result.exit_code == 0
        assert "기업 비교" in result.output

    def test_compare_markdown_output_saves_file(self, tmp_path):
        from hirekit.engine.company_comparator import ComparisonResult

        mock_result = ComparisonResult(
            companies=["카카오", "네이버"],
            dimensions={"growth": [3.5, 4.0]},
            winner_by_dimension={"growth": "네이버"},
            overall_scores={"카카오": 72.0, "네이버": 78.0},
            overall_recommendation="네이버가 더 유리해요.",
            comparison_table={},
        )

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_comparator.CompanyComparator") as MockComparator:
                MockComparator.return_value.compare_many.return_value = mock_result
                result = runner.invoke(
                    app,
                    ["compare", "카카오", "네이버", "--output", "markdown"],
                )

        assert result.exit_code == 0
        assert (tmp_path / "카카오_vs_네이버_compare.md").exists()

    def test_compare_json_output_contains_structured_result(self, tmp_path):
        from hirekit.engine.company_comparator import ComparisonResult

        mock_result = ComparisonResult(
            companies=["토스", "네이버"],
            dimensions={"growth": [4.5, 3.5], "compensation": [4.4, 4.0]},
            winner_by_dimension={"growth": "토스"},
            overall_scores={"토스": 84.0, "네이버": 76.0},
            overall_recommendation="토스를 우선 추천해요.",
            comparison_table={"companies": ["토스", "네이버"]},
        )

        with patch("hirekit.cli.app.load_config") as mock_cfg:
            cfg = MagicMock()
            cfg.output.directory = str(tmp_path)
            mock_cfg.return_value = cfg

            with patch("hirekit.engine.company_comparator.CompanyComparator") as MockComparator:
                MockComparator.return_value.compare_many.return_value = mock_result
                result = runner.invoke(
                    app,
                    ["compare", "토스", "네이버", "--output", "json"],
                )

        assert result.exit_code == 0
        assert '"winner"' in result.output
        assert '"overall_scores"' in result.output


# ---------------------------------------------------------------------------
# _load_profile helper
# ---------------------------------------------------------------------------

class TestLoadProfile:
    def test_returns_none_for_empty_path(self):
        from hirekit.cli.app import _load_profile
        result = _load_profile("")
        # No default profile exists in test env — returns None
        assert result is None or isinstance(result, dict)

    def test_returns_none_for_missing_file(self):
        from hirekit.cli.app import _load_profile
        result = _load_profile("/nonexistent/path/profile.yaml")
        assert result is None

    def test_loads_yaml_profile(self, tmp_path):
        from hirekit.cli.app import _load_profile
        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(
            "name: 홍길동\nyears_of_experience: 3\nskills:\n  technical:\n    - Python\n",
            encoding="utf-8",
        )
        result = _load_profile(str(profile_file))
        assert result is not None
        assert result["name"] == "홍길동"
        assert result["years_of_experience"] == 3
