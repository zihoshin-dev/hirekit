from __future__ import annotations

from dataclasses import dataclass, field

from hirekit.core.trust_contract import VERDICT_GUIDANCE, VerdictLabel
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.confidence_rules import conflicting_keys, derive_confidence
from hirekit.engine.jd_matcher import JDAnalysis
from hirekit.engine.resume_advisor import ResumeFeedback


@dataclass
class HeroVerdict:
    label: VerdictLabel
    combined_score: float
    confidence: str
    advisory_note: str
    reasons: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "combined_score": self.combined_score,
            "confidence": self.confidence,
            "advisory_note": self.advisory_note,
            "reasons": self.reasons,
            "cautions": self.cautions,
            "next_actions": self.next_actions,
        }


def compose_hero_verdict(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None = None,
    resume_feedback: ResumeFeedback | None = None,
) -> HeroVerdict:
    combined = _combined_score(report, jd_analysis, resume_feedback)
    evidence_quality = _evidence_quality(report)
    role_fit_score = _role_fit_score(report, jd_analysis, resume_feedback)
    actionability_score = _actionability_score(
        report,
        jd_analysis,
        resume_feedback,
        evidence_quality,
    )
    label = _label_from_rubric(
        evidence_quality=evidence_quality,
        role_fit_score=role_fit_score,
        actionability_score=actionability_score,
    )
    confidence = _confidence_from_rubric(
        evidence_quality=evidence_quality,
        coverage_count=_coverage_count(report, jd_analysis, resume_feedback),
    )

    return HeroVerdict(
        label=label,
        combined_score=combined,
        confidence=confidence,
        advisory_note=VERDICT_GUIDANCE[label],
        reasons=_build_reasons(
            report=report,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
            evidence_quality=evidence_quality,
            role_fit_score=role_fit_score,
            actionability_score=actionability_score,
        ),
        cautions=_build_cautions(
            report=report,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
            evidence_quality=evidence_quality,
            confidence=confidence,
            label=label,
        ),
        next_actions=_build_next_actions(
            label=label,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
            evidence_quality=evidence_quality,
        ),
    )


def _combined_score(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
) -> float:
    weighted_total = 0.0
    total_weight = 0.0

    if report.scorecard is not None:
        weighted_total += report.scorecard.total_score * 0.5
        total_weight += 0.5
    if jd_analysis is not None:
        weighted_total += jd_analysis.match_score * 0.3
        total_weight += 0.3
    if resume_feedback is not None:
        weighted_total += resume_feedback.overall_score * 0.2
        total_weight += 0.2

    return round(weighted_total / total_weight if total_weight else 0.0, 1)


def _coverage_count(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
) -> int:
    count = 1 if report.scorecard is not None else 0
    if jd_analysis is not None:
        count += 1
    if resume_feedback is not None:
        count += 1
    return count


def _evidence_quality(report: AnalysisReport) -> str:
    signals: list[str] = []
    dimension_confidence = _dimension_confidence(report)
    if dimension_confidence is not None:
        signals.append(dimension_confidence)
    source_confidence = _source_confidence(report)
    if source_confidence is not None:
        signals.append(source_confidence)
    if not signals:
        return "low"
    return min(signals, key=_confidence_rank)


def _dimension_confidence(report: AnalysisReport) -> str | None:
    if report.scorecard is None or not report.scorecard.dimensions:
        return None

    values = [
        dimension.confidence
        for dimension in report.scorecard.dimensions
        if dimension.confidence in {"high", "medium", "low"}
    ]
    if values:
        high = sum(1 for value in values if value == "high")
        low = sum(1 for value in values if value == "low")
        if low >= 2:
            return "low"
        if high >= 3 and low == 0:
            return "high"
        return "medium"

    evidence_count = sum(1 for dimension in report.scorecard.dimensions if dimension.evidence.strip())
    return "medium" if evidence_count >= 3 else "low"


