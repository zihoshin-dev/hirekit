"""Cross-functional advisory panel synthesis for career decisions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from hirekit.engine.career_strategy import CareerStrategy
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.company_comparator import ComparisonResult
from hirekit.engine.hero_verdict import HeroVerdict
from hirekit.engine.jd_matcher import JDAnalysis
from hirekit.engine.resume_advisor import ResumeFeedback

PanelVerdict = Literal["Go", "Hold", "Pass"]


@dataclass
class PanelLens:
    """One expert-council lens inside the advisory panel."""

    key: str
    title: str
    verdict: PanelVerdict
    confidence: str
    summary: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class AdvisoryPanel:
    """Structured multi-lens advisory panel for a target company."""

    company: str
    overall_verdict: PanelVerdict
    overall_confidence: str
    consensus_summary: str
    lenses: list[PanelLens]
    next_actions: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# Advisory Panel: {self.company}",
            f"- 종합 판정: {self.overall_verdict}",
            f"- 신뢰도: {self.overall_confidence}",
            "",
            self.consensus_summary,
        ]
        if self.next_actions:
            lines.extend(
                [
                    "",
                    "## 바로 할 일",
                    *[f"- {item}" for item in self.next_actions],
                ]
            )
        lines.append("")
        lines.append("## 패널 렌즈")
        for lens in self.lenses:
            lines.extend(
                [
                    "",
                    f"### {lens.title}",
                    f"- 판정: {lens.verdict}",
                    f"- 신뢰도: {lens.confidence}",
                    lens.summary,
                    *[f"- {item}" for item in lens.evidence],
                ]
            )
        return "\n".join(lines)


def compose_advisory_panel(
    *,
    report: AnalysisReport,
    hero_verdict: HeroVerdict,
    jd_analysis: JDAnalysis | None = None,
    resume_feedback: ResumeFeedback | None = None,
    strategy_result: CareerStrategy | None = None,
    comparison_result: ComparisonResult | None = None,
) -> AdvisoryPanel:
    dims = {dimension.name: dimension for dimension in (report.scorecard.dimensions if report.scorecard else [])}
    target_company = report.company
    war_room = report.to_dict().get("war_room", {})

    hiring_score = _average(
        [
            hero_verdict.combined_score,
            getattr(jd_analysis, "match_score", None),
            getattr(resume_feedback, "overall_score", None),
        ]
    )
    hiring_lens = PanelLens(
        key="hiring",
        title="Hiring & Career Committee",
        verdict=_verdict_from_score(hiring_score),
        confidence=hero_verdict.confidence,
        summary=(
            f"채용 관점 종합 점수는 {hiring_score:.0f}/100이에요. 지원 시점과 준비도 판단에 직접 연결되는 렌즈예요."
        ),
        evidence=_compact_evidence(
            [
                _hero_evidence(hero_verdict),
                _jd_evidence(jd_analysis),
                _resume_evidence(resume_feedback),
                _war_room_role_evidence(war_room),
            ]
        ),
    )

    engineering_score = _average(
        [
            _dimension_score(dims, "job_fit"),
            _comparison_dimension_score(comparison_result, target_company, "tech_level"),
        ]
    )
    engineering_lens = PanelLens(
        key="engineering",
        title="Engineering Council",
        verdict=_verdict_from_score(engineering_score),
        confidence=_confidence_from_items(
            dims.get("job_fit") is not None,
            comparison_result is not None,
        ),
        summary=(f"엔지니어링 적합도는 {engineering_score:.0f}/100이에요. 기술 스택 적합성과 비교 우위를 같이 봐요."),
        evidence=_compact_evidence(
            [
                _dimension_evidence(dims, "job_fit"),
                _comparison_winner_evidence(comparison_result, "tech_level", "기술 수준"),
                _war_room_stack_evidence(war_room),
                _war_room_actual_work_evidence(war_room),
            ]
        ),
    )

    product_score = _average(
        [
            _dimension_score(dims, "growth"),
            _dimension_score(dims, "career_leverage"),
            _comparison_overall_score(comparison_result, target_company),
        ]
    )
    product_lens = PanelLens(
        key="product",
        title="Founder, Product & Market Council",
        verdict=_verdict_from_score(product_score),
        confidence=_confidence_from_items(
            dims.get("growth") is not None,
            dims.get("career_leverage") is not None,
            comparison_result is not None,
        ),
        summary=(
            f"시장성과 커리어 레버리지 기준 점수는 {product_score:.0f}/100이에요. "
            "성장성과 브랜드/시장 포지션을 함께 평가해요."
        ),
        evidence=_compact_evidence(
            [
                _dimension_evidence(dims, "growth"),
                _dimension_evidence(dims, "career_leverage"),
                _comparison_recommendation_evidence(comparison_result),
                _war_room_growth_evidence(war_room),
            ]
        ),
    )

    risk_score = _risk_score(
        hero_verdict=hero_verdict,
        culture_score=_dimension_score(dims, "culture_fit"),
        compensation_score=_dimension_score(dims, "compensation"),
        strategy_result=strategy_result,
    )
    risk_lens = PanelLens(
        key="risk",
        title="Risk, Legal & Governance Council",
        verdict=_verdict_from_score(risk_score, go_threshold=70, hold_threshold=45),
        confidence=_confidence_from_items(
            dims.get("culture_fit") is not None,
            dims.get("compensation") is not None,
            strategy_result is not None,
        ),
        summary=(
            f"리스크/가드레일 점수는 {risk_score:.0f}/100이에요. 신호가 약하거나 준비 기간이 길면 더 보수적으로 봐요."
        ),
        evidence=_compact_evidence(
            [
                _dimension_evidence(dims, "culture_fit"),
                _dimension_evidence(dims, "compensation"),
                _strategy_timeline_evidence(strategy_result),
                _war_room_org_health_evidence(war_room),
            ]
        ),
    )

    career_score = _average(
        [
            getattr(strategy_result, "fit_score", None),
            hiring_score,
        ]
    )
    career_lens = PanelLens(
        key="career",
        title="Career Coach Council",
        verdict=_verdict_from_score(career_score),
        confidence=_confidence_from_items(strategy_result is not None, True),
        summary=(
            f"개인화 전략 관점 점수는 {career_score:.0f}/100이에요. "
            "현재 프로필 기준으로 얼마나 현실적으로 준비 가능한지 봐요."
        ),
        evidence=_compact_evidence(
            [
                _strategy_fit_evidence(strategy_result),
                _strategy_gap_evidence(strategy_result),
                _war_room_role_evidence(war_room),
            ]
        ),
    )

    lenses = [
        hiring_lens,
        engineering_lens,
        product_lens,
        risk_lens,
        career_lens,
    ]
    overall_verdict = _consensus_verdict(lenses, hero_verdict.label)
    overall_confidence = _consensus_confidence(lenses, hero_verdict.confidence)
    next_actions = _panel_next_actions(
        hero_verdict=hero_verdict,
        strategy_result=strategy_result,
        comparison_result=comparison_result,
        overall_verdict=overall_verdict,
    )

    return AdvisoryPanel(
        company=target_company,
        overall_verdict=overall_verdict,
        overall_confidence=overall_confidence,
        consensus_summary=_consensus_summary(lenses, overall_verdict),
        lenses=lenses,
        next_actions=next_actions,
    )


def _average(values: list[float | None]) -> float:
    clean = [value for value in values if value is not None]
    if not clean:
        return 50.0
    return round(sum(clean) / len(clean), 1)


def _verdict_from_score(
    score: float,
    *,
    go_threshold: float = 65,
    hold_threshold: float = 40,
) -> PanelVerdict:
    if score >= go_threshold:
        return "Go"
    if score >= hold_threshold:
        return "Hold"
    return "Pass"


def _dimension_score(dims: Mapping[str, object], key: str) -> float | None:
    dimension = dims.get(key)
    if dimension is None:
        return None
    return round(float(getattr(dimension, "score", 0.0)) * 20, 1)


def _dimension_evidence(dims: Mapping[str, object], key: str) -> str | None:
    dimension = dims.get(key)
    if dimension is None:
        return None
    evidence = str(getattr(dimension, "evidence", "")).strip()
    label = str(getattr(dimension, "label", key)).strip()
    if not evidence:
        return None
    return f"{label}: {evidence}"


def _comparison_dimension_score(
    comparison_result: ComparisonResult | None,
    company: str,
    key: str,
) -> float | None:
    if comparison_result is None:
        return None
    company_scores = comparison_result.comparison_table.get("scores", {}).get(company, {})
    value = company_scores.get(key)
    if value is None:
        return None
    return round(float(value) * 20, 1)


def _comparison_overall_score(
    comparison_result: ComparisonResult | None,
    company: str,
) -> float | None:
    if comparison_result is None:
        return None
    return comparison_result.overall_scores.get(company)


def _comparison_winner_evidence(
    comparison_result: ComparisonResult | None,
    key: str,
    label: str,
) -> str | None:
    if comparison_result is None:
        return None
    winner = comparison_result.winner_by_dimension.get(key)
    if not winner:
        return None
    return f"{label} 차원 우세: {winner}"


def _comparison_recommendation_evidence(
    comparison_result: ComparisonResult | None,
) -> str | None:
    if comparison_result is None:
        return None
    return comparison_result.overall_recommendation.splitlines()[0].strip()


def _war_room_role_evidence(war_room: dict[str, object]) -> str | None:
    expectations = war_room.get("role_expectations", [])
    if not isinstance(expectations, list) or not expectations:
        return None
    return "역할 기대치: " + ", ".join(str(item) for item in expectations[:3])


def _war_room_stack_evidence(war_room: dict[str, object]) -> str | None:
    stack = war_room.get("stack_reality", {})
    if not isinstance(stack, dict):
        return None
    confirmed = stack.get("confirmed", [])
    likely = stack.get("likely", [])
    parts: list[str] = []
    if isinstance(confirmed, list) and confirmed:
        parts.append("확인 스택: " + ", ".join(str(item) for item in confirmed[:3]))
    if isinstance(likely, list) and likely:
        parts.append("가능성 높은 스택: " + ", ".join(str(item) for item in likely[:3]))
    return " / ".join(parts) if parts else None


def _war_room_actual_work_evidence(war_room: dict[str, object]) -> str | None:
    actual_work = war_room.get("actual_work", [])
    if not isinstance(actual_work, list) or not actual_work:
        return None
    return "실제 업무 신호: " + ", ".join(str(item) for item in actual_work[:3])


def _war_room_growth_evidence(war_room: dict[str, object]) -> str | None:
    growth = war_room.get("growth_reality", {})
    if not isinstance(growth, dict) or not growth:
        return None
    direction = growth.get("revenue_growth_direction")
    rate = growth.get("revenue_growth_rate")
    if direction is None and rate is None:
        return None
    return f"성장 현실: 방향={direction or 'unknown'}, 성장률={rate if rate is not None else 'unknown'}"


def _war_room_org_health_evidence(war_room: dict[str, object]) -> str | None:
    org = war_room.get("org_health", {})
    if not isinstance(org, dict):
        return None
    state = str(org.get("state") or "unknown")
    verified = org.get("verified", [])
    supporting = org.get("supporting", [])
    facts: list[str] = []
    if isinstance(verified, list):
        facts.extend(str(item) for item in verified[:2])
    if isinstance(supporting, list) and not facts:
        facts.extend(str(item) for item in supporting[:2])
    if not facts and state == "unknown":
        return "조직 건강: 확인 가능한 근거가 부족해요"
    if not facts:
        return f"조직 건강 상태: {state}"
    return f"조직 건강({state}): " + ", ".join(facts)


def _confidence_from_items(*items: bool) -> str:
    hits = sum(1 for item in items if item)
    if hits >= 3:
        return "high"
    if hits >= 2:
        return "medium"
    return "low"


def _risk_score(
    *,
    hero_verdict: HeroVerdict,
    culture_score: float | None,
    compensation_score: float | None,
    strategy_result: CareerStrategy | None,
) -> float:
    score = _average([culture_score, compensation_score, hero_verdict.combined_score])
    if hero_verdict.confidence == "low":
        score -= 15
    elif hero_verdict.confidence == "medium":
        score -= 5
    if strategy_result is not None:
        if "6-12개월" in strategy_result.timeline:
            score -= 15
        elif "3-4개월" in strategy_result.timeline:
            score -= 8
    return max(0.0, round(score, 1))


def _consensus_verdict(
    lenses: list[PanelLens],
    hero_label: PanelVerdict,
) -> PanelVerdict:
    counts = {"Go": 0, "Hold": 0, "Pass": 0}
    for lens in lenses:
        counts[lens.verdict] += 1
    if counts["Pass"] >= 2:
        return "Pass"
    if counts["Go"] >= 3:
        return "Go"
    return hero_label if hero_label != "Go" or counts["Pass"] == 0 else "Hold"


def _consensus_confidence(
    lenses: list[PanelLens],
    hero_confidence: str,
) -> str:
    high = sum(1 for lens in lenses if lens.confidence == "high")
    medium = sum(1 for lens in lenses if lens.confidence == "medium")
    if high >= 3:
        return "high"
    if high + medium >= 3:
        return "medium"
    return hero_confidence


def _consensus_summary(
    lenses: list[PanelLens],
    overall_verdict: PanelVerdict,
) -> str:
    go_titles = [lens.title for lens in lenses if lens.verdict == "Go"]
    caution_titles = [lens.title for lens in lenses if lens.verdict != "Go"]
    if overall_verdict == "Go":
        return f"{len(go_titles)}개 렌즈가 긍정적이에요. 핵심 지지 렌즈: {', '.join(go_titles[:3])}."
    return f"보수적으로 접근해야 해요. 경계 렌즈: {', '.join(caution_titles[:3])}."


def _panel_next_actions(
    *,
    hero_verdict: HeroVerdict,
    strategy_result: CareerStrategy | None,
    comparison_result: ComparisonResult | None,
    overall_verdict: PanelVerdict,
) -> list[str]:
    actions: list[str] = []
    if overall_verdict == "Go":
        actions.append("이번 주 안에 지원서/이력서 버전을 고정하고 제출해요.")
    elif overall_verdict == "Hold":
        actions.append("지원 전 핵심 갭과 리스크를 먼저 정리해요.")
    else:
        actions.append("지금은 무리하게 지원하지 말고 대안 기업으로 우선순위를 옮겨요.")

    if strategy_result is not None and strategy_result.gap_analysis:
        top_gap = strategy_result.gap_analysis[0]
        actions.append(f"가장 중요한 갭인 {top_gap.skill} 보완 계획을 1개 작성해요.")
    if comparison_result is not None and comparison_result.winner != comparison_result.companies[0]:
        actions.append(f"비교 우세 기업인 {comparison_result.winner}도 병행 검토해요.")
    if hero_verdict.confidence != "high":
        actions.append("판정 신뢰도가 높지 않으니 추가 근거를 1~2개 더 수집해요.")
    return actions


def _compact_evidence(items: list[str | None]) -> list[str]:
    return [item for item in items if item]


def _hero_evidence(hero_verdict: HeroVerdict) -> str:
    return f"Hero Verdict {hero_verdict.label} ({hero_verdict.combined_score:.0f}/100, {hero_verdict.confidence})"


def _jd_evidence(jd_analysis: JDAnalysis | None) -> str | None:
    if jd_analysis is None:
        return None
    return f"JD 매칭 {jd_analysis.match_score:.0f}/100"


def _resume_evidence(resume_feedback: ResumeFeedback | None) -> str | None:
    if resume_feedback is None:
        return None
    return f"이력서 {resume_feedback.overall_score:.0f}/100"


def _strategy_fit_evidence(strategy_result: CareerStrategy | None) -> str | None:
    if strategy_result is None:
        return None
    return f"전략 적합도 {strategy_result.fit_score:.0f}/100"


def _strategy_gap_evidence(strategy_result: CareerStrategy | None) -> str | None:
    if strategy_result is None or not strategy_result.gap_analysis:
        return None
    top_gap = strategy_result.gap_analysis[0]
    return f"핵심 갭 {top_gap.skill} ({top_gap.importance})"


def _strategy_timeline_evidence(strategy_result: CareerStrategy | None) -> str | None:
    if strategy_result is None:
        return None
    return f"권장 준비 기간: {strategy_result.timeline}"
