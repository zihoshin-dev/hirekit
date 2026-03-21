"""Resume advisor — review, feedback, and JD-tailored suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hirekit.llm.base import BaseLLM, NoLLM


@dataclass
class ResumeFeedback:
    """Structured feedback on a resume."""

    overall_score: float = 0.0  # 0-100
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    keyword_gaps: list[str] = field(default_factory=list)  # vs JD
    ats_issues: list[str] = field(default_factory=list)
    tailored_suggestions: list[str] = field(default_factory=list)
    rewritten_sections: dict[str, str] = field(default_factory=dict)

    @property
    def grade(self) -> str:
        if self.overall_score >= 80:
            return "S"
        if self.overall_score >= 65:
            return "A"
        if self.overall_score >= 50:
            return "B"
        if self.overall_score >= 35:
            return "C"
        return "D"

    def to_markdown(self) -> str:
        lines = [
            "# Resume Review",
            f"**Score:** {self.overall_score:.0f}/100 (Grade {self.grade})",
            "",
            "---",
        ]

        if self.strengths:
            lines.append("\n## Strengths")
            for s in self.strengths:
                lines.append(f"- {s}")

        if self.improvements:
            lines.append("\n## Areas for Improvement")
            for i in self.improvements:
                lines.append(f"- {i}")

        if self.missing_sections:
            lines.append("\n## Missing Sections")
            for m in self.missing_sections:
                lines.append(f"- {m}")

        if self.ats_issues:
            lines.append("\n## ATS Compatibility Issues")
            for a in self.ats_issues:
                lines.append(f"- {a}")

        if self.keyword_gaps:
            lines.append("\n## Keyword Gaps (vs Job Description)")
            for k in self.keyword_gaps:
                lines.append(f"- {k}")

        if self.tailored_suggestions:
            lines.append("\n## Tailored Suggestions")
            for t in self.tailored_suggestions:
                lines.append(f"- {t}")

        if self.rewritten_sections:
            lines.append("\n---\n")
            lines.append("## Suggested Rewrites")
            for section, content in self.rewritten_sections.items():
                lines.append(f"\n### {section}")
                lines.append(content)

        return "\n".join(lines)


# Standard resume sections to check
EXPECTED_SECTIONS = [
    "contact", "summary", "experience", "education",
    "skills", "projects", "certifications",
]

# ATS-unfriendly patterns
ATS_ISSUES = [
    (r"[^\x00-\x7F\uAC00-\uD7A3\u3000-\u303F]", "Special characters detected"),
    (r"(\.png|\.jpg|\.jpeg|\.gif)", "Image references (ATS can't read images)"),
    (r"<table|<img|<div", "HTML formatting (use plain text)"),
]


class ResumeAdvisor:
    """Review resumes and provide actionable feedback."""

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or NoLLM()

    def review(
        self,
        resume_path: str | Path,
        jd_text: str = "",
        profile: dict[str, Any] | None = None,
    ) -> ResumeFeedback:
        """Review a resume file and provide feedback.

        Args:
            resume_path: Path to resume (Markdown, text, or PDF).
            jd_text: Optional JD text for targeted review.
            profile: Optional user career profile.
        """
        path = Path(resume_path)
        if not path.exists():
            feedback = ResumeFeedback()
            feedback.improvements.append(f"File not found: {resume_path}")
            return feedback

        resume_text = self._read_resume(path)
        if not resume_text:
            feedback = ResumeFeedback()
            feedback.improvements.append("Could not read resume file")
            return feedback

        feedback = ResumeFeedback()

        # Rule-based analysis (always runs)
        self._check_structure(resume_text, feedback)
        self._check_ats(resume_text, feedback)
        self._check_content_quality(resume_text, feedback)

        if jd_text:
            self._check_keyword_match(resume_text, jd_text, feedback)

        # LLM-enhanced review
        if self.llm.is_available() and not isinstance(self.llm, NoLLM):
            self._llm_review(resume_text, jd_text, profile, feedback)

        # Calculate overall score
        self._calculate_score(feedback)

        return feedback

    def _read_resume(self, path: Path) -> str:
        """Read resume from various formats."""
        suffix = path.suffix.lower()

        if suffix in (".md", ".txt", ".text"):
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            # Basic PDF text extraction
            try:
                import subprocess
                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True, text=True, timeout=10,
                )
                return result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return path.read_bytes().decode("utf-8", errors="ignore")

        # Try reading as text
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""

    def _check_structure(self, text: str, feedback: ResumeFeedback) -> None:
        """Check for expected resume sections."""
        text_lower = text.lower()

        section_keywords = {
            "contact": ["email", "phone", "연락처", "이메일"],
            "summary": ["summary", "about", "소개", "요약", "자기소개"],
            "experience": [
                "experience", "경력", "경험", "이전 직장", "work",
            ],
            "education": ["education", "학력", "학교", "대학"],
            "skills": ["skills", "기술", "역량", "tech stack"],
            "projects": ["project", "프로젝트", "포트폴리오"],
        }

        for section, keywords in section_keywords.items():
            found = any(k in text_lower for k in keywords)
            if found:
                feedback.strengths.append(f"{section} section present")
            else:
                feedback.missing_sections.append(section)

    def _check_ats(self, text: str, feedback: ResumeFeedback) -> None:
        """Check ATS compatibility."""
        for pattern, issue in ATS_ISSUES:
            if re.search(pattern, text):
                feedback.ats_issues.append(issue)

        # Check length
        word_count = len(text.split())
        if word_count < 100:
            feedback.ats_issues.append(
                f"Too short ({word_count} words). Aim for 300-600 words."
            )
        elif word_count > 1500:
            feedback.ats_issues.append(
                f"Too long ({word_count} words). Keep under 1000 for readability."
            )

    def _check_content_quality(
        self, text: str, feedback: ResumeFeedback
    ) -> None:
        """Check for content quality signals."""
        # Check for quantitative results
        numbers = re.findall(r"\d+[%만억원명건]", text)
        if numbers:
            feedback.strengths.append(
                f"Quantitative results found ({len(numbers)} metrics)"
            )
        else:
            feedback.improvements.append(
                "Add quantitative results (%, revenue, users, etc.)"
            )

        # Check for action verbs
        action_verbs = [
            "설계", "구축", "개발", "운영", "최적화", "개선",
            "리드", "주도", "기획", "분석", "도입", "자동화",
            "built", "led", "designed", "improved", "launched",
            "reduced", "increased", "managed", "created",
        ]
        found_verbs = [v for v in action_verbs if v in text.lower()]
        if len(found_verbs) >= 3:
            feedback.strengths.append("Strong action verbs used")
        else:
            feedback.improvements.append(
                "Use more action verbs (설계, 구축, 리드, 개선, etc.)"
            )

    def _check_keyword_match(
        self, resume: str, jd: str, feedback: ResumeFeedback
    ) -> None:
        """Compare resume keywords against JD requirements."""
        # Extract significant keywords from JD (2+ chars, not common words)
        stop_words = {
            "the", "and", "for", "you", "are", "with", "this", "that",
            "our", "have", "will", "from", "not", "but", "can", "all",
            "경험", "이상", "관련", "우대", "필수", "능력", "담당",
        }

        jd_words = set(re.findall(r"[a-zA-Z가-힣]{2,}", jd.lower()))
        jd_keywords = jd_words - stop_words

        resume_lower = resume.lower()
        missing = [k for k in jd_keywords if k not in resume_lower]

        # Only report significant gaps (filter common words)
        significant_missing = [
            m for m in missing
            if len(m) >= 3 or any(
                c >= "\uac00" for c in m  # Korean chars
            )
        ][:15]

        feedback.keyword_gaps = significant_missing

    def _llm_review(
        self,
        resume: str,
        jd: str,
        profile: dict[str, Any] | None,
        feedback: ResumeFeedback,
    ) -> None:
        """LLM-enhanced resume review."""
        jd_context = f"\n\n채용공고:\n{jd[:2000]}" if jd else ""

        prompt = (
            f"다음 이력서를 리뷰해주세요:\n\n"
            f"```\n{resume[:4000]}\n```\n"
            f"{jd_context}\n\n"
            "다음 관점에서 피드백을 제공하세요:\n"
            "1. 강점 3가지\n"
            "2. 개선사항 5가지 (구체적으로)\n"
            "3. 채용공고 대비 부족한 키워드/경험\n"
            "4. 핵심 섹션 개선 제안 (경력 기술 부분)\n"
            "5. ATS 통과를 위한 팁\n"
        )

        resp = self.llm.generate(prompt=prompt, temperature=0.3)
        if resp.text:
            feedback.tailored_suggestions.append(resp.text)

    def _calculate_score(self, feedback: ResumeFeedback) -> None:
        """Calculate overall resume score."""
        score = 50.0  # Base score

        # Positive signals
        score += len(feedback.strengths) * 5
        score -= len(feedback.improvements) * 3
        score -= len(feedback.missing_sections) * 5
        score -= len(feedback.ats_issues) * 4
        score -= min(len(feedback.keyword_gaps), 5) * 2

        feedback.overall_score = max(0, min(100, score))
