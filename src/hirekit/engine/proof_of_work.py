from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class ProofOfWorkArtifact:
    company: str
    verdict: str
    confidence: str
    thesis: str
    evidence: list[str] = field(default_factory=list)
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
            next_actions=self.next_actions,
        )


class ProofOfWorkGenerator:
    def generate(
        self,
        *,
        company: str,
        verdict: dict[str, Any],
        company_report: dict[str, Any],
        jd_analysis: dict[str, Any] | None = None,
        resume_feedback: dict[str, Any] | None = None,
    ) -> ProofOfWorkArtifact:
        confidence = str(verdict.get("confidence", "low"))
        label = str(verdict.get("label", "Hold"))
        reasons = [str(reason) for reason in verdict.get("reasons", []) if str(reason).strip()]

        if confidence == "low" or not reasons:
            return ProofOfWorkArtifact(
                company=company,
                verdict=label,
                confidence=confidence,
                thesis="근거가 충분하지 않아 실행 메모를 만들기보다 추가 검증이 먼저예요.",
                evidence=reasons or ["판정 근거 부족"],
                next_actions=[
                    "최신 공시와 채용공고를 다시 확인해요.",
                    "지원 전 검증 질문 3개를 만들어요.",
                ],
                status="needs_more_evidence",
            )

        scorecard = company_report.get("scorecard", {})
        grade = scorecard.get("grade", "N/A")
        thesis = f"{company}는 현재 {label} 판단이며, 등급 {grade} 근거를 활용한 맞춤형 지원 메모를 준비할 가치가 있어요."

        evidence = reasons[:]
        if jd_analysis and jd_analysis.get("strengths"):
            evidence.append("JD 강점: " + ", ".join(jd_analysis["strengths"][:3]))
        if resume_feedback and resume_feedback.get("strengths"):
            evidence.append("이력서 강점: " + ", ".join(resume_feedback["strengths"][:3]))

        next_actions = [
            "지원동기에 바로 쓸 근거 문장 2개를 추려요.",
            "면접에서 설명할 정량 성과 1개를 준비해요.",
            "리스크 대응 질문 2개를 정리해요.",
        ]

        return ProofOfWorkArtifact(
            company=company,
            verdict=label,
            confidence=confidence,
            thesis=thesis,
            evidence=evidence,
            next_actions=next_actions,
        )
