"""Korean cover letter (자기소개서) coach engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from hirekit.core.scoring import score_to_grade
from hirekit.llm.base import BaseLLM, NoLLM  # noqa: F401 (NoLLM used as default)

# ---------------------------------------------------------------------------
# Section templates (rule-based / NoLLM mode)
# ---------------------------------------------------------------------------

_SECTION_TEMPLATES: dict[str, dict[str, str]] = {
    "growth": {
        "title": "성장과정",
        "prompt_hint": (
            "어린 시절부터 지금까지 본인을 성장시킨 경험을 중심으로 작성하세요. "
            "가정환경, 교육환경보다 본인의 가치관 형성에 영향을 준 사건/경험에 집중하세요."
        ),
        "template": (
            "저는 [{keyword}]라는 가치관을 바탕으로 성장해 왔습니다. "
            "[구체적 경험 1]을 통해 [배운 점]을 깨달았으며, "
            "[구체적 경험 2]를 거치며 [역량/태도]를 키웠습니다. "
            "이러한 성장 배경이 [{company}]에서 [{position}]으로 기여할 토대가 될 것입니다."
        ),
    },
    "motivation": {
        "title": "지원동기",
        "prompt_hint": (
            "기업의 사업 방향, 최근 전략, 제품/서비스에 대한 구체적 이해를 드러내세요. "
            "단순 '좋아서'가 아닌, 나의 커리어 목표와 기업의 방향이 만나는 지점을 서술하세요."
        ),
        "template": (
            "[{company}]를 지원하게 된 이유는 [{company_strength}]에 있습니다. "
            "[{company_recent_move}]를 접하며 이 회사가 나아가는 방향이 "
            "제가 추구하는 [{career_goal}]와 일치함을 확인했습니다. "
            "특히 [{position}] 직무를 통해 [{contribution}]으로 기여하고 싶습니다."
        ),
    },
    "competency": {
        "title": "직무역량 및 입사 후 포부",
        "prompt_hint": (
            "직무와 직접 연결되는 경험, 프로젝트, 수치 결과를 중심으로 서술하세요. "
            "입사 후 1년/3년/5년 포부를 구체적으로 제시하세요."
        ),
        "template": (
            "저의 핵심 직무역량은 [{top_skill}]입니다. "
            "[프로젝트/경험]에서 [구체적 행동]을 통해 [정량적 성과]를 달성했습니다. "
            "입사 후에는 [{short_term_goal}]을 먼저 달성하고, "
            "장기적으로는 [{long_term_goal}]을 목표로 삼겠습니다."
        ),
    },
    "personality": {
        "title": "성격의 장단점",
        "prompt_hint": (
            "장점은 직무와 연결된 구체적 사례로, "
            "단점은 인지하고 개선하는 노력까지 포함하여 서술하세요."
        ),
        "template": (
            "저의 강점은 [{strength}]입니다. "
            "[구체적 상황]에서 이 강점을 발휘해 [결과]를 이끌어냈습니다. "
            "반면 [{weakness}]는 개선 중인 부분입니다. "
            "[개선 노력/방법]을 통해 이를 극복하고 있으며, "
            "최근 [개선 사례]로 성장하고 있습니다."
        ),
    },
}

# Company insight extraction keywords
_COMPANY_INSIGHT_KEYS = [
    "사업", "전략", "비전", "미션", "서비스", "제품", "성장", "투자",
    "기술", "혁신", "글로벌", "플랫폼", "매출", "이용자",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CoverLetterSection:
    """A single section of a Korean cover letter."""

    key: str          # e.g. "growth", "motivation", "competency", "personality"
    title: str        # e.g. "성장과정"
    content: str = ""
    word_count: int = 0
    score: float = 0.0  # 0-100
    feedback: list[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        return score_to_grade(self.score)

    def to_markdown(self) -> str:
        lines = [
            f"### {self.title}",
            "",
            self.content,
            "",
            f"*글자 수: {self.word_count}자 | 점수: {self.score:.0f}/100 (Grade {self.grade})*",
        ]
        if self.feedback:
            lines.append("\n**피드백:**")
            for fb in self.feedback:
                lines.append(f"- {fb}")
        return "\n".join(lines)


@dataclass
class CoverLetterDraft:
    """Full Korean cover letter with all four sections."""

    company: str
    position: str = ""

    sections: list[CoverLetterSection] = field(default_factory=list)
    overall_score: float = 0.0
    strategy_notes: list[str] = field(default_factory=list)

    # Company-specific insights injected into motivation
    company_insights: dict[str, str] = field(default_factory=dict)

    @property
    def grade(self) -> str:
        return score_to_grade(self.overall_score)

    def to_markdown(self) -> str:
        lines = [
            f"# 자기소개서: {self.company}",
            f"**포지션:** {self.position or '미지정'}",
            f"**종합 점수:** {self.overall_score:.0f}/100 (Grade {self.grade})",
            "",
            "---",
            "",
        ]

        if self.company_insights:
            lines.append("## 기업 분석 인사이트 (지원동기 반영)")
            for key, val in self.company_insights.items():
                lines.append(f"- **{key}**: {val}")
            lines.append("")
            lines.append("---")
            lines.append("")

        for section in self.sections:
            lines.append(section.to_markdown())
            lines.append("")
            lines.append("---")
            lines.append("")

        if self.strategy_notes:
            lines.append("## 전략 메모")
            for note in self.strategy_notes:
                lines.append(f"- {note}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class CoverLetterCoach:
    """Korean 자기소개서 coach — rule-based + optional LLM enhancement."""

    # Character count targets per section (Korean standard: 500–1000자)
    _TARGET_CHARS = 700

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or NoLLM()

    def draft(
        self,
        company: str,
        position: str = "",
        profile: dict[str, Any] | None = None,
        company_report: dict[str, Any] | None = None,
    ) -> CoverLetterDraft:
        """Generate a full 자기소개서 draft.

        Args:
            company: Target company name (e.g., "카카오").
            position: Target role (e.g., "PM", "백엔드 엔지니어").
            profile: User career profile dict (from profile.yaml).
            company_report: Company analysis dict (from AnalysisReport.to_dict()).
        """
        draft = CoverLetterDraft(company=company, position=position)

        # 1. Extract company insights for motivation section
        draft.company_insights = self._extract_company_insights(
            company, company_report
        )

        # 2. Build each section
        for key in ("growth", "motivation", "competency", "personality"):
            section = self._build_section(
                key=key,
                company=company,
                position=position,
                profile=profile,
                company_insights=draft.company_insights,
            )
            draft.sections.append(section)

        # 3. LLM enhancement
        if self.llm.is_available():
            self._enhance_with_llm(draft, profile)
        else:
            self._rule_based_feedback(draft)

        # 4. Calculate overall score
        draft.overall_score = self._calculate_overall_score(draft)

        return draft

    # ------------------------------------------------------------------
    # Company insight extraction
    # ------------------------------------------------------------------

    def _extract_company_insights(
        self,
        company: str,
        report: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Extract key company insights to inject into motivation section."""
        insights: dict[str, str] = {}

        if not report:
            insights["기업명"] = company
            return insights

        # Pull from sections dict if present
        sections = report.get("sections", {})
        raw_texts: list[str] = []

        for section_data in sections.values():
            if isinstance(section_data, dict):
                for val in section_data.values():
                    if isinstance(val, str) and len(val) > 10:
                        raw_texts.append(val)
                    elif isinstance(val, list):
                        raw_texts.extend(
                            item for item in val if isinstance(item, str)
                        )

        combined = " ".join(raw_texts)

        # Extract key insight sentences containing insight keywords
        sentences = re.split(r"[.。\n]", combined)
        found: list[str] = []
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue
            if any(kw in sent for kw in _COMPANY_INSIGHT_KEYS):
                found.append(sent[:120])
            if len(found) >= 3:
                break

        if found:
            insights["핵심 사업"] = found[0]
            if len(found) > 1:
                insights["최근 전략"] = found[1]
            if len(found) > 2:
                insights["기술/혁신"] = found[2]
        else:
            insights["기업명"] = company

        return insights

    # ------------------------------------------------------------------
    # Section building (rule-based)
    # ------------------------------------------------------------------

    def _build_section(
        self,
        key: str,
        company: str,
        position: str,
        profile: dict[str, Any] | None,
        company_insights: dict[str, str],
    ) -> CoverLetterSection:
        """Build a single section using templates."""
        tmpl_data = _SECTION_TEMPLATES[key]
        section = CoverLetterSection(key=key, title=tmpl_data["title"])

        # Resolve substitution variables
        vars_: dict[str, str] = {
            "company": company,
            "position": position or "해당 직무",
        }

        if profile:
            skills = profile.get("skills", {})
            tech_skills = skills.get("technical", [])
            assets = profile.get("career_assets", [])

            vars_["top_skill"] = tech_skills[0] if tech_skills else "핵심 역량"
            vars_["keyword"] = (
                profile.get("values", ["성장과 도전"])[0]
                if profile.get("values")
                else "성장과 도전"
            )
            vars_["career_goal"] = profile.get("career_goal", "커리어 목표")
            vars_["short_term_goal"] = profile.get(
                "short_term_goal", "빠른 온보딩 및 성과 창출"
            )
            vars_["long_term_goal"] = profile.get(
                "long_term_goal", "핵심 인재로 성장"
            )
            vars_["strength"] = (
                skills.get("soft", ["문제 해결력"])[0]
                if skills.get("soft")
                else "문제 해결력"
            )
            vars_["weakness"] = profile.get("weakness", "완벽주의적 성향")
            vars_["contribution"] = (
                assets[0].get("asset", "성과") if assets else "직무 성과"
            )
        else:
            vars_["top_skill"] = "핵심 역량"
            vars_["keyword"] = "성장과 도전"
            vars_["career_goal"] = "커리어 목표"
            vars_["short_term_goal"] = "빠른 온보딩 및 성과 창출"
            vars_["long_term_goal"] = "핵심 인재로 성장"
            vars_["strength"] = "문제 해결력"
            vars_["weakness"] = "완벽주의적 성향"
            vars_["contribution"] = "직무 성과"

        # Inject company insights into motivation section
        if key == "motivation":
            insight_vals = list(company_insights.values())
            vars_["company_strength"] = insight_vals[0] if insight_vals else company
            vars_["company_recent_move"] = (
                insight_vals[1] if len(insight_vals) > 1 else f"{company}의 최근 행보"
            )

        # Apply template substitution
        content = tmpl_data["template"]
        for var_key, var_val in vars_.items():
            content = content.replace(f"[{{{var_key}}}]", var_val)

        section.content = content
        section.word_count = len(content)
        return section

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _rule_based_feedback(self, draft: CoverLetterDraft) -> None:
        """Apply rule-based scoring and feedback to all sections."""
        for section in draft.sections:
            score, feedback = self._score_section(section, draft.company)
            section.score = score
            section.feedback = feedback

        # Generic strategy notes
        draft.strategy_notes = [
            f"{draft.company} 최신 뉴스·공시를 읽고 지원동기에 구체적 수치를 추가하세요.",
            "각 섹션 글자 수를 700자 내외로 맞추고, 수치 결과(%, 건수 등)를 포함하세요.",
            "STAR 구조(상황-과제-행동-결과)로 경험을 재구성하면 신뢰도가 높아집니다.",
            "맞춤법 검사기(한국어 맞춤법 검사기)로 최종 검토하세요.",
            "제출 전 해당 포지션 JD와 다시 대조하여 키워드 일치도를 확인하세요.",
        ]

    def _score_section(
        self, section: CoverLetterSection, company: str
    ) -> tuple[float, list[str]]:
        """Score a section with rule-based checks."""
        score = 50.0
        feedback: list[str] = []

        content = section.content
        char_count = len(content)

        # Length check
        if char_count >= self._TARGET_CHARS:
            score += 15
        elif char_count >= 400:
            score += 8
            feedback.append(f"글자 수({char_count}자)를 700자 이상으로 늘리세요.")
        else:
            feedback.append(f"글자 수({char_count}자)가 너무 짧습니다. 구체적 경험을 추가하세요.")

        # Company name mention
        if company in content:
            score += 10
        else:
            feedback.append(f"'{company}'를 직접 언급하여 맞춤형 자소서임을 보여주세요.")

        # Quantitative evidence
        if re.search(r"\d+[%건명억원회년개월]|\d+\s*[%]", content):
            score += 10
        else:
            feedback.append("수치(%, 건수, 금액 등)를 포함한 구체적 성과를 추가하세요.")

        # Template placeholder not substituted
        unfilled = re.findall(r"\[[가-힣a-zA-Z\s]+\]", content)
        if unfilled:
            score -= 15
            feedback.append(
                f"다음 항목을 실제 내용으로 채워주세요: {', '.join(unfilled[:3])}"
            )

        # Position mention
        if section.key == "motivation" and not content.strip():
            score -= 10

        return min(100.0, max(0.0, score)), feedback

    def _calculate_overall_score(self, draft: CoverLetterDraft) -> float:
        """Weighted average of section scores."""
        weights = {
            "growth": 0.20,
            "motivation": 0.35,
            "competency": 0.30,
            "personality": 0.15,
        }
        total = 0.0
        for section in draft.sections:
            total += section.score * weights.get(section.key, 0.25)
        return round(total, 1)

    # ------------------------------------------------------------------
    # LLM enhancement
    # ------------------------------------------------------------------

    def _enhance_with_llm(
        self,
        draft: CoverLetterDraft,
        profile: dict[str, Any] | None,
    ) -> None:
        """Use LLM to rewrite sections and generate tailored feedback."""
        profile_ctx = self._build_profile_context(profile)
        insight_ctx = "\n".join(
            f"- {k}: {v}" for k, v in draft.company_insights.items()
        )

        for section in draft.sections:
            prompt = (
                f"회사: {draft.company}\n"
                f"포지션: {draft.position or '미지정'}\n\n"
                f"기업 인사이트:\n{insight_ctx}\n\n"
                f"지원자 프로필:\n{profile_ctx}\n\n"
                f"자기소개서 항목: [{section.title}]\n"
                f"현재 초안:\n{section.content}\n\n"
                "위 초안을 바탕으로 다음 조건에 맞게 개선된 자기소개서를 작성하세요:\n"
                "1. 700자 내외의 한국어 자기소개서 본문 (구체적 경험 + 수치 포함)\n"
                "2. 기업의 특성과 포지션에 맞게 맞춤화\n"
                "3. STAR 구조 활용\n"
                "4. 피드백 3가지 (개선할 점)\n\n"
                "형식:\n"
                "본문:\n[작성된 자기소개서]\n\n"
                "피드백:\n- [피드백1]\n- [피드백2]\n- [피드백3]"
            )

            resp = self.llm.generate(prompt=prompt, temperature=0.4)
            if resp.text:
                self._parse_llm_section(section, resp.text, draft.company)

        # Overall strategy from LLM
        pos = draft.position or "미지정"
        strategy_prompt = (
            f"{draft.company} [{pos}] 포지션 자기소개서 전략을 3가지 bullet로 제시하세요."
        )
        resp = self.llm.generate(prompt=strategy_prompt, temperature=0.3)
        if resp.text:
            items = re.findall(r"[-•]\s*(.+)", resp.text)
            draft.strategy_notes = items[:5] if items else [resp.text.strip()]

    def _parse_llm_section(
        self,
        section: CoverLetterSection,
        text: str,
        company: str,
    ) -> None:
        """Parse LLM response into section content and feedback."""
        body_match = re.search(r"본문[:：]\s*\n?([\s\S]+?)(?:\n\n피드백|$)", text)
        feedback_matches = re.findall(r"[-•]\s*(.+)", text)

        if body_match:
            section.content = body_match.group(1).strip()
            section.word_count = len(section.content)

        # Feedback items from LLM output
        if feedback_matches:
            section.feedback = feedback_matches[:3]

        # Re-score with rule-based after LLM content
        score, extra_fb = self._score_section(section, company)
        section.score = score
        if extra_fb and not section.feedback:
            section.feedback = extra_fb

    def _build_profile_context(self, profile: dict[str, Any] | None) -> str:
        """Build a concise profile context string for LLM prompts."""
        if not profile:
            return "프로필 정보 없음"

        skills = profile.get("skills", {})
        assets = profile.get("career_assets", [])
        lines = [
            f"경력: {profile.get('years_of_experience', 'N/A')}년",
            f"기술: {', '.join(skills.get('technical', [])[:5])}",
            f"도메인: {', '.join(skills.get('domain', [])[:3])}",
            f"소프트 스킬: {', '.join(skills.get('soft', [])[:3])}",
            f"핵심 자산: {', '.join(a['asset'] for a in assets[:4])}",
            f"커리어 목표: {profile.get('career_goal', '')}",
        ]
        return "\n".join(lines)
