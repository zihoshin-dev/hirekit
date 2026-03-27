"""Career strategy engine — rule-based analysis for job seekers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import cast

from hirekit.core.company_db import get_default_db
from hirekit.core.tech_taxonomy import (
    classify_experience,
    get_category,
    normalize_tech,
)
from hirekit.engine.business_segments import summarize_growth_reality
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.data_reviewer import DataReviewer
from hirekit.engine.jd_matcher import JDAnalysis
from hirekit.engine.resume_advisor import ResumeFeedback
from hirekit.engine.scorer import ScoreDimension

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SkillGap:
    """A single skill the user lacks that the target company needs."""

    skill: str
    category: str  # e.g. "Backend", "DevOps", "ML/AI"
    importance: str  # "required" | "preferred"
    learning_suggestion: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "skill": self.skill,
            "category": self.category,
            "importance": self.importance,
            "learning_suggestion": self.learning_suggestion,
        }


@dataclass
class CareerProfile:
    """User's career profile for strategy analysis."""

    target_company: str
    current_company: str | None = None
    years_of_experience: int = 0
    current_role: str = ""
    target_role: str = ""
    skills: list[str] = field(default_factory=list)
    education: str | None = None


@dataclass
class GroundedStrategySections:
    why_role_matters: list[str] = field(default_factory=list)
    why_to_hesitate: list[str] = field(default_factory=list)
    application_changes: list[str] = field(default_factory=list)
    verify_next: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "why_role_matters": self.why_role_matters,
            "why_to_hesitate": self.why_to_hesitate,
            "application_changes": self.application_changes,
            "verify_next": self.verify_next,
        }


@dataclass
class CareerStrategy:
    """Structured career strategy result."""

    fit_score: float  # 0-100
    gap_analysis: list[SkillGap]
    approach_strategy: str
    resume_focus: list[str]
    interview_prep: list[str]
    timeline: str
    alternative_companies: list[str]
    career_path: str
    risk_assessment: str
    grounded_recommendations: GroundedStrategySections = field(default_factory=GroundedStrategySections)

    def to_dict(self) -> dict[str, object]:
        return {
            "fit_score": self.fit_score,
            "gap_analysis": [gap.to_dict() for gap in self.gap_analysis],
            "approach_strategy": self.approach_strategy,
            "resume_focus": self.resume_focus,
            "interview_prep": self.interview_prep,
            "timeline": self.timeline,
            "alternative_companies": self.alternative_companies,
            "career_path": self.career_path,
            "risk_assessment": self.risk_assessment,
            "grounded_recommendations": self.grounded_recommendations.to_dict(),
        }


# ---------------------------------------------------------------------------
# Company knowledge base (rule-based, no LLM)
# ---------------------------------------------------------------------------

# Known tech stacks for major Korean/global companies
_COMPANY_TECH_STACK: dict[str, list[str]] = {
    "토스": ["kotlin", "spring", "react", "typescript", "aws", "kubernetes", "kafka"],
    "toss": ["kotlin", "spring", "react", "typescript", "aws", "kubernetes", "kafka"],
    "카카오": ["java", "spring", "react", "python", "kafka", "kubernetes", "mysql"],
    "kakao": ["java", "spring", "react", "python", "kafka", "kubernetes", "mysql"],
    "네이버": ["java", "spring", "python", "react", "kafka", "kubernetes", "mysql"],
    "naver": ["java", "spring", "python", "react", "kafka", "kubernetes", "mysql"],
    "라인": ["java", "go", "kotlin", "react", "kafka", "kubernetes"],
    "line": ["java", "go", "kotlin", "react", "kafka", "kubernetes"],
    "쿠팡": ["java", "kotlin", "spring", "react", "aws", "kafka", "kubernetes"],
    "coupang": ["java", "kotlin", "spring", "react", "aws", "kafka", "kubernetes"],
    "배달의민족": ["kotlin", "spring", "react", "aws", "kafka", "mysql"],
    "baemin": ["kotlin", "spring", "react", "aws", "kafka", "mysql"],
    "당근마켓": ["go", "kotlin", "react", "postgresql", "aws", "kubernetes"],
    "당근": ["go", "kotlin", "react", "postgresql", "aws", "kubernetes"],
    "daangn": ["go", "kotlin", "react", "postgresql", "aws", "kubernetes"],
    "google": ["python", "java", "go", "c++", "kubernetes", "tensorflow", "gcp"],
    "구글": ["python", "java", "go", "c++", "kubernetes", "tensorflow", "gcp"],
    "meta": ["python", "react", "pytorch", "c++", "java", "hack"],
    "amazon": ["java", "python", "aws", "kotlin", "typescript", "react"],
    "netflix": ["java", "python", "react", "aws", "kafka", "spark"],
    "airbnb": ["java", "python", "react", "typescript", "airflow"],
    "삼성": ["java", "c++", "python", "react", "android"],
    "samsung": ["java", "c++", "python", "react", "android"],
    "lg": ["java", "c++", "python", "spring"],
    "현대": ["java", "spring", "python", "android"],
    "sk": ["java", "spring", "python", "aws"],
}