def _source_confidence(report: AnalysisReport) -> str | None:
    if not report.source_results:
        return None
    expected_sources = [result.source_name for result in report.source_results]
    return derive_confidence(expected_sources, report.source_results)


def _role_fit_score(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
) -> float:
    values: list[float] = []
    job_fit = _dimension_score(report, "job_fit")
    if job_fit is not None:
        values.append(job_fit)
    if jd_analysis is not None:
        values.append(jd_analysis.match_score)
    if resume_feedback is not None:
        values.append(resume_feedback.overall_score)
    return round(sum(values) / len(values), 1) if values else 0.0


def _dimension_score(report: AnalysisReport, key: str) -> float | None:
    if report.scorecard is None:
        return None
    for dimension in report.scorecard.dimensions:
        if dimension.name == key:
            return round(dimension.score * 20, 1)
    return None


def _actionability_score(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    evidence_quality: str,
) -> float:
    score = 35.0

    if report.scorecard is not None and any(dimension.evidence.strip() for dimension in report.scorecard.dimensions):
        score += 10

    if jd_analysis is not None:
        score += 15 if jd_analysis.strengths else 5
        if jd_analysis.match_score >= 75:
            score += 10
        elif jd_analysis.match_score < 50:
            score -= 10
        score -= min(len(jd_analysis.gaps), 3) * 5
    else:
        score -= 10

    if resume_feedback is not None:
        score += 15 if resume_feedback.strengths else 5
        if resume_feedback.overall_score >= 70:
            score += 10
        elif resume_feedback.overall_score < 50:
            score -= 10
        score -= min(len(resume_feedback.missing_sections), 3) * 5
    else:
        score -= 10

    if evidence_quality == "high":
        score += 10
    elif evidence_quality == "low":
        score -= 15

    return round(max(0.0, min(score, 100.0)), 1)


def _label_from_rubric(
    *,
    evidence_quality: str,
    role_fit_score: float,
    actionability_score: float,
) -> VerdictLabel:
    if evidence_quality == "low":
        return "Hold" if max(role_fit_score, actionability_score) >= 45 else "Pass"
    if role_fit_score >= 72 and actionability_score >= 65:
        return "Go"
    if evidence_quality == "high" and role_fit_score < 45 and actionability_score < 45:
        return "Pass"
    return "Hold"


def _confidence_from_rubric(*, evidence_quality: str, coverage_count: int) -> str:
    if evidence_quality == "low":
        return "low"
    if evidence_quality == "high" and coverage_count >= 3:
        return "high"
    return "medium"


def _build_reasons(
    *,
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    evidence_quality: str,
    role_fit_score: float,
    actionability_score: float,
) -> list[str]:
    reasons = [
        _evidence_reason(report, evidence_quality),
        _role_fit_reason(report, jd_analysis, resume_feedback, role_fit_score),
        _actionability_reason(jd_analysis, resume_feedback, actionability_score),
    ]
    if report.scorecard is not None:
        reasons.append(f"기업 분석 {report.scorecard.total_score:.0f}/100")
    return [reason for reason in reasons if reason]


def _evidence_reason(report: AnalysisReport, evidence_quality: str) -> str:
    source_count = len(report.source_results)
    conflict_count = len(conflicting_keys(report.source_results)) if report.source_results else 0
    detail = f"근거 품질 {evidence_quality}: 추적 가능한 소스 {source_count}개"
    if conflict_count:
        detail += f", 상충 신호 {conflict_count}개"
    return detail


def _role_fit_reason(
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    role_fit_score: float,
) -> str:
    parts: list[str] = []
    job_fit = _dimension_score(report, "job_fit")
    if job_fit is not None:
        parts.append(f"기업 Job Fit {job_fit:.0f}/100")
    if jd_analysis is not None:
        parts.append(f"JD 매칭 {jd_analysis.match_score:.0f}/100")
    if resume_feedback is not None:
        parts.append(f"이력서 {resume_feedback.overall_score:.0f}/100")
    suffix = " · ".join(parts)
    return f"역할 적합도 {role_fit_score:.0f}/100: {suffix}" if suffix else f"역할 적합도 {role_fit_score:.0f}/100"


