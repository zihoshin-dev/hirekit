"""Interview preparation engine — generate questions and coaching."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.interview_questions import (
    AnswerGuide,
    InterviewQuestion,
    QuestionCategory,
    QUESTION_BANK,
    build_answer_guide,
    get_questions_by_category,
    get_star_questions,
    get_tech_questions_for_stack,
    get_top_frequency_questions,
)
from hirekit.llm.base import BaseLLM, NoLLM


# ---------------------------------------------------------------------------
# Known company-culture mappings for rule-based culture-fit questions
# ---------------------------------------------------------------------------

_COMPANY_CULTURE_HINTS: dict[str, dict[str, Any]] = {
    "카카오": {
        "keywords": ["AI", "플랫폼", "톡비즈", "수평 문화"],
        "culture_category": QuestionCategory.LARGE_CORP,
        "is_startup": False,
    },
    "네이버": {
        "keywords": ["검색", "클로바", "AI", "글로벌"],
        "culture_category": QuestionCategory.LARGE_CORP,
        "is_startup": False,
    },
    "토스": {
        "keywords": ["핀테크", "사용자 경험", "데이터", "성장"],
        "culture_category": QuestionCategory.STARTUP,
        "is_startup": True,
    },
    "쿠팡": {
        "keywords": ["이커머스", "물류", "데이터", "고객 집착"],
        "culture_category": QuestionCategory.LARGE_CORP,
        "is_startup": False,
    },
    "당근": {
        "keywords": ["로컬", "커뮤니티", "중고거래", "연결"],
        "culture_category": QuestionCategory.STARTUP,
        "is_startup": True,
    },
    "라인": {
        "keywords": ["메신저", "글로벌", "일본", "플랫폼"],
        "culture_category": QuestionCategory.LARGE_CORP,
        "is_startup": False,
    },
    "크래프톤": {
        "keywords": ["게임", "글로벌", "배틀그라운드", "창의성"],
        "culture_category": QuestionCategory.LARGE_CORP,
        "is_startup": False,
    },
    "무신사": {
        "keywords": ["패션", "커머스", "MZ세대", "브랜드"],
        "culture_category": QuestionCategory.STARTUP,
        "is_startup": True,
    },
    "뱅크샐러드": {
        "keywords": ["핀테크", "데이터", "마이데이터"],
        "culture_category": QuestionCategory.STARTUP,
        "is_startup": True,
    },
    "리멤버": {
        "keywords": ["B2B", "명함", "커리어", "네트워킹"],
        "culture_category": QuestionCategory.STARTUP,
        "is_startup": True,
    },
}

# Tech stack → question category mapping
_STACK_CATEGORY_MAP: dict[str, QuestionCategory] = {
    "react": QuestionCategory.FRONTEND,
    "vue": QuestionCategory.FRONTEND,
    "angular": QuestionCategory.FRONTEND,
    "next": QuestionCategory.FRONTEND,
    "typescript": QuestionCategory.FRONTEND,
    "css": QuestionCategory.FRONTEND,
    "node": QuestionCategory.BACKEND,
    "django": QuestionCategory.BACKEND,
    "spring": QuestionCategory.BACKEND,
    "fastapi": QuestionCategory.BACKEND,
    "postgresql": QuestionCategory.BACKEND,
    "mysql": QuestionCategory.BACKEND,
    "redis": QuestionCategory.BACKEND,
    "kafka": QuestionCategory.BACKEND,
    "kubernetes": QuestionCategory.DEVOPS,
    "docker": QuestionCategory.DEVOPS,
    "terraform": QuestionCategory.DEVOPS,
    "aws": QuestionCategory.DEVOPS,
    "gcp": QuestionCategory.DEVOPS,
    "spark": QuestionCategory.DATA,
    "airflow": QuestionCategory.DATA,
    "dbt": QuestionCategory.DATA,
    "python": QuestionCategory.DATA,
    "swift": QuestionCategory.MOBILE,
    "kotlin": QuestionCategory.MOBILE,
    "flutter": QuestionCategory.MOBILE,
    "android": QuestionCategory.MOBILE,
    "ios": QuestionCategory.MOBILE,
}

# Role keyword → recommended categories
_ROLE_CATEGORY_MAP: dict[str, list[QuestionCategory]] = {
    "frontend": [QuestionCategory.FRONTEND, QuestionCategory.TECH_COMMON],
    "프론트엔드": [QuestionCategory.FRONTEND, QuestionCategory.TECH_COMMON],
    "backend": [QuestionCategory.BACKEND, QuestionCategory.TECH_COMMON],
    "백엔드": [QuestionCategory.BACKEND, QuestionCategory.TECH_COMMON],
    "fullstack": [QuestionCategory.FRONTEND, QuestionCategory.BACKEND, QuestionCategory.TECH_COMMON],
    "풀스택": [QuestionCategory.FRONTEND, QuestionCategory.BACKEND, QuestionCategory.TECH_COMMON],
    "devops": [QuestionCategory.DEVOPS, QuestionCategory.TECH_COMMON],
    "sre": [QuestionCategory.DEVOPS, QuestionCategory.TECH_COMMON],
    "data": [QuestionCategory.DATA, QuestionCategory.TECH_COMMON],
    "데이터": [QuestionCategory.DATA, QuestionCategory.TECH_COMMON],
    "ml": [QuestionCategory.DATA, QuestionCategory.TECH_COMMON],
    "mobile": [QuestionCategory.MOBILE, QuestionCategory.TECH_COMMON],
    "모바일": [QuestionCategory.MOBILE, QuestionCategory.TECH_COMMON],
    "ios": [QuestionCategory.MOBILE, QuestionCategory.TECH_COMMON],
    "android": [QuestionCategory.MOBILE, QuestionCategory.TECH_COMMON],
    "pm": [QuestionCategory.PERSONALITY, QuestionCategory.LEADERSHIP],
    "manager": [QuestionCategory.LEADERSHIP, QuestionCategory.TECH_COMMON],
    "lead": [QuestionCategory.LEADERSHIP, QuestionCategory.TECH_COMMON],
    "리드": [QuestionCategory.LEADERSHIP, QuestionCategory.TECH_COMMON],
}


@dataclass
class STARStory:
    """STAR format story for interview answers."""

    question: str = ""
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""

    def to_markdown(self) -> str:
        return (
            f"**Q: {self.question}**\n"
            f"- **Situation**: {self.situation}\n"
            f"- **Task**: {self.task}\n"
            f"- **Action**: {self.action}\n"
            f"- **Result**: {self.result}\n"
        )


@dataclass
class InterviewSession:
    """Structured interview session plan with time allocation and difficulty curve."""

    company: str
    position: str
    total_minutes: int = 60

    questions: list[InterviewQuestion] = field(default_factory=list)
    time_per_question: list[int] = field(default_factory=list)  # seconds per question
    difficulty_curve: list[int] = field(default_factory=list)   # difficulty at each index

    notes: str = ""

    def to_markdown(self) -> str:
        lines = [
            f"# 면접 시뮬레이션: {self.company} — {self.position}",
            f"**총 예상 시간:** {self.total_minutes}분",
            "",
            "| # | 카테고리 | 질문 | 시간(초) | 난이도 |",
            "|---|----------|------|----------|--------|",
        ]
        for i, q in enumerate(self.questions):
            t = self.time_per_question[i] if i < len(self.time_per_question) else 120
            d = "★" * q.difficulty + "☆" * (3 - q.difficulty)
            lines.append(f"| {i+1} | {q.category.value} | {q.question[:50]}... | {t}s | {d} |")

        if self.notes:
            lines.append(f"\n**메모:** {self.notes}")
        return "\n".join(lines)


@dataclass
class InterviewGuide:
    """Structured interview preparation guide."""

    company: str
    position: str = ""

    # Question categories
    common_questions: list[dict[str, str]] = field(default_factory=list)
    technical_questions: list[dict[str, str]] = field(default_factory=list)
    behavioral_questions: list[dict[str, str]] = field(default_factory=list)
    culture_fit_questions: list[dict[str, str]] = field(default_factory=list)
    reverse_questions: list[str] = field(default_factory=list)

    # Answer guides (rule-based)
    answer_guides: list[AnswerGuide] = field(default_factory=list)

    # STAR stories
    star_stories: list[STARStory] = field(default_factory=list)

    # Process info
    interview_process: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# Interview Prep: {self.company}",
            f"**Position:** {self.position}",
            "",
            "---",
        ]

        if self.interview_process:
            lines.append("\n## Interview Process")
            for i, step in enumerate(self.interview_process, 1):
                lines.append(f"{i}. {step}")

        lines.append("\n## Common Questions")
        for q in self.common_questions:
            lines.append(f"\n**Q: {q['question']}**")
            lines.append(f"- Answer Direction: {q.get('answer', '')}")

        if self.technical_questions:
            lines.append("\n## Technical / Role-Specific Questions")
            for q in self.technical_questions:
                lines.append(f"\n**Q: {q['question']}**")
                lines.append(f"- Answer Direction: {q.get('answer', '')}")

        if self.behavioral_questions:
            lines.append("\n## Behavioral Questions (STAR)")
            for q in self.behavioral_questions:
                lines.append(f"\n**Q: {q['question']}**")
                lines.append(f"- Answer Direction: {q.get('answer', '')}")

        if self.culture_fit_questions:
            lines.append("\n## Culture Fit Questions")
            for q in self.culture_fit_questions:
                lines.append(f"\n**Q: {q['question']}**")
                lines.append(f"- Answer Direction: {q.get('answer', '')}")

        if self.answer_guides:
            lines.append("\n## Answer Guides")
            for guide in self.answer_guides:
                lines.append(f"\n{guide.to_markdown()}")

        if self.star_stories:
            lines.append("\n## STAR Stories")
            for story in self.star_stories:
                lines.append(f"\n{story.to_markdown()}")

        if self.reverse_questions:
            lines.append("\n## Reverse Questions (show company knowledge)")
            for i, q in enumerate(self.reverse_questions, 1):
                lines.append(f"{i}. {q}")

        if self.tips:
            lines.append("\n## Tips")
            for tip in self.tips:
                lines.append(f"- {tip}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Default question templates (used in No-LLM mode)
# ---------------------------------------------------------------------------

DEFAULT_COMMON_QUESTIONS = [
    {
        "question": "Why do you want to join {company}?",
        "answer": "Connect your career goals with the company's mission and recent strategy.",
    },
    {
        "question": "Why this role specifically?",
        "answer": "Map your skills and experience to the role requirements.",
    },
    {
        "question": "Tell me about your biggest achievement.",
        "answer": "Use STAR format. Include quantitative results.",
    },
    {
        "question": "Where do you see yourself in 3-5 years?",
        "answer": "Align with the company's growth trajectory and your role's growth path.",
    },
    {
        "question": "Why are you leaving your current role?",
        "answer": "Focus on growth opportunities, not complaints. Be positive.",
    },
]

DEFAULT_REVERSE_QUESTIONS = [
    "What does success look like for this role in the first 6 months?",
    "How does the team approach product decisions?",
    "What's the biggest challenge the team is facing right now?",
    "How does {company} approach AI/technology in this domain?",
    "What's the team structure and who would I work with?",
]

# Company-data-driven reverse question templates
_COMPANY_REVERSE_TEMPLATES = [
    "최근 {company}가 {keyword} 분야에 집중하는 것을 보았는데, 이 팀은 어떤 방식으로 기여하나요?",
    "{company}의 {keyword} 전략에서 이 포지션이 어떤 역할을 담당하게 되나요?",
    "{keyword}와 관련해서 팀이 현재 풀고 있는 가장 어려운 문제는 무엇인가요?",
    "{company}에서 {keyword} 관련 기술 스택이나 방향성이 앞으로 어떻게 변화할 것으로 보시나요?",
]


def _detect_role_categories(position: str) -> list[QuestionCategory]:
    """Detect relevant question categories from position string."""
    pos_lower = position.lower()
    for keyword, categories in _ROLE_CATEGORY_MAP.items():
        if keyword in pos_lower:
            return categories
    # Default: general tech + personality
    return [QuestionCategory.TECH_COMMON, QuestionCategory.PERSONALITY]


def _detect_company_culture(company: str) -> dict[str, Any]:
    """Return culture hints for known companies."""
    for name, hints in _COMPANY_CULTURE_HINTS.items():
        if name in company:
            return hints
    return {"keywords": [], "culture_category": QuestionCategory.LARGE_CORP, "is_startup": False}


def _pick_questions(
    category: QuestionCategory,
    count: int,
    min_frequency: int = 3,
    seed: int | None = None,
) -> list[InterviewQuestion]:
    """Pick top-N questions from a category, sorted by frequency."""
    pool = [q for q in get_questions_by_category(category) if q.frequency >= min_frequency]
    pool.sort(key=lambda q: q.frequency, reverse=True)
    return pool[:count]


def _build_tech_questions_from_jd(
    jd_skills: list[str],
    position: str,
    count: int = 8,
) -> list[dict[str, str]]:
    """Build technical questions based on JD skills and position."""
    results: list[dict[str, str]] = []
    seen: set[str] = set()

    # Match by tech stack keywords
    if jd_skills:
        matched = get_tech_questions_for_stack(jd_skills)
        for q in matched[:count]:
            if q.question not in seen:
                seen.add(q.question)
                results.append({
                    "question": q.question,
                    "answer": " / ".join(q.answer_points[:3]),
                    "difficulty": str(q.difficulty),
                    "frequency": str(q.frequency),
                })

    # Fill remaining from role-based categories
    role_cats = _detect_role_categories(position)
    for cat in role_cats:
        if len(results) >= count:
            break
        for q in _pick_questions(cat, count):
            if q.question not in seen:
                seen.add(q.question)
                results.append({
                    "question": q.question,
                    "answer": " / ".join(q.answer_points[:3]),
                    "difficulty": str(q.difficulty),
                    "frequency": str(q.frequency),
                })
            if len(results) >= count:
                break

    return results[:count]


def _build_behavioral_questions(count: int = 5) -> list[dict[str, str]]:
    """Build STAR-based behavioral questions from the question bank."""
    star_qs = get_star_questions(QuestionCategory.PERSONALITY)
    # Also pull from general tech + leadership
    star_qs += get_star_questions(QuestionCategory.TECH_COMMON)
    star_qs += get_star_questions(QuestionCategory.LEADERSHIP)

    # Deduplicate and sort by frequency
    seen: set[str] = set()
    unique: list[InterviewQuestion] = []
    for q in sorted(star_qs, key=lambda x: x.frequency, reverse=True):
        if q.question not in seen:
            seen.add(q.question)
            unique.append(q)

    return [
        {
            "question": q.question,
            "answer": f"STAR 포맷 활용. 핵심: {' / '.join(q.answer_points[:2])}",
        }
        for q in unique[:count]
    ]


def _build_culture_fit_questions(
    company: str,
    culture_hints: dict[str, Any],
    count: int = 4,
) -> list[dict[str, str]]:
    """Build culture-fit questions based on company culture data."""
    results: list[dict[str, str]] = []
    culture_cat = culture_hints.get("culture_category", QuestionCategory.LARGE_CORP)

    pool = _pick_questions(culture_cat, count + 2, min_frequency=3)
    for q in pool[:count]:
        results.append({
            "question": q.question,
            "answer": " / ".join(q.answer_points[:2]),
        })

    return results


def _build_company_reverse_questions(
    company: str,
    culture_hints: dict[str, Any],
    report: AnalysisReport | None,
    base_questions: list[str],
) -> list[str]:
    """Build company-specific reverse questions using company data."""
    keywords = list(culture_hints.get("keywords", []))

    # Extract keywords from report if available
    if report:
        for section_data in report.sections.values():
            if isinstance(section_data, dict):
                for val in section_data.values():
                    if isinstance(val, str) and len(val) > 5:
                        # Pick first meaningful noun-like word
                        words = [w for w in val.split() if len(w) >= 2]
                        keywords.extend(words[:2])

    # Generate company-specific questions
    company_qs: list[str] = []
    for kw in keywords[:3]:
        template = _COMPANY_REVERSE_TEMPLATES[len(company_qs) % len(_COMPANY_REVERSE_TEMPLATES)]
        company_qs.append(template.format(company=company, keyword=kw))

    # Merge with base questions (company-name substituted)
    substituted = [q.replace("{company}", company) for q in base_questions]

    # Deduplicate
    seen: set[str] = set()
    final: list[str] = []
    for q in company_qs + substituted:
        if q not in seen:
            seen.add(q)
            final.append(q)

    return final[:7]


def _build_answer_guides_for_guide(guide: InterviewGuide) -> list[AnswerGuide]:
    """Build answer guides for the top behavioral questions in the guide."""
    guides: list[AnswerGuide] = []

    # Collect question texts from behavioral and high-frequency common
    question_texts = [q["question"] for q in guide.behavioral_questions[:3]]
    question_texts += [q["question"] for q in guide.technical_questions[:2]]

    # Match back to QUESTION_BANK
    q_map = {q.question: q for q in QUESTION_BANK}
    for text in question_texts:
        if text in q_map:
            guides.append(build_answer_guide(q_map[text]))

    return guides


def _build_session(
    guide: InterviewGuide,
    total_minutes: int = 60,
) -> InterviewSession:
    """Build an InterviewSession from a guide with time allocation and difficulty curve."""
    session = InterviewSession(
        company=guide.company,
        position=guide.position,
        total_minutes=total_minutes,
    )

    # Collect all questions from guide (map back to InterviewQuestion where possible)
    q_map = {q.question: q for q in QUESTION_BANK}
    all_q_texts: list[str] = (
        [q["question"] for q in guide.common_questions[:2]]
        + [q["question"] for q in guide.technical_questions[:4]]
        + [q["question"] for q in guide.behavioral_questions[:3]]
        + [q["question"] for q in guide.culture_fit_questions[:2]]
    )

    matched: list[InterviewQuestion] = []
    for text in all_q_texts:
        if text in q_map:
            matched.append(q_map[text])

    # Sort: easy → medium → hard (difficulty curve)
    matched.sort(key=lambda q: q.difficulty)
    session.questions = matched
    session.difficulty_curve = [q.difficulty for q in matched]

    # Allocate time proportional to difficulty
    total_sec = total_minutes * 60
    weights = [q.difficulty for q in matched] if matched else [1]
    total_weight = sum(weights) or 1
    session.time_per_question = [
        int(total_sec * w / total_weight) for w in weights
    ]

    return session


class InterviewPrep:
    """Generate company-specific interview preparation guides."""

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or NoLLM()

    def prepare(
        self,
        company: str,
        position: str = "",
        report: AnalysisReport | None = None,
        profile: dict[str, Any] | None = None,
        jd_skills: list[str] | None = None,
    ) -> InterviewGuide:
        """Generate interview preparation guide.

        Args:
            company: Company name.
            position: Target position/role.
            report: Company analysis report (for context).
            profile: User career profile.
            jd_skills: Tech skills extracted from the job description.
        """
        guide = InterviewGuide(company=company, position=position)

        # 1. Common questions (template-based, always available)
        guide.common_questions = [
            {
                "question": q["question"].replace("{company}", company),
                "answer": q["answer"],
            }
            for q in DEFAULT_COMMON_QUESTIONS
        ]

        # 2. Company culture hints
        culture_hints = _detect_company_culture(company)

        # 3. Technical questions — JD-based or role-based
        skills = jd_skills or []
        if profile:
            tech_skills = profile.get("skills", {}).get("technical", [])
            skills = list(set(skills + tech_skills))

        guide.technical_questions = _build_tech_questions_from_jd(
            jd_skills=jd_skills or [],
            position=position,
            count=8,
        )

        # 4. Behavioral (STAR) questions
        guide.behavioral_questions = _build_behavioral_questions(count=5)

        # 5. Culture-fit questions
        guide.culture_fit_questions = _build_culture_fit_questions(
            company=company,
            culture_hints=culture_hints,
            count=4,
        )

        # 6. Reverse questions (company-data driven, cap at 5)
        guide.reverse_questions = _build_company_reverse_questions(
            company=company,
            culture_hints=culture_hints,
            report=report,
            base_questions=DEFAULT_REVERSE_QUESTIONS,
        )[:5]

        # 7. Rule-based answer guides
        guide.answer_guides = _build_answer_guides_for_guide(guide)

        # 8. Tips (always generated, LLM can override)
        guide.tips = self._build_tips(company, position, culture_hints, profile)

        # 9. LLM-enhanced preparation (overrides/extends above)
        if self.llm.is_available():
            self._enhance_with_llm(guide, report, profile)

        return guide

    def build_session(
        self,
        guide: InterviewGuide,
        total_minutes: int = 60,
    ) -> InterviewSession:
        """Build a timed interview simulation session from a guide."""
        return _build_session(guide, total_minutes=total_minutes)

    def _build_tips(
        self,
        company: str,
        position: str,
        culture_hints: dict[str, Any],
        profile: dict[str, Any] | None,
    ) -> list[str]:
        """Generate rule-based tips tailored to company and position."""
        tips = [
            f"{company}의 최근 뉴스, 공식 블로그, IR 자료를 면접 전날 반드시 확인하세요.",
            "STAR 형식(상황-과제-행동-결과)으로 3개 이상의 경험 스토리를 준비하세요.",
            "역질문은 단순 복지 질문이 아닌, 사업/기술 방향에 관한 질문으로 준비하세요.",
            "정량적 성과(%, 시간 단축, 트래픽 규모)를 최소 3개 이상 암기해 두세요.",
            "기술 면접 전에 해당 기업의 기술 블로그와 GitHub 레포지토리를 살펴보세요.",
        ]

        keywords = culture_hints.get("keywords", [])
        if keywords:
            tips.append(
                f"{company}의 핵심 키워드인 '{', '.join(keywords[:3])}'와 본인 경험을 연결하는 스토리를 준비하세요."
            )

        is_startup = culture_hints.get("is_startup", False)
        if is_startup:
            tips.append("스타트업 면접에서는 불확실한 환경에서의 실행력과 오너십을 강조하세요.")
            tips.append("MVP 경험, 빠른 가설 검증 경험을 구체적으로 준비하세요.")
        else:
            tips.append("대기업 면접에서는 협업과 조직 내 영향력을 발휘한 사례를 강조하세요.")
            tips.append("규모 있는 시스템 운영 경험(대용량 트래픽, 레거시 개선 등)을 어필하세요.")

        pos_lower = position.lower()
        if any(k in pos_lower for k in ["lead", "리드", "manager", "head"]):
            tips.append("리더십 면접에서는 팀원의 성장을 이끈 사례와 기술적 의사결정 경험을 준비하세요.")

        if profile:
            gaps = profile.get("gaps", [])
            if gaps:
                tips.append(f"부족한 역량({', '.join(gaps[:2])})은 보완 계획과 함께 솔직하게 언급하세요.")

        return tips

    def _enhance_with_llm(
        self,
        guide: InterviewGuide,
        report: AnalysisReport | None,
        profile: dict[str, Any] | None,
    ) -> None:
        """Use LLM to generate company-specific questions and coaching."""
        company_context = ""
        if report:
            for section_num, section_data in sorted(report.sections.items()):
                if isinstance(section_data, dict):
                    for key, val in section_data.items():
                        if isinstance(val, str):
                            company_context += f"{key}: {val[:200]}\n"

        profile_context = ""
        if profile:
            skills = profile.get("skills", {})
            assets = profile.get("career_assets", [])
            profile_context = (
                f"Skills: {', '.join(skills.get('technical', []))}\n"
                f"Domain: {', '.join(skills.get('domain', []))}\n"
                f"Assets: {', '.join(a['asset'] for a in assets[:5])}\n"
                f"Experience: {profile.get('years_of_experience', 'N/A')} years\n"
            )

        prompt = (
            f"회사: {guide.company}\n"
            f"포지션: {guide.position}\n\n"
            f"회사 정보:\n{company_context[:2000]}\n\n"
            f"지원자 프로필:\n{profile_context}\n\n"
            "위 정보를 바탕으로 면접 준비 가이드를 작성해주세요:\n\n"
            "1. 이 회사의 면접 프로세스 (라운드별 형태와 평가 포인트)\n"
            "2. 직무 특화 기술 질문 5개 (답변 방향 포함)\n"
            "3. 행동 면접(STAR) 질문 3개 (지원자 경력 기반)\n"
            "4. 역질문 5개 (기업 이해도를 보여주는 질문)\n"
            "5. 합격 팁 5개 (이 회사/포지션 특화)\n"
        )

        resp = self.llm.generate(prompt=prompt, temperature=0.3)
        if resp.text:
            self._parse_llm_guide(guide, resp.text)

    def _parse_llm_guide(self, guide: InterviewGuide, text: str) -> None:
        """Parse LLM response into structured guide."""
        import re

        sections = re.split(r"\n(?=\d+\.)", text)
        for section in sections:
            items = re.findall(r"[-•]\s*(.+)", section)
            lower = section.lower()

            if "프로세스" in lower or "라운드" in lower:
                guide.interview_process = items
            elif "기술" in lower or "직무" in lower:
                guide.technical_questions = [
                    {"question": q, "answer": ""} for q in items
                ]
            elif "행동" in lower or "star" in lower:
                guide.behavioral_questions = [
                    {"question": q, "answer": ""} for q in items
                ]
            elif "역질문" in lower:
                guide.reverse_questions = items
            elif "팁" in lower or "합격" in lower:
                guide.tips = items
