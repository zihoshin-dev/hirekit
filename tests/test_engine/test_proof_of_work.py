from __future__ import annotations

from hirekit.engine.proof_of_work import ProofOfWorkGenerator


class TestProofOfWorkGenerator:
    def test_generate_ready_artifact_with_grounded_evidence(self):
        generator = ProofOfWorkGenerator()
        artifact = generator.generate(
            company="카카오",
            verdict={
                "label": "Go",
                "confidence": "high",
                "reasons": ["기업 분석 82/100", "JD 매칭 78/100"],
                "cautions": ["권고 결과이므로 제출 전 JD 최신 상태를 다시 확인해요."],
                "next_actions": ["지원서 핵심 문장 2개를 바로 작성해요."],
            },
            company_report={"scorecard": {"grade": "S"}},
            jd_analysis={"strengths": ["Python", "Kubernetes"]},
            resume_feedback={"strengths": ["결제 시스템 운영", "장애율 30% 감소"]},
        )
        assert artifact.status == "ready"
        assert artifact.evidence
        assert artifact.cautions
        assert artifact.next_actions[0] == "지원서 핵심 문장 2개를 바로 작성해요."
        md = artifact.to_markdown()
        assert "카카오" in md
        assert "기업 분석 82/100" in md
        assert "주의할 점" in md

    def test_low_confidence_refuses_full_execution_memo(self):
        generator = ProofOfWorkGenerator()
        artifact = generator.generate(
            company="가상회사",
            verdict={"label": "Hold", "confidence": "low", "reasons": []},
            company_report={"scorecard": {"grade": "C"}},
        )
        assert artifact.status == "needs_more_evidence"
        assert "추가 검증" in artifact.thesis
        assert artifact.cautions
        assert any("근거" in caution or "신뢰" in caution for caution in artifact.cautions)

    def test_markdown_includes_next_actions(self):
        generator = ProofOfWorkGenerator()
        artifact = generator.generate(
            company="네이버",
            verdict={
                "label": "Hold",
                "confidence": "medium",
                "reasons": ["기업 분석 68/100"],
                "cautions": ["근거가 일부만 확보되어 있어요."],
            },
            company_report={"scorecard": {"grade": "A"}},
        )
        md = artifact.to_markdown()
        assert "바로 할 일" in md
        assert "지원동기" in md
        assert "근거가 일부만 확보되어 있어요." in md
