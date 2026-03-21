"""Jinja2-based Markdown renderer for HireKit analysis reports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from hirekit.engine.company_analyzer import AnalysisReport

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class MarkdownRenderer:
    """Renders an AnalysisReport to Markdown using Jinja2 templates."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(disabled_extensions=("md.j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render(
        self,
        report: AnalysisReport,
        template: str = "report_ko",
        *,
        privacy_track: bool = False,
        profile: dict | None = None,
    ) -> str:
        """Render *report* to Markdown.

        Parameters
        ----------
        report:
            The ``AnalysisReport`` produced by ``CompanyAnalyzer``.
        template:
            Template name without extension — ``"report_ko"`` (default) or
            ``"report_en"``.
        privacy_track:
            When ``True`` section 6 (Data Privacy & Compliance) is included.
        profile:
            Optional user-profile dict; when provided section 9 (Career
            Mapping) is included.
        """
        template_file = f"{template}.md.j2"
        tmpl = self._env.get_template(template_file)

        data = report.to_dict()
        scorecard = data.get("scorecard", {})
        sources = data.get("sources", [])
        sections = data.get("sections", {})

        # Jinja2 dict keys must be ints — to_dict() preserves them as ints
        # but JSON round-trips turn them to strings; normalise both.
        sections = {
            int(k): v for k, v in sections.items()
        }

        context = {
            "company": data.get("company", ""),
            "region": data.get("region", ""),
            "tier": data.get("tier", 1),
            "grade": scorecard.get("grade", "N/A"),
            "sections": sections,
            "scorecard": scorecard,
            "sources": sources,
            "privacy_track": privacy_track,
            "profile": profile,
        }

        return tmpl.render(**context)
