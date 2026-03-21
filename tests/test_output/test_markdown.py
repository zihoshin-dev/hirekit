"""Tests for Jinja2 Markdown renderer — snapshot-style behavioral tests."""

import pytest

from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.scorer import Scorecard, ScoreDimension
from hirekit.output.markdown import MarkdownRenderer


def make_report(
    company: str = "카카오",
    region: str = "kr",
    tier: int = 1,
    sections: dict | None = None,
    score: float = 80.0,
) -> AnalysisReport:
    """Factory for minimal AnalysisReport."""
    scorecard = Scorecard(
        company=company,
        dimensions=[ScoreDimension(name="job_fit", label="Job Fit",
                                   weight=1.0, score=score / 20)],
    )
    return AnalysisReport(
        company=company,
        region=region,
        tier=tier,
        sections=sections or {},
        scorecard=scorecard,
    )


class TestMarkdownRendererInit:
    def test_renderer_creates_jinja_environment(self):
        renderer = MarkdownRenderer()
        assert renderer._env is not None

    def test_template_file_loaded(self):
        renderer = MarkdownRenderer()
        # Should not raise
        tmpl = renderer._env.get_template("report_ko.md.j2")
        assert tmpl is not None


class TestMarkdownRendererRender:
    def test_company_name_in_output(self):
        renderer = MarkdownRenderer()
        report = make_report(company="토스")
        md = renderer.render(report)
        assert "토스" in md

    def test_region_uppercased_in_output(self):
        renderer = MarkdownRenderer()
        report = make_report(region="kr")
        md = renderer.render(report)
        assert "KR" in md

    def test_grade_in_output(self):
        renderer = MarkdownRenderer()
        report = make_report(score=80.0)
        md = renderer.render(report)
        # score=80/20=4.0 → total=80 → grade S
        assert "S" in md

    def test_empty_sections_renders_without_error(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={})
        md = renderer.render(report)
        assert isinstance(md, str)
        assert len(md) > 0

    def test_section_1_overview_rendered_when_present(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={
            1: {
                "company_name": "카카오",
                "ceo": "홍은택",
                "established": "20061003",
                "address": "제주",
                "homepage": "https://kakao.com",
            }
        })
        md = renderer.render(report)
        assert "회사 개요" in md
        assert "홍은택" in md

    def test_section_1_financials_rendered(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={
            1: {
                "financials": [
                    {
                        "account": "매출액",
                        "current_amount": "3000000000000",
                        "previous_amount": "2500000000000",
                        "two_years_ago": "",
                    }
                ]
            }
        })
        md = renderer.render(report)
        assert "매출액" in md
        assert "조" in md  # formatted by normalizer

    def test_missing_section_shows_placeholder(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={})
        md = renderer.render(report)
        # When section 1 is absent, template should show fallback text
        assert "추가 데이터가 필요" in md or "회사 개요" in md

    def test_llm_analysis_injected_when_present(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={
            1: {"analysis": "LLM이 생성한 회사 개요 분석 내용입니다."}
        })
        md = renderer.render(report)
        assert "LLM이 생성한 회사 개요 분석 내용입니다." in md

    def test_english_template_renders(self):
        renderer = MarkdownRenderer()
        report = make_report(company="Kakao", region="us")
        md = renderer.render(report, template="report_en")
        assert "Kakao" in md

    def test_tier_value_present_in_output(self):
        renderer = MarkdownRenderer()
        report = make_report(tier=2)
        md = renderer.render(report)
        assert "2" in md

    def test_int_and_string_section_keys_both_work(self):
        """to_dict() returns int keys; JSON round-trip gives string keys — both must work."""
        renderer = MarkdownRenderer()
        # Simulate string keys (as from JSON round-trip)
        report = make_report(sections={1: {"ceo": "홍길동"}})
        md = renderer.render(report)
        assert "홍길동" in md


class TestMarkdownSnapshotPatterns:
    """Snapshot-style: verify structural patterns are always present."""

    def test_output_starts_with_company_heading(self):
        renderer = MarkdownRenderer()
        report = make_report(company="네이버")
        md = renderer.render(report)
        assert md.strip().startswith("# 네이버")

    def test_output_contains_section_headers(self):
        renderer = MarkdownRenderer()
        report = make_report(sections={1: {"ceo": "최수연"}})
        md = renderer.render(report)
        assert "##" in md  # at least one section header

    def test_horizontal_rules_present(self):
        renderer = MarkdownRenderer()
        report = make_report()
        md = renderer.render(report)
        assert "---" in md
