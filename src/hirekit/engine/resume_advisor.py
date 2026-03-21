"""Resume advisor — review, feedback, and JD-tailored suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hirekit.llm.base import BaseLLM, NoLLM

# ---------------------------------------------------------------------------
# Section recognition
# ---------------------------------------------------------------------------

_SECTION_KEYWORDS: dict[str, list[str]] = {
    "contact": [
        "이메일", "연락처", "전화", "email", "phone", "contact", "주소", "github",
    ],
    "summary": [
        "요약", "자기소개", "소개", "summary", "about", "profile", "objective",
    ],
    "experience": [
        "경력사항", "경력", "경험", "이전 직장", "work experience", "experience",
        "직장", "재직", "회사",
    ],
    "education": [
        "학력", "학교", "대학", "education", "대학교", "졸업", "전공",
    ],
    "skills": [
        "보유 기술", "기술 스택", "기술", "역량", "skills", "tech stack",
        "technologies", "tools", "언어",
    ],
    "projects": [
        "프로젝트 경험", "프로젝트", "project", "portfolio", "포트폴리오", "작업물",
    ],
    "certifications": [
        "자격증", "certification", "license", "수료", "어학",
    ],
    "awards": [
        "수상", "award", "achievement", "honors", "대회", "공모전",
    ],
}

_SECTION_LABELS: dict[str, str] = {
    "contact": "인적사항/연락처",
    "summary": "자기소개/요약",
    "experience": "경력사항",
    "education": "학력",
    "skills": "기술 스택",
    "projects": "프로젝트 경험",
    "certifications": "자격증",
    "awards": "수상/수료",
}

_REQUIRED_SECTIONS = {"contact", "experience", "education", "skills"}

_ATS_ISSUES: list[tuple[str, str]] = [
    (
        r"[^\x00-\x7F\uAC00-\uD7A3\u3000-\u303F\u0020-\u007E]",
        "비표준 특수문자 감지 (ATS 파싱 오류 가능)",
    ),
    (r"(\.png|\.jpg|\.jpeg|\.gif)", "이미지 참조 포함 (ATS는 이미지를 읽지 못함)"),
    (r"<table|<img|<div", "HTML 태그 포함 (plain text로 변환하세요)"),
]

_ACTION_VERBS_KO: list[str] = [
    "설계", "구축", "개발", "운영", "최적화", "개선", "리드", "주도",
    "기획", "분석", "도입", "자동화", "달성", "구현", "제안", "협업",
    "관리", "배포", "출시", "절감", "증가", "확장", "연구", "검증",
    "했습니다", "이끌었습니다", "달성했습니다", "개발했습니다", "주도했습니다",
]
_ACTION_VERBS_EN: list[str] = [
    "built", "led", "designed", "improved", "launched", "reduced",
    "increased", "managed", "created", "developed", "deployed", "optimized",
    "implemented", "delivered", "achieved", "established",
]

_QUANT_PATTERN = re.compile(
    r"\d+\s*[%％]"
    r"|\d+[만억천원]+"
    r"|\d+\s*명"
    r"|\d+\s*[건개]"
    r"|\d+\s*배"
    r"|\d+[xX배]"
    r"|\$\s*\d+"
    r"|\d+\s*(ms|초|분|시간)"
    r"|\d+\s*(TB|GB|MB)"
    r"|[+-]\d+\s*[%％]",
    re.UNICODE,
)


@dataclass
class SectionAnalysis:
    """Result of structure analysis for a single resume section."""

    key: str
    label: str
    found: bool
    required: bool
    line_count: int = 0
    char_count: int = 0
    quant_count: int = 0
    action_verb_count: int = 0


@dataclass
class ResumeFeedback:
    """Structured feedback on a resume."""

    overall_score: float = 0.0
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    missing_sections: list[str] = field(default_factory=list)
    keyword_gaps: list[str] = field(default_factory=list)
    ats_issues: list[str] = field(default_factory=list)
    tailored_suggestions: list[str] = field(default_factory=list)
    rewritten_sections: dict[str, str] = field(default_factory=dict)

    # Enhanced analysis fields
    section_analyses: list[SectionAnalysis] = field(default_factory=list)
    completeness_score: float = 0.0
    keyword_density: dict[str, int] = field(default_factory=dict)
    quant_score: float = 0.0
    action_verb_ratio: float = 0.0
    before_after_suggestions: list[dict[str, str]] = field(default_factory=list)
    ats_keyword_suggestions: list[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        from hirekit.core.scoring import score_to_grade

        return score_to_grade(self.overall_score)

    def to_markdown(self) -> str:
        lines = [
            "# Resume Review",
            f"**Score:** {self.overall_score:.0f}/100 (Grade {self.grade})",
            f"**Completeness:** {self.completeness_score:.0f}/100",
            f"**Quantification:** {self.quant_score:.0f}/100",
            "",
            "---",
        ]

        if self.section_analyses:
            lines.append("\n## Section Analysis")
            for sa in self.section_analyses:
                status = "v" if sa.found else "x"
                req = " (필수)" if sa.required else ""
                lines.append(f"- {status} **{sa.label}**{req}")
                if sa.found and sa.quant_count:
                    lines.append(f"  - 정량 지표: {sa.quant_count}개")
                if sa.found and sa.action_verb_count:
                    lines.append(f"  - 액션 동사: {sa.action_verb_count}개")

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

        if self.before_after_suggestions:
            lines.append("\n## Before -> After 개선 예시")
            for ba in self.before_after_suggestions:
                lines.append(f"\n**Before:** {ba['before']}")
                lines.append(f"**After:** {ba['after']}")
                if ba.get("tip"):
                    lines.append(f"*Tip: {ba['tip']}*")

        if self.ats_keyword_suggestions:
            lines.append("\n## ATS 키워드 최적화 제안")
            for kw in self.ats_keyword_suggestions:
                lines.append(f"- {kw}")

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
        """Review a resume file and provide feedback."""
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

        # Rule-based analysis (always runs, no LLM needed)
        self._analyze_structure(resume_text, feedback)
        self._check_ats(resume_text, feedback)
        self._check_content_quality(resume_text, feedback)
        self._score_completeness(feedback)
        self._generate_before_after(resume_text, feedback)

        if jd_text:
            self._check_keyword_match(resume_text, jd_text, feedback)
            self._suggest_ats_keywords(resume_text, jd_text, feedback)

        if self.llm.is_available():
            self._llm_review(resume_text, jd_text, profile, feedback)

        self._calculate_score(feedback)

        return feedback

    def _read_resume(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in (".md", ".txt", ".text"):
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            try:
                import subprocess

                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return result.stdout
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return path.read_bytes().decode("utf-8", errors="ignore")
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ""

    def _analyze_structure(self, text: str, feedback: ResumeFeedback) -> None:
        """Detect Korean/English resume sections and compute per-section metrics."""
        text_lower = text.lower()
        section_blocks = self._split_into_section_blocks(text)

        for key, keywords in _SECTION_KEYWORDS.items():
            found = any(kw.lower() in text_lower for kw in keywords)
            label = _SECTION_LABELS[key]
            required = key in _REQUIRED_SECTIONS

            sa = SectionAnalysis(key=key, label=label, found=found, required=required)

            if found:
                block = section_blocks.get(key, "")
                block_lines = [ln for ln in block.splitlines() if ln.strip()]
                sa.line_count = len(block_lines)
                sa.char_count = len(block)
                sa.quant_count = len(_QUANT_PATTERN.findall(block))
                sa.action_verb_count = self._count_action_verbs(block)
                feedback.strengths.append(f"{key} section present ({label})")
            else:
                if required:
                    feedback.missing_sections.append(label)
                else:
                    feedback.missing_sections.append(f"{label} (선택)")

            feedback.section_analyses.append(sa)

    def _split_into_section_blocks(self, text: str) -> dict[str, str]:
        blocks: dict[str, str] = {}
        lines = text.splitlines()
        current_key: str | None = None
        current_lines: list[str] = []

        for line in lines:
            line_lower = line.lower().strip()
            matched_key = self._match_section_key(line_lower)
            if matched_key:
                if current_key:
                    blocks[current_key] = "\n".join(current_lines)
                current_key = matched_key
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_key:
            blocks[current_key] = "\n".join(current_lines)

        return blocks

    def _match_section_key(self, line_lower: str) -> str | None:
        for key, keywords in _SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in line_lower:
                    return key
        return None

    def _count_action_verbs(self, text: str) -> int:
        text_lower = text.lower()
        count = 0
        for verb in _ACTION_VERBS_KO + _ACTION_VERBS_EN:
            count += text_lower.count(verb.lower())
        return count

    def _score_completeness(self, feedback: ResumeFeedback) -> None:
        if not feedback.section_analyses:
            feedback.completeness_score = 0.0
            return

        required_found = sum(1 for sa in feedback.section_analyses if sa.required and sa.found)
        optional_found = sum(1 for sa in feedback.section_analyses if not sa.required and sa.found)
        optional_total = sum(1 for sa in feedback.section_analyses if not sa.required)

        required_score = (required_found / len(_REQUIRED_SECTIONS)) * 60
        optional_score = (optional_found / optional_total) * 40 if optional_total else 0
        feedback.completeness_score = round(required_score + optional_score, 1)

    def _check_ats(self, text: str, feedback: ResumeFeedback) -> None:
        for pattern, issue in _ATS_ISSUES:
            if re.search(pattern, text):
                feedback.ats_issues.append(issue)

        word_count = len(text.split())
        if word_count < 100:
            feedback.ats_issues.append(
                f"Too short ({word_count} words). Aim for 300-600 words."
            )
        elif word_count > 1500:
            feedback.ats_issues.append(
                f"Too long ({word_count} words). Keep under 1000 for readability."
            )

    def _check_content_quality(self, text: str, feedback: ResumeFeedback) -> None:
        quant_matches = _QUANT_PATTERN.findall(text)
        quant_count = len(quant_matches)

        if quant_count >= 5:
            feedback.strengths.append(f"정량적 성과 {quant_count}개 포함 (우수)")
            feedback.quant_score = min(100.0, 60 + quant_count * 4)
        elif quant_count >= 2:
            feedback.improvements.append(
                f"정량 지표 {quant_count}개 발견. "
                "5개 이상을 목표로 수치(%, 명, 억원 등)를 추가하세요."
            )
            feedback.quant_score = 40.0 + quant_count * 8
        else:
            feedback.improvements.append(
                "정량적 성과가 부족합니다. "
                "'매출 30% 증가', '사용자 5,000명 확보' 등을 추가하세요."
            )
            feedback.quant_score = max(0.0, quant_count * 15.0)

        total_action_verbs = self._count_action_verbs(text)
        sentence_count = max(1, len(re.split(r"[.。\n]", text)))
        ratio = min(1.0, total_action_verbs / sentence_count)
        feedback.action_verb_ratio = round(ratio, 2)

        if total_action_verbs >= 5:
            feedback.strengths.append(f"액션 동사 {total_action_verbs}개 사용 (능동적 서술)")
        else:
            feedback.improvements.append(
                "액션 동사를 더 사용하세요: '개발했습니다', '주도했습니다', '달성했습니다' 등"
            )

        tech_terms = re.findall(
            r"\b[A-Z][a-zA-Z0-9+#._-]{1,}\b|[가-힣]{2,}(?:\s[가-힣]{2,})?",
            text,
        )
        density: dict[str, int] = {}
        for term in tech_terms:
            t = term.strip()
            if t and len(t) >= 2:
                density[t] = density.get(t, 0) + 1
        feedback.keyword_density = dict(
            sorted(density.items(), key=lambda x: x[1], reverse=True)[:20]
        )

    def _generate_before_after(self, text: str, feedback: ResumeFeedback) -> None:
        suggestions: list[dict[str, str]] = []

        vague = re.search(
            r"([가-힣a-zA-Z ]{3,20})\s*(업무를\s*담당|을\s*담당|를\s*담당|담당했습니다|맡았습니다)",
            text,
        )
        if vague:
            suggestions.append({
                "before": vague.group(0).strip(),
                "after": f"{vague.group(1)} 업무 수행 — [구체적 기여/수치] 달성",
                "tip": "담당->달성으로 전환하고 수치를 추가하세요.",
            })

        contrib = re.search(r"([가-힣a-zA-Z ]{3,30})\s*에\s*기여했습니다", text)
        if contrib and not _QUANT_PATTERN.search(contrib.group(0)):
            suggestions.append({
                "before": contrib.group(0).strip(),
                "after": f"{contrib.group(1)} 개선에 기여 — XX% 향상 / XX명 증가",
                "tip": "기여의 규모를 수치로 증명하세요.",
            })

        dev = re.search(r"([가-힣a-zA-Za-z ]{3,30})\s*(개발했습니다|구축했습니다)", text)
        if dev and not _QUANT_PATTERN.search(dev.group(0)):
            suggestions.append({
                "before": dev.group(0).strip(),
                "after": f"{dev.group(1)} 개발 — [규모/성능/사용자 수] 포함",
                "tip": "기술 스택과 결과 규모를 함께 기술하세요.",
            })

        feedback.before_after_suggestions = suggestions[:5]

    def _check_keyword_match(self, resume: str, jd: str, feedback: ResumeFeedback) -> None:
        stop_words = {
            "the", "and", "for", "you", "are", "with", "this", "that",
            "our", "have", "will", "from", "not", "but", "can", "all",
            "경험", "이상", "관련", "우대", "필수", "능력", "담당",
        }
        jd_words = set(re.findall(r"[a-zA-Z가-힣]{2,}", jd.lower()))
        jd_keywords = jd_words - stop_words
        resume_lower = resume.lower()
        missing = [k for k in jd_keywords if k not in resume_lower]
        significant_missing = [
            m for m in missing
            if len(m) >= 3 or any(c >= "\uac00" for c in m)
        ][:15]
        feedback.keyword_gaps = significant_missing

    def _suggest_ats_keywords(self, resume: str, jd: str, feedback: ResumeFeedback) -> None:
        tech_pattern = re.compile(
            r"\b([A-Z][a-zA-Z0-9+#._-]{1,}|[가-힣]{2,6}(?:JS|QL|AI|ML|DB)?)\b"
        )
        jd_tech = set(tech_pattern.findall(jd))
        resume_lower = resume.lower()
        missing_tech = [
            t for t in jd_tech
            if t.lower() not in resume_lower and len(t) >= 2
        ]
        feedback.ats_keyword_suggestions = [
            f"JD 핵심 키워드 '{kw}'이(가) 이력서에 없습니다. 기술 스택 또는 경력 항목에 추가하세요."
            for kw in sorted(missing_tech)[:8]
        ]

    def _llm_review(
        self,
        resume: str,
        jd: str,
        profile: dict[str, Any] | None,
        feedback: ResumeFeedback,
    ) -> None:
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
        completeness_contrib = feedback.completeness_score * 0.40
        quant_contrib = feedback.quant_score * 0.30
        action_score = min(100.0, feedback.action_verb_ratio * 200)
        ats_penalty = len(feedback.ats_issues) * 5
        action_contrib = max(0.0, action_score - ats_penalty) * 0.30
        raw = completeness_contrib + quant_contrib + action_contrib
        raw += len(feedback.strengths) * 2
        raw -= len(feedback.improvements) * 1.5
        raw -= min(len(feedback.keyword_gaps), 5) * 1.5
        feedback.overall_score = round(max(0.0, min(100.0, raw)), 1)