# Similar companies by domain/culture
_SIMILAR_COMPANIES: dict[str, list[str]] = {
    "토스": ["카카오페이", "네이버파이낸셜", "뱅크샐러드", "핀다", "크래프톤"],
    "toss": ["kakao pay", "naver financial", "banksalad", "finda"],
    "카카오": ["네이버", "라인", "쿠팡", "배달의민족"],
    "kakao": ["naver", "line", "coupang"],
    "네이버": ["카카오", "라인", "쿠팡"],
    "naver": ["kakao", "line", "coupang"],
    "쿠팡": ["배달의민족", "마켓컬리", "오아시스", "11번가"],
    "coupang": ["baemin", "kurly", "oasis"],
    "배달의민족": ["쿠팡이츠", "요기요", "쿠팡"],
    "당근마켓": ["번개장터", "중고나라", "숨고"],
    "당근": ["번개장터", "중고나라", "숨고"],
    "google": ["meta", "amazon", "microsoft", "apple"],
    "meta": ["google", "amazon", "microsoft"],
    "amazon": ["google", "meta", "microsoft"],
}

# Career path suggestions by role
_CAREER_PATHS: dict[str, str] = {
    "backend": "주니어 BE → 시니어 BE → Tech Lead → Engineering Manager 또는 Principal Engineer",
    "frontend": "주니어 FE → 시니어 FE → FE Lead → Full-stack Lead 또는 Frontend Architect",
    "fullstack": "Full-stack → Tech Lead → Engineering Manager 또는 CTO 트랙",
    "data": "데이터 분석가 → 시니어 → Data Lead → Head of Data 또는 Data Platform Engineer",
    "ml": "ML Engineer → Senior MLE → Staff MLE → ML Platform Lead 또는 Research Engineer",
    "devops": "DevOps Engineer → Senior DevOps → Platform Lead → Staff Engineer (Infra)",
    "pm": "Junior PM → PM → Senior PM → Group PM → CPO 트랙",
    "designer": "Junior UX → UX Designer → Senior UX → Design Lead → Head of Design",
    "mobile": "Mobile Engineer → Senior Mobile → Tech Lead → Principal Engineer",
    "security": "보안 엔지니어 → Senior → Security Lead → CISO 트랙",
}

