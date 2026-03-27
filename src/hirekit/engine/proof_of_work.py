from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class ProofOfWorkArtifact:
    company: str
    verdict: str
    confidence: str
    thesis: str
    evidence: list[str] = field(default_factory=list)
    cautions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    status: str = "ready"

    def to_markdown(self) -> str:
        env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), trim_blocks=True, lstrip_blocks=True)
        template = env.get_template("proof_of_work_ko.md.j2")
        return template.render(
            company=self.company,
            verdict=self.verdict,
            confidence=self.confidence,
            thesis=self.thesis,
            evidence=self.evidence,
            cautions=self.cautions,
            next_actions=self.next_actions,
        )


class ProofOfWorkGenerator:
    def generate(
        self,
        *,
        company: str,
        verdict: Mapping[str, object],
        company_report: Mapping[str, object],
        jd_analysis: Mapping[str, object] | None = None,
        resume_feedback: Mapping[str, object] | None = None,
    ) -> ProofOfWorkArtifact:
        confidence = _string_value(verdict, "confidence", default="low")
        label = _string_value(verdict, "label", default="Hold")
        reasons = _string_list(verdict, "reasons")
        cautions = _string_list(verdict, "cautions")
        verdict_actions = _string_list(verdict, "next_actions")

        if confidence == "low" or not reasons:
            return ProofOfWorkArtifact(
                company=company,
                verdict=label,
                confidence=confidence,
                thesis="근거가 충분하지 않아 실행 메모를 확정하기보다 추가 검증이 먼저예요.",
                evidence=reasons or ["판정 근거 부족"],
                cautions=cautions or ["근거 신뢰도가 낮아 지금 단계에서는 실행 메모보다 검증 메모가 더 안전해요."],
                next_actions=verdict_actions
                or [
                    "최신 공시와 채용공고를 다시 확인해요.",
                    "지원 전 검증 질문 3개를 만들어요.",
                ],
                status="needs_more_evidence",
            )

        scorecard = _mapping_value(company_report, "scorecard")
        grade = _string_value(scorecard, "grade", default="N/A")
        thesis = _build_thesis(company=company, label=label, grade=grade, confidence=confidence)

        evidence = reasons[:]
        jd_strengths = _string_list(jd_analysis, "strengths") if jd_analysis is not None else []
        if jd_strengths:
            evidence.append("JD 강점: " + ", ".join(jd_strengths[:3]))
        resume_strengths = _string_list(resume_feedback, "strengths") if resume_feedback is not None else []
        if resume_strengths:
            evidence.append("이력서 강점: " + ", ".join(resume_strengths[:3]))

        return ProofOfWorkArtifact(
            company=company,
            verdict=label,
            confidence=confidence,
            thesis=thesis,
            evidence=evidence,
            cautions=cautions,
            next_actions=verdict_actions or _default_next_actions(label),
        )


def _build_thesis(*, company: str, label: str, grade: str, confidence: str) -> str:
    if label == "Go":
        return (
            f"{company}는 현재 {label} 권고예요. 등급 {grade}와 정렬된 역할 근거가 있어 "
            "바로 지원 메모로 압축할 가치가 있어요."
        )
    if label == "Hold":
        return (
            f"{company}는 현재 {label} 권고예요. 등급 {grade} 근거는 있지만 "
            f"신뢰도 {confidence} 상태라 제출 전 보완 포인트를 먼저 정리하는 편이 안전해요."
        )
    return (
        f"{company}는 현재 {label} 권고예요. 등급 {grade} 기준으로는 우선순위를 낮추고 "
        "더 강한 대안을 비교하는 편이 좋아요."
    )


def _default_next_actions(label: str) -> list[str]:
    if label == "Go":
        return [
            "지원동기에 바로 쓸 근거 문장 2개를 추려요.",
            "면접에서 설명할 정량 성과 1개를 준비해요.",
            "리스크 대응 질문 2개를 정리해요.",
        ]
    if label == "Hold":
        return [
            "지원 여부를 다시 판단할 검증 질문 2개를 적어요.",
            "지원동기에 쓸 수 있는 근거와 비어 있는 근거를 나눠 적어요.",
            "부족한 근거와 충돌 지점을 먼저 확인해요.",
            "최신 채용공고·기술 스택·보상 정보를 추가 수집해요.",
        ]
    return [
        "현재 근거로는 우선순위를 낮추고 다른 타깃을 비교해요.",
        "재평가 조건이 생길 때만 다시 검토해요.",
        "리스크를 감수할 이유가 있는지 먼저 점검해요.",
    ]


def _string_value(mapping: Mapping[str, object], key: str, *, default: str) -> str:
    value = mapping.get(key, default)
    return value if isinstance(value, str) and value.strip() else default


def _mapping_value(mapping: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = mapping.get(key, {})
    return cast(Mapping[str, object], value) if isinstance(value, Mapping) else {}


def _string_list(mapping: Mapping[str, object] | None, key: str) -> list[str]:
    if mapping is None:
        return []
    value = mapping.get(key, [])
    if not isinstance(value, list):
        return []
    items = cast(list[object], value)
    return [item for item in items if isinstance(item, str) and item.strip()]
