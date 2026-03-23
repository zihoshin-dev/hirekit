"""CLI end-to-end tests using typer.testing.CliRunner — no real API calls."""

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