def _actionability_reason(
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    actionability_score: float,
) -> str:
    strengths = len(jd_analysis.strengths) if jd_analysis is not None else 0
    resume_strengths = len(resume_feedback.strengths) if resume_feedback is not None else 0
    gaps = len(jd_analysis.gaps) if jd_analysis is not None else 0
    return (
        f"실행 가능성 {actionability_score:.0f}/100: JD 강점 {strengths}개, "
        f"이력서 강점 {resume_strengths}개, 남은 갭 {gaps}개"
    )


def _build_cautions(
    *,
    report: AnalysisReport,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    evidence_quality: str,
    confidence: str,
    label: VerdictLabel,
) -> list[str]:
    cautions: list[str] = []

    if evidence_quality == "low":
        cautions.append("근거 신뢰도가 낮아 강한 지원 권고로 올리지 않았어요.")
    if any(result.is_stale for result in report.source_results):
        cautions.append("오래된 근거가 포함되어 있어 최신 공시·채용공고 재확인이 필요해요.")
    if report.source_results and conflicting_keys(report.source_results):
        cautions.append("출처 간 상충 신호가 있어 사실관계를 다시 검증해야 해요.")
    if jd_analysis is None:
        cautions.append("JD 정보가 없어 역할 적합도를 보수적으로 봤어요.")
    elif len(jd_analysis.gaps) >= 3:
        cautions.append("핵심 갭이 여러 개라 지원 메시지를 바로 제출하기엔 이르다고 봤어요.")
    if resume_feedback is None:
        cautions.append("이력서 정보가 없어 실제 제출 준비도는 별도 확인이 필요해요.")
    elif len(resume_feedback.missing_sections) >= 2:
        cautions.append("이력서 필수 정보가 비어 있어 실행 가능성을 낮게 봤어요.")
    if label != "Go" and confidence != "high":
        cautions.append("현재 판정은 우선순위 조정용 권고예요. 추가 확인 후 다시 보는 편이 안전해요.")

    return cautions


def _build_next_actions(
    *,
    label: VerdictLabel,
    jd_analysis: JDAnalysis | None,
    resume_feedback: ResumeFeedback | None,
    evidence_quality: str,
) -> list[str]:
    actions: list[str] = []

    if label == "Go":
        actions.extend(
            [
                "지원서에 바로 넣을 근거 문장 2개를 확정해요.",
                "JD와 맞는 핵심 경험 1개를 면접 사례로 압축해요.",
            ]
        )
    elif label == "Hold":
        actions.extend(
            [
                "최신 공시·채용공고·기술 블로그를 다시 확인해요.",
                "지원 여부를 다시 판단할 검증 질문 2개를 적어봐요.",
            ]
        )
    else:
        actions.extend(
            [
                "지금은 우선순위를 낮추고 더 강한 대안 기업과 비교해요.",
                "재도전 조건이 생길 때만 다시 평가할 기준을 적어둬요.",
            ]
        )

    if jd_analysis is not None and jd_analysis.gaps:
        actions.append(f"남은 갭인 {jd_analysis.gaps[0]}는 보완 계획 또는 설명 문장으로 정리해요.")
    elif resume_feedback is not None and resume_feedback.missing_sections:
        actions.append(f"누락된 섹션 {resume_feedback.missing_sections[0]}부터 채워 실행력을 높여요.")
    elif label == "Go":
        actions.append("제출 전 리스크 질문 2개를 미리 준비해요.")

    if evidence_quality == "low":
        actions.insert(0, "판정을 믿기 전에 최신 근거를 1~2개 더 추가 검증해요.")

    return actions[:4]


def _confidence_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(value, 0)
