"""Interview preparation engine — generate questions and coaching."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.llm.base import BaseLLM, NoLLM


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
class InterviewGuide:
    """Structured interview preparation guide."""

    company: str
    position: str = ""

    # Question categories
    common_questions: list[dict[str, str]] = field(default_factory=list)
    technical_questions: list[dict[str, str]] = field(default_factory=list)
    behavioral_questions: list[dict[str, str]] = field(default_factory=list)
    reverse_questions: list[str] = field(default_factory=list)

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


# Default question templates (used in No-LLM mode)
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
    ) -> InterviewGuide:
        """Generate interview preparation guide.

        Args:
            company: Company name.
            position: Target position/role.
            report: Company analysis report (for context).
            profile: User career profile.
        """
        guide = InterviewGuide(company=company, position=position)

        # Template-based questions (always available)
        guide.common_questions = [
            {
                "question": q["question"].replace("{company}", company),
                "answer": q["answer"],
            }
            for q in DEFAULT_COMMON_QUESTIONS
        ]
        guide.reverse_questions = [
            q.replace("{company}", company) for q in DEFAULT_REVERSE_QUESTIONS
        ]

        # LLM-enhanced preparation
        if self.llm.is_available():
            self._enhance_with_llm(guide, report, profile)
        else:
            # Add default tips in no-LLM mode
            guide.tips = [
                f"Research {company}'s recent news and strategy before the interview",
                "Prepare 3 STAR stories that match the role requirements",
                "Practice your reverse questions — they show genuine interest",
                "Review the company's tech blog and engineering culture",
                "Prepare concrete examples with quantitative results",
            ]

        return guide

    def _enhance_with_llm(
        self,
        guide: InterviewGuide,
        report: AnalysisReport | None,
        profile: dict[str, Any] | None,
    ) -> None:
        """Use LLM to generate company-specific questions and coaching."""
        company_context = ""
        if report:
            # Build context from report sections
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