# Learning suggestions for common skills
_LEARNING_SUGGESTIONS: dict[str, str] = {
    "kotlin": "Kotlin 공식 문서 + 사이드 프로젝트 1개 (3-4주)",
    "spring": "Spring Boot 공식 가이드 + REST API 프로젝트 (4-6주)",
    "react": "React 공식 문서 → 토이 프로젝트 (2-4주)",
    "typescript": "TypeScript Handbook → JS 프로젝트 마이그레이션 (1-2주)",
    "aws": "AWS Free Tier 실습 → SAA 자격증 (1-2개월)",
    "kubernetes": "K8s 공식 튜토리얼 → minikube 실습 → CKA 준비 (2-3개월)",
    "kafka": "Confluent Kafka 101 → 스트리밍 파이프라인 실습 (2-3주)",
    "docker": "Docker 공식 튜토리얼 → Docker Compose 실습 (1-2주)",
    "go": "Go 공식 투어 (tour.golang.org) → CLI 툴 제작 (3-4주)",
    "python": "Python 공식 튜토리얼 → FastAPI 프로젝트 (2-3주)",
    "pytorch": "PyTorch 튜토리얼 → Kaggle 참여 (1개월)",
    "tensorflow": "TensorFlow 공식 가이드 → 모델 배포 실습 (1개월)",
    "spark": "Spark 공식 퀵스타트 → PySpark 실습 (2-3주)",
    "postgresql": "PostgreSQL 공식 문서 → 실습 프로젝트 DB 적용 (1-2주)",
    "redis": "Redis 공식 문서 → 캐싱 레이어 구현 실습 (1주)",
    "terraform": "Terraform 공식 튜토리얼 → 인프라 코드화 (2-3주)",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class CareerStrategyEngine:
    """Rule-based career strategy analyzer — no LLM required."""

    def analyze(
        self,
        profile: CareerProfile,
        *,
        company_report: AnalysisReport | None = None,
        jd_analysis: JDAnalysis | None = None,
        resume_feedback: ResumeFeedback | None = None,
    ) -> CareerStrategy:
        """Generate a career strategy for the given profile.

        Steps:
        1. Load target company tech stack
        2. Compute skill gap (user skills vs company stack)
        3. Score fit (0-100)
        4. Generate approach strategy, resume focus, interview prep
        5. Recommend timeline and alternative companies
        6. Compose grounded strategy sections from structured evidence when available
        """
        company_key = profile.target_company.lower()
        company_stack = self._get_company_stack(company_key)

        # Normalize user skills
        user_skills_norm = {normalize_tech(s.lower()) for s in profile.skills}
        user_skills_raw = {s.lower() for s in profile.skills}
        all_user_skills = user_skills_norm | user_skills_raw

        # Skill gap analysis
        gap_analysis = self._compute_gaps(company_stack, all_user_skills)

        # Fit score
        fit_score = self._compute_fit_score(profile, company_stack, all_user_skills, gap_analysis)

        # Approach strategy
        approach_strategy = self._build_approach_strategy(profile, fit_score, gap_analysis)

        # Resume focus
        resume_focus = self._build_resume_focus(profile, company_key, all_user_skills)

        # Interview prep
        interview_prep = self._build_interview_prep(profile, company_key, gap_analysis)

        # Timeline
        timeline = self._recommend_timeline(gap_analysis, fit_score)

        # Alternatives
        alternative_companies = _SIMILAR_COMPANIES.get(company_key, _SIMILAR_COMPANIES.get(profile.target_company, []))[
            :5
        ]

        # Career path
        career_path = self._suggest_career_path(profile)

        # Risk assessment
        risk_assessment = self._assess_risk(profile, fit_score, gap_analysis)

        grounded_recommendations = self._build_grounded_recommendations(
            profile=profile,
            fit_score=fit_score,
            gaps=gap_analysis,
            company_report=company_report,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
        )

        return CareerStrategy(
            fit_score=fit_score,
            gap_analysis=gap_analysis,
            approach_strategy=approach_strategy,
            resume_focus=resume_focus,
            interview_prep=interview_prep,
            timeline=timeline,
            alternative_companies=alternative_companies,
            career_path=career_path,
            risk_assessment=risk_assessment,
            grounded_recommendations=grounded_recommendations,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_grounded_recommendations(
        self,
        *,
        profile: CareerProfile,
        fit_score: float,
        gaps: list[SkillGap],
        company_report: AnalysisReport | None,
        jd_analysis: JDAnalysis | None,
        resume_feedback: ResumeFeedback | None,
    ) -> GroundedStrategySections:
        sections = GroundedStrategySections()
        war_room = self._war_room_payload(company_report)
        score_dimensions = self._score_dimensions(company_report)
        growth_summary = self._growth_summary(company_report)
        compensation_summary = self._compensation_summary(company_report, war_room)
        org_health_bucket = self._org_health_bucket(company_report, war_room)

        self._append_unique(
            sections.why_role_matters,
            self._dimension_summary(score_dimensions.get("job_fit")),
        )
        self._append_unique(
            sections.why_role_matters,
            self._dimension_summary(score_dimensions.get("career_leverage")),
        )
        self._append_unique(sections.why_role_matters, growth_summary)
        self._append_unique(
            sections.why_role_matters,
            self._role_reality_summary(war_room),
        )

        if jd_analysis is not None:
            if jd_analysis.hard_alignment:
                self._append_unique(
                    sections.why_role_matters,
                    f"[jd/hard_alignment] {jd_analysis.hard_alignment[0]}",
                )
            elif jd_analysis.soft_alignment:
                self._append_unique(
                    sections.why_role_matters,
                    f"[jd/soft_alignment] {jd_analysis.soft_alignment[0]}",
                )

            if jd_analysis.role_reality_mismatches:
                self._append_unique(
                    sections.why_to_hesitate,
                    f"[jd/role_reality_mismatch] {jd_analysis.role_reality_mismatches[0]}",
                )
            if jd_analysis.gaps:
                self._append_unique(
                    sections.why_to_hesitate,
                    f"[jd/gap] {jd_analysis.gaps[0]} 요구 근거를 아직 직접 보여주지 못해요.",
                )
                self._append_unique(
                    sections.application_changes,
                    f"[application/jd_gap] {jd_analysis.gaps[0]}는 유사 경험 또는 학습 계획과 함께 지원서에 명시해요.",
                )
            for item in jd_analysis.ambiguous_expectations[:2]:
                self._append_unique(
                    sections.verify_next,
                    f"needs verification — jd: {item}",
                )

        if resume_feedback is not None:
            for item in resume_feedback.strengths[:2]:
                self._append_unique(
                    sections.why_role_matters,
                    f"[resume/strength] {item}",
                )
            if resume_feedback.missing_proof:
                self._append_unique(
                    sections.why_to_hesitate,
                    f"[resume/missing_proof] {resume_feedback.missing_proof[0]}",
                )
            for item in resume_feedback.missing_proof[:2]:
                self._append_unique(
                    sections.application_changes,
                    f"[application/proof] {item}",
                )
            for item in resume_feedback.transferability_opportunities[:2]:
                self._append_unique(
                    sections.application_changes,
                    f"[application/transferability] {item}",
                )
            for item in resume_feedback.tailored_suggestions[:2]:
                self._append_unique(
                    sections.application_changes,
                    f"[application/tailoring] {item}",
                )

        self._append_org_health_guidance(
            sections=sections,
            org_health_bucket=org_health_bucket,
        )

        if compensation_summary:
            if "unknown" in compensation_summary:
                self._append_unique(sections.verify_next, f"needs verification — {compensation_summary}")
            else:
                self._append_unique(sections.why_role_matters, compensation_summary)

        if gaps:
            top_gap = gaps[0]
            self._append_unique(
                sections.why_to_hesitate,
                f"[skill_gap/{top_gap.importance}] {top_gap.skill} 근거가 아직 부족해요.",
            )
            self._append_unique(
                sections.application_changes,
                (
                    f"[application/skill_gap] {top_gap.skill}는 "
                    f"{top_gap.learning_suggestion} 수준의 보완 계획을 짧게 넣어요."
                ),
            )

        if not sections.why_role_matters:
            self._append_unique(
                sections.why_role_matters,
                (
                    f"[fit/generated] {profile.target_company} 기준 적합도 "
                    f"{fit_score:.0f}/100으로 현재 프로필과 기본 정렬이 보여요."
                ),
            )
        if not sections.why_to_hesitate:
            self._append_unique(
                sections.why_to_hesitate,
                "[unknown] 치명적 경고는 아직 많지 않지만 확인되지 않은 근거는 그대로 남겨 두고 판단해야 해요.",
            )
        if not sections.application_changes:
            if profile.skills:
                self._append_unique(
                    sections.application_changes,
                    (
                        f"[application/generated] 보유 기술 {profile.skills[0]}로 만든 "
                        "실제 성과 문장을 지원서 첫 단락에 배치해요."
                    ),
                )
            else:
                self._append_unique(
                    sections.application_changes,
                    "[application/generated] 현재 역할에서 만든 정량 성과 1개를 먼저 지원서 상단에 추가해요.",
                )
        if not sections.verify_next:
            self._append_unique(
                sections.verify_next,
                "needs verification — 구조화된 회사/JD/이력서 근거가 충분하지 않아 추가 확인이 먼저예요.",
            )

        sections.why_role_matters = sections.why_role_matters[:4]
        sections.why_to_hesitate = sections.why_to_hesitate[:4]
        sections.application_changes = sections.application_changes[:4]
        sections.verify_next = sections.verify_next[:4]
        return sections

    @staticmethod
    def _append_unique(items: list[str], value: str) -> None:
        normalized = value.strip()
        if normalized and normalized not in items:
            items.append(normalized)

    @staticmethod
    def _war_room_payload(company_report: AnalysisReport | None) -> dict[str, object]:
        if company_report is None:
            return {}
        report_dict = cast(dict[str, object], company_report.to_dict())
        payload = report_dict.get("war_room")
        return CareerStrategyEngine._mapping_dict(payload)

    @staticmethod
    def _score_dimensions(company_report: AnalysisReport | None) -> dict[str, ScoreDimension]:
        if company_report is None or company_report.scorecard is None:
            return {}
        return {dimension.name: dimension for dimension in company_report.scorecard.dimensions}

    @staticmethod
    def _dimension_summary(dimension: ScoreDimension | None) -> str:
        if dimension is None or not dimension.evidence.strip():
            return ""
        score = round(dimension.score * 20, 1)
        confidence = dimension.confidence or "unknown"
        return f"[scorecard/{confidence}] {dimension.label} {score:.0f}/100 — {dimension.evidence}"

    def _role_reality_summary(self, war_room: Mapping[str, object]) -> str:
        role_expectations = self._string_list(war_room.get("role_expectations"))
        actual_work = self._string_list(war_room.get("actual_work"))
        stack_reality = self._mapping_dict(war_room.get("stack_reality"))

        if role_expectations and actual_work:
            return (
                "[role/supporting] "
                f"기대치 '{role_expectations[0]}' 와 실제 업무 '{actual_work[0]}' 가 같은 문제를 가리켜요."
            )

        confirmed = self._string_list(stack_reality.get("confirmed"))
        if role_expectations and confirmed:
            return (
                "[role/supporting] "
                f"역할 기대치 '{role_expectations[0]}' 를 뒷받침하는 스택 단서로 {confirmed[0]} 이 확인돼요."
            )

        return ""

    def _growth_summary(self, company_report: AnalysisReport | None) -> str:
        if company_report is None:
            return ""

        source_data: dict[str, dict[str, object]] = {}
        for result in company_report.source_results:
            source_data.setdefault(result.source_name, {}).update(result.data)

        summary = cast(dict[str, object], summarize_growth_reality(source_data))
        verified_facts = self._mapping_dict(summary.get("verified_facts"))
        growth_reality = self._mapping_dict(verified_facts.get("growth_reality"))
        if not growth_reality:
            return ""

        rate = growth_reality.get("revenue_growth_rate")
        direction = self._growth_direction_label(str(growth_reality.get("revenue_growth_direction", "flat")))
        interpretations = self._string_list(summary.get("interpretation"))
        interpretation = ""
        if interpretations:
            interpretation = interpretations[0]
        trust_label = self._trust_label_for_data_key(company_report, "growth_reality")

        rate_label = "매출 추세는 확인됐어요"
        if isinstance(rate, (int, float)):
            rate_label = f"매출 성장률 {rate:.1f}%"

        line = f"[growth/{trust_label}] {rate_label} ({direction})"
        if interpretation:
            line += f" — {interpretation}"
        return line

    def _compensation_summary(
        self,
        company_report: AnalysisReport | None,
        war_room: Mapping[str, object],
    ) -> str:
        if company_report is None:
            return ""

        summary = self._mapping_dict(war_room.get("compensation_growth_reality"))
        if not summary:
            return ""

        trust_label = self._trust_label_for_data_key(
            company_report,
            "compensation_growth_reality",
        )
        headcount = summary.get("headcount_total")
        salary_data_available = summary.get("salary_data_available")
        tenure = summary.get("avg_tenure_years")

        parts: list[str] = []
        if isinstance(headcount, (int, float)) and headcount > 0:
            parts.append(f"추정 인원 {int(headcount):,}명")
        if salary_data_available is True:
            parts.append("급여 데이터 확인됨")
        else:
            parts.append("급여 데이터는 아직 unknown")
        if isinstance(tenure, (int, float)) and tenure > 0:
            parts.append(f"평균 근속 최대 {tenure:.1f}년")

        return f"[compensation/{trust_label}] " + ", ".join(parts)

    def _org_health_bucket(
        self,
        company_report: AnalysisReport | None,
        war_room: Mapping[str, object],
    ) -> dict[str, object]:
        if company_report is not None and company_report.source_results:
            bucket = cast(
                dict[str, object],
                DataReviewer()
                .review(company_report.source_results)
                .intelligence_layer.get(
                    "org_health",
                    {},
                ),
            )
            if bucket and any(bucket.values()):
                return bucket

        org_health = self._mapping_dict(war_room.get("org_health"))
        if not org_health:
            return {}

        return {
            "state": org_health.get("state", "unknown"),
            "verified_facts": [
                {"summary": item, "trust_label": "verified"} for item in self._string_list(org_health.get("verified"))
            ],
            "supporting_signals": [
                {"summary": item, "trust_label": "supporting"}
                for item in self._string_list(org_health.get("supporting"))
            ],
            "contradictions": [],
            "unknowns": [] if org_health.get("state") != "unknown" else ["org_health_unknown"],
        }

    def _append_org_health_guidance(
        self,
        *,
        sections: GroundedStrategySections,
        org_health_bucket: Mapping[str, object],
    ) -> None:
        if not org_health_bucket:
            return

        state = str(org_health_bucket.get("state", "unknown"))
        verified_facts = self._mapping_items(org_health_bucket.get("verified_facts"))
        supporting_signals = self._mapping_items(org_health_bucket.get("supporting_signals"))
        contradictions = self._mapping_items(org_health_bucket.get("contradictions"))
        unknowns = self._string_list(org_health_bucket.get("unknowns"))

        if state == "verified" and verified_facts:
            first_fact = verified_facts[0]
            summary = str(first_fact.get("summary", "")).strip()
            self._append_unique(
                sections.why_role_matters,
                f"[org_health/verified] {summary}",
            )
        elif state == "contradictory":
            detail = "상충 신호가 함께 보여요."
            if contradictions:
                claim_key = str(contradictions[0].get("claim_key", "org_health"))
                statuses = ", ".join(self._string_list(contradictions[0].get("statuses")))
                if statuses:
                    detail = f"{claim_key} 기준으로 {statuses} 신호가 함께 보여요."
            self._append_unique(
                sections.why_to_hesitate,
                f"[org_health/contradictory] {detail}",
            )
            self._append_unique(
                sections.verify_next,
                "needs verification — org_health: contradictory_evidence",
            )
        elif state in {"supporting", "unknown"} and supporting_signals:
            first_signal = supporting_signals[0]
            summary = str(first_signal.get("summary", "")).strip()
            self._append_unique(
                sections.why_to_hesitate,
                f"[org_health/supporting-only] {summary}",
            )

        for item in unknowns[:2]:
            self._append_unique(
                sections.verify_next,
                f"needs verification — org_health: {item}",
            )

    @staticmethod
    def _string_list(value: object) -> list[str]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @staticmethod
    def _mapping_dict(value: object) -> dict[str, object]:
        if not isinstance(value, Mapping):
            return {}
        return {str(key): item for key, item in value.items()}

    @classmethod
    def _mapping_items(cls, value: object) -> list[dict[str, object]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return []
        return [cls._mapping_dict(item) for item in value if cls._mapping_dict(item)]

    @staticmethod
    def _growth_direction_label(direction: str) -> str:
        return {
            "growing": "성장",
            "shrinking": "감소",
            "flat": "보합",
        }.get(direction, direction or "보합")

    @staticmethod
    def _trust_label_for_data_key(
        company_report: AnalysisReport,
        data_key: str,
    ) -> str:
        for result in company_report.source_results:
            if data_key in result.data:
                return result.trust_label
        return "unknown"

    def _get_company_stack(self, company_key: str) -> list[str]:
        """Return tech stack for a known company.

        Lookup order: CompanyDB (dynamic JSON) → hardcoded fallback dict.
        """
        db_stack = get_default_db().get_tech_stack(company_key)
        if db_stack:
            return db_stack
        return _COMPANY_TECH_STACK.get(company_key, [])

    def _compute_gaps(self, company_stack: list[str], user_skills: set[str]) -> list[SkillGap]:
        """Find skills in company stack not covered by user."""
        gaps: list[SkillGap] = []
        # First half of stack = core (required), rest = preferred
        core_cutoff = max(1, len(company_stack) // 2)

        for i, tech in enumerate(company_stack):
            tech_norm = normalize_tech(tech)
            if tech_norm in user_skills or tech in user_skills:
                continue

            importance = "required" if i < core_cutoff else "preferred"
            category = get_category(tech_norm) or "General"
            suggestion = _LEARNING_SUGGESTIONS.get(tech_norm, f"{tech} 공식 문서 학습")

            gaps.append(
                SkillGap(
                    skill=tech,
                    category=category,
                    importance=importance,
                    learning_suggestion=suggestion,
                )
            )
        return gaps

    def _compute_fit_score(
        self,
        profile: CareerProfile,
        company_stack: list[str],
        user_skills: set[str],
        gaps: list[SkillGap],
    ) -> float:
        """Compute 0-100 fit score.

        Weights:
        - Skill match: 50%
        - Experience seniority: 30%
        - Role alignment: 20%
        """
        # Skill match ratio
        if company_stack:
            matched = len(company_stack) - len(gaps)
            skill_ratio = matched / len(company_stack)
        else:
            skill_ratio = 0.5  # unknown company — neutral

        # Experience component
        seniority = classify_experience(profile.years_of_experience)
        exp_score = {
            "junior": 0.6,
            "mid": 0.85,
            "senior": 1.0,
        }.get(seniority.name, 0.7)

        # Role alignment
        role_score = self._compute_role_alignment(profile)

        raw = (skill_ratio * 0.5 + exp_score * 0.3 + role_score * 0.2) * 100
        return round(min(raw, 100.0), 1)

    def _compute_role_alignment(self, profile: CareerProfile) -> float:
        """0-1 score for how well current role aligns with target role."""
        if not profile.current_role or not profile.target_role:
            return 0.7  # no data — neutral

        current = profile.current_role.lower()
        target = profile.target_role.lower()

        # Same role family
        _ROLE_FAMILIES = [
            {"backend", "백엔드", "server", "서버", "be"},
            {"frontend", "프론트", "fe", "ui"},
            {"fullstack", "풀스택", "full-stack"},
            {"data", "데이터", "analytics", "analyst"},
            {"ml", "machine learning", "ai", "머신러닝"},
            {"devops", "sre", "infra", "인프라", "platform"},
            {"pm", "product manager", "기획", "po", "product owner"},
            {"mobile", "android", "ios", "앱"},
            {"security", "보안"},
        ]

        for family in _ROLE_FAMILIES:
            current_match = any(k in current for k in family)
            target_match = any(k in target for k in family)
            if current_match and target_match:
                return 1.0

        # Partial match (e.g. backend → fullstack)
        for family in _ROLE_FAMILIES:
            if any(k in current for k in family) or any(k in target for k in family):
                return 0.6

        return 0.4  # unrelated roles

    def _build_approach_strategy(
        self,
        profile: CareerProfile,
        fit_score: float,
        gaps: list[SkillGap],
    ) -> str:
        """Generate a textual approach strategy."""
        company = profile.target_company
        required_gaps = [g for g in gaps if g.importance == "required"]

        if fit_score >= 75:
            opening = f"{company}에 대한 적합도가 높아요 (점수: {fit_score:.0f}). 바로 지원을 권장해요."
        elif fit_score >= 50:
            opening = f"{company} 지원에 준비가 필요해요 (점수: {fit_score:.0f}). 핵심 갭을 보완하면 경쟁력이 높아져요."
        else:
            opening = (
                f"{company} 지원까지 추가 준비가 필요해요 (점수: {fit_score:.0f}). "
                "갭을 채운 뒤 6-12개월 내 재도전을 권장해요."
            )

        if profile.current_company:
            transition = (
                f"\n\n현재 {profile.current_company} 경험을 {company}에서 활용할 수 있는 "
                "공통점을 어필하세요. 도메인 전환 시에는 기술 스택 연속성을 강조하세요."
            )
        else:
            transition = ""

        # 직무 전환(인접 역할 이동) 감지 및 브리지 전략
        role_transition = ""
        if profile.current_role and profile.target_role:
            curr = profile.current_role.lower()
            tgt = profile.target_role.lower()
            if curr != tgt:
                role_transition = (
                    f"\n\n인접 역할 전환 ({profile.current_role} → {profile.target_role}): "
                    f"브리지 스킬(두 역할에 공통으로 필요한 역량)을 중심으로 어필하세요. "
                    f"현재 역할에서 {profile.target_role} 업무를 일부 수행한 경험이 있다면 "
                    f"구체적 사례를 강조하세요."
                )

        if required_gaps:
            gap_names = ", ".join(g.skill for g in required_gaps[:3])
            gap_note = f"\n\n핵심 보완 사항: {gap_names}."
        else:
            gap_note = "\n\n기술 스택 커버리지가 우수해요. 경험의 깊이와 임팩트를 중심으로 어필하세요."

        return opening + transition + role_transition + gap_note

    def _build_resume_focus(self, profile: CareerProfile, company_key: str, user_skills: set[str]) -> list[str]:
        """Return list of resume emphasis points."""
        company_stack = self._get_company_stack(company_key)
        matched_stack = [s for s in company_stack if normalize_tech(s) in user_skills or s in user_skills]

        focus = []

        if matched_stack:
            focus.append(
                f"보유 기술 중 {', '.join(matched_stack[:4])}를 사용한 실제 임팩트 수치 기재 "
                "(예: 처리량 N배 향상, 응답 시간 X% 단축)"
            )

        seniority = classify_experience(profile.years_of_experience)
        if seniority.name == "senior":
            focus.append("팀 리드 경험, 아키텍처 의사결정, 멘토링 사례 강조")
        elif seniority.name == "mid":
            focus.append("주도적으로 완성한 프로젝트와 기술적 문제 해결 사례 강조")
        else:
            focus.append("학습 속도와 성장 가능성, 사이드 프로젝트·오픈소스 기여 강조")

        if profile.current_company:
            focus.append(f"{profile.current_company} 재직 중 달성한 정량적 성과 (MAU, 거래액, 성능 지표 등)")

        focus.append(f"{profile.target_company} 제품/서비스에 대한 이해와 개선 아이디어 언급")
        focus.append("협업·커뮤니케이션 능력을 보여주는 크로스팀 프로젝트 사례")

        return focus

    def _build_interview_prep(
        self,
        profile: CareerProfile,
        company_key: str,
        gaps: list[SkillGap],
    ) -> list[str]:
        """Return list of interview preparation points."""
        prep = [
            f"{profile.target_company}의 핵심 제품과 비즈니스 모델 숙지 "
            "(서비스 직접 사용, 공식 블로그·테크블로그 정독)",
        ]

        seniority = classify_experience(profile.years_of_experience)
        if seniority.name == "senior":
            prep.append("시스템 디자인 인터뷰 집중 준비: 대규모 트래픽 처리, 마이크로서비스 설계")
        elif seniority.name == "mid":
            prep.append("코딩 인터뷰: LeetCode Medium 30문제 + 자료구조/알고리즘 복습")
        else:
            prep.append("코딩 인터뷰 기초: LeetCode Easy~Medium, 자료구조/알고리즘 핵심 문제")

        company_stack = self._get_company_stack(company_key)
        if company_stack:
            core_tech = company_stack[:3]
            prep.append(f"기술 심층 질문 대비: {', '.join(core_tech)} 동작 원리와 트레이드오프 설명 연습")

        prep.append("STAR 기법으로 과거 경험 3-5개 스토리 준비 (상황-과제-행동-결과)")

        if gaps:
            gap_skills = [g.skill for g in gaps if g.importance == "required"][:2]
            if gap_skills:
                prep.append(
                    f"갭 스킬 질문 대비: {', '.join(gap_skills)} 관련 질문 시 "
                    "학습 계획과 유사 경험으로 대응하는 답변 준비"
                )

        prep.append("역질문 준비: 팀 문화, 기술 부채 현황, 온보딩 프로세스 등")

        return prep

    def _recommend_timeline(self, gaps: list[SkillGap], fit_score: float) -> str:
        """Recommend preparation timeline."""
        required_gaps = [g for g in gaps if g.importance == "required"]
        n_gaps = len(required_gaps)

        if fit_score >= 75 and n_gaps == 0:
            return "즉시 지원 가능 — 지원서 준비에 1-2주 투자 권장"
        if fit_score >= 60 and n_gaps <= 1:
            return "1-2개월 — 핵심 갭 1개 보완 후 지원 (매주 10-15시간 학습 기준)"
        if fit_score >= 45 and n_gaps <= 3:
            return "3-4개월 — 필수 기술 갭 보완 + 사이드 프로젝트 완성 후 지원"
        return "6-12개월 — 기술 스택 재정비 + 포트폴리오 강화 후 도전 권장"

    def _suggest_career_path(self, profile: CareerProfile) -> str:
        """Suggest a career development path."""
        role = profile.target_role.lower() if profile.target_role else ""

        _ROLE_PATH_MAP = [
            ({"backend", "백엔드", "server", "서버", "be"}, "backend"),
            ({"frontend", "프론트", "fe", "ui"}, "frontend"),
            ({"fullstack", "풀스택"}, "fullstack"),
            ({"data", "데이터", "analytics", "analyst"}, "data"),
            ({"ml", "machine learning", "ai", "머신러닝"}, "ml"),
            ({"devops", "sre", "infra", "platform"}, "devops"),
            ({"pm", "product", "기획", "po"}, "pm"),
            ({"mobile", "android", "ios"}, "mobile"),
            ({"security", "보안"}, "security"),
        ]

        for keywords, path_key in _ROLE_PATH_MAP:
            if any(k in role for k in keywords):
                return _CAREER_PATHS[path_key]

        return (
            f"{profile.target_company} 입사 → 시니어 → Lead → "
            "Manager 또는 Principal Engineer (전문성에 따라 IC / EM 트랙 선택)"
        )

    def _assess_risk(
        self,
        profile: CareerProfile,
        fit_score: float,
        gaps: list[SkillGap],
    ) -> str:
        """Assess transition risk level and provide guidance."""
        required_gaps = [g for g in gaps if g.importance == "required"]

        if fit_score >= 75 and len(required_gaps) == 0:
            level = "낮음"
            detail = "기술 적합도가 높아 바로 지원 준비를 진행해도 돼요. 협상 시 연봉 하한을 미리 설정하세요."
        elif fit_score >= 55:
            level = "중간"
            detail = (
                "일부 갭이 있지만 충분히 극복 가능한 수준이에요. "
                "이직 전 현재 직장 내 유사 기술 적용 경험을 쌓으면 리스크가 줄어요."
            )
        else:
            level = "높음"
            detail = (
                "지금 기준으로는 갭과 증거 공백이 커 보여요. "
                "대안 기업에 먼저 지원해 면접 경험을 쌓거나, "
                "갭 보완 후 재도전을 권장해요."
            )
            # 직무 전환(비전통적 경로) 시 대안 포지션 + 단계적 이동 경로 제시
            if profile.current_role and profile.target_role:
                curr = profile.current_role.lower()
                tgt = profile.target_role.lower()
                if curr != tgt:
                    detail += (
                        f"\n\n대안 포지션: {profile.current_role}의 경험을 살릴 수 있는 "
                        f"하이브리드 역할(예: Technical {profile.target_role}, "
                        f"{profile.current_role} 출신 {profile.target_role})을 먼저 고려하세요. "
                        f"단계적 이동 경로를 통해 목표 직무에 점진적으로 접근하는 것이 안전해요."
                    )

        if profile.current_company:
            detail += f" 현재 {profile.current_company}를 재직하며 준비하는 것이 유리해요."

        return f"리스크 수준: {level}\n{detail}"
