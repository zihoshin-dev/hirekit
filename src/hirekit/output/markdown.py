"""Jinja2-based Markdown renderer for HireKit analysis reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReportLike(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


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
        report: ReportLike,
        template: str = "report_ko",
        *,
        privacy_track: bool = False,
        profile: dict[str, Any] | None = None,
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

        # Normalize raw source data into template-ready format
        from hirekit.engine.data_normalizer import normalize_sections
        sections = normalize_sections(sections)

        hero_verdict = self._build_hero_verdict(scorecard)
        confidence_breakdown = self._build_confidence_breakdown(scorecard)
        evidence_summary = self._build_evidence_summary(sources)
        next_actions = self._build_next_actions(hero_verdict["label"])
        low_confidence_warning = self._build_low_confidence_warning(
            confidence_breakdown,
            evidence_summary,
        )

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
            "hero_verdict": hero_verdict,
            "confidence_breakdown": confidence_breakdown,
            "evidence_summary": evidence_summary,
            "next_actions": next_actions,
            "low_confidence_warning": low_confidence_warning,
        }

        return tmpl.render(**context)

    @staticmethod
    def _build_hero_verdict(scorecard: dict[str, Any]) -> dict[str, Any]:
        total = float(scorecard.get("total", 0.0) or 0.0)
        if total >= 65:
            label = "Go"
        elif total >= 40:
            label = "Hold"
        else:
            label = "Pass"
        return {
            "label": label,
            "total": total,
            "grade": scorecard.get("grade", "N/A"),
        }

    @staticmethod
    def _build_confidence_breakdown(scorecard: dict[str, Any]) -> list[dict[str, Any]]:
        breakdown: list[dict[str, Any]] = []
        for dimension in scorecard.get("dimensions", []):
            breakdown.append(
                {
                    "label": dimension.get("label") or dimension.get("name", ""),
                    "score": dimension.get("score", 0.0),
                    "confidence": dimension.get("confidence", "unknown") or "unknown",
                    "evidence": dimension.get("evidence", ""),
                    "source": dimension.get("source", ""),
                }
            )
        return breakdown

    @staticmethod
    def _build_evidence_summary(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        summary: list[dict[str, Any]] = []
        for source in sources[:5]:
            summary.append(
                {
                    "name": source.get("name", ""),
                    "section": source.get("section", ""),
                    "trust_label": source.get("trust_label", "unknown"),
                    "is_stale": source.get("is_stale", False),
                    "url": source.get("url", ""),
                }
            )
        return summary

    @staticmethod
    def _build_next_actions(label: str) -> list[str]:
        if label == "Go":
            return [
                "지원 스토리에 활용할 근거 숫자 3개를 정리해요.",
                "핵심 강점과 리스크를 면접 답변 구조에 연결해요.",
                "JD와 이력서 간 맞물리는 경험을 한 문장으로 압축해요.",
            ]
        if label == "Hold":
            return [
                "부족한 근거와 충돌 지점을 먼저 확인해요.",
                "최신 채용공고·기술 스택·보상 정보를 추가 수집해요.",
                "지원 전 리스크를 해소할 질문 목록을 만들어요.",
            ]
        return [
            "현재 근거로는 우선순위를 낮추고 다른 타깃을 비교해요.",
            "지원 필요성이 크다면 추가 데이터 확보 후 재평가해요.",
            "리스크를 감수할 이유가 있는지 먼저 점검해요.",
        ]

    @staticmethod
    def _build_low_confidence_warning(
        confidence_breakdown: list[dict[str, Any]],
        evidence_summary: list[dict[str, Any]],
    ) -> str:
        if any(item.get("confidence") == "low" for item in confidence_breakdown):
            return "일부 핵심 차원의 신뢰도가 낮아요. 지원 판단 전에 추가 근거 확인이 필요해요."
        if any(bool(item.get("is_stale")) for item in evidence_summary):
            return "일부 근거가 오래되었어요. 최신 데이터로 다시 확인하는 편이 안전해요."
        return ""
