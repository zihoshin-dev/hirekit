from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hirekit.core.trust_contract import VERDICT_GUIDANCE, VerdictLabel
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.jd_matcher import JDAnalysis
from hirekit.engine.resume_advisor import ResumeFeedback


@dataclass
class HeroVerdict:
    label: VerdictLabel
    combined_score: float
    confidence: str
    advisory_note: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "combined_score": self.combined_score,
            "confidence": self.confidence,
            "advisory_note": self.advisory_note,
            "reasons": self.reasons,
        }


def compose_hero_verdict(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None = None,
    resume_feedback: ResumeFeedback | None = None,
) -> HeroVerdict:
    weighted_total = 0.0
    total_weight = 0.0
    reasons: list[str] = []

    if report.scorecard is not None:
        weighted_total += report.scorecard.total_score * 0.5
        total_weight += 0.5
        reasons.append(f"기업 분석 {report.scorecard.total_score:.0f}/100")

    if jd_analysis is not None:
        weighted_total += jd_analysis.match_score * 0.3
        total_weight += 0.3
        reasons.append(f"JD 매칭 {jd_analysis.match_score:.0f}/100")

    if resume_feedback is not None:
        weighted_total += resume_feedback.overall_score * 0.2
        total_weight += 0.2
        reasons.append(f"이력서 {resume_feedback.overall_score:.0f}/100")

    combined = weighted_total / total_weight if total_weight else 0.0

    if combined >= 65:
        label: VerdictLabel = "Go"
    elif combined >= 40:
        label = "Hold"
    else:
        label = "Pass"

    if total_weight >= 0.8:
        confidence = "high"
    elif total_weight >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return HeroVerdict(
        label=label,
        combined_score=combined,
        confidence=confidence,
        advisory_note=VERDICT_GUIDANCE[label],
        reasons=reasons,
    )
