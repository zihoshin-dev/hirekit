"""JD (Job Description) matcher — parse job postings and match against user profile."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx
from bs4 import BeautifulSoup

from hirekit.llm.base import BaseLLM, NoLLM


@dataclass
class SkillMatch:
    """A single skill requirement and its match status."""

    skill: str
    required: bool = True  # required vs preferred
    matched: bool = False
    user_evidence: str = ""  # from profile


@dataclass
class JDAnalysis:
    """Structured analysis of a job description."""

    title: str = ""
    company: str = ""
    url: str = ""
    raw_text: str = ""

    # Extracted requirements
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_years: str = ""
    education: str = ""
    responsibilities: list[str] = field(default_factory=list)
    qualifications: list[str] = field(default_factory=list)

    # Match results (filled after matching)
    skill_matches: list[SkillMatch] = field(default_factory=list)
    match_score: float = 0.0  # 0-100
    gaps: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    strategy: str = ""  # LLM-generated application strategy

    @property
    def match_grade(self) -> str:
        if self.match_score >= 80:
            return "S"
        if self.match_score >= 65:
            return "A"
        if self.match_score >= 50:
            return "B"
        if self.match_score >= 35:
            return "C"
        return "D"

    def to_markdown(self) -> str:
        lines = [
            f"# JD Analysis: {self.title}",
            f"**Company:** {self.company}",
            f"**Match Score:** {self.match_score:.0f}/100 (Grade {self.match_grade})",
            "",
            "---",
            "",
            "## Requirements",
            f"**Experience:** {self.experience_years}",
            f"**Education:** {self.education}",
            "",
            "### Required Skills",
        ]
        for s in self.required_skills:
            lines.append(f"- {s}")

        if self.preferred_skills:
            lines.append("\n### Preferred Skills")
            for s in self.preferred_skills:
                lines.append(f"- {s}")

        if self.responsibilities:
            lines.append("\n## Responsibilities")
            for r in self.responsibilities:
                lines.append(f"- {r}")

        lines.append("\n---\n")
        lines.append("## Match Analysis")

        if self.strengths:
            lines.append("\n### Strengths (what you bring)")
            for s in self.strengths:
                lines.append(f"- {s}")

        if self.gaps:
            lines.append("\n### Gaps (what to address)")
            for g in self.gaps:
                lines.append(f"- {g}")

        if self.skill_matches:
            lines.append("\n### Skill Matching Detail")
            lines.append("| Skill | Required | Matched | Evidence |")
            lines.append("|-------|----------|---------|----------|")
            for m in self.skill_matches:
                req = "Required" if m.required else "Preferred"
                matched = "O" if m.matched else "X"
                lines.append(
                    f"| {m.skill} | {req} | {matched} | {m.user_evidence} |"
                )

        if self.strategy:
            lines.append("\n---\n")
            lines.append("## Application Strategy")
            lines.append(self.strategy)

        return "\n".join(lines)


class JDMatcher:
    """Parse job descriptions and match against user profile."""

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or NoLLM()

    def analyze(
        self,
        jd_source: str,
        profile: dict[str, Any] | None = None,
    ) -> JDAnalysis:
        """Analyze a JD from URL or text.

        Args:
            jd_source: URL to job posting or raw JD text.
            profile: User career profile dict (from profile.yaml).
        """
        # 1. Get JD text
        if jd_source.startswith("http"):
            raw_text, title, company = self._fetch_jd(jd_source)
            url = jd_source
        else:
            raw_text = jd_source
            title, company, url = "", "", ""

        analysis = JDAnalysis(
            title=title, company=company, url=url, raw_text=raw_text
        )

        # 2. Extract requirements (rule-based + LLM)
        self._extract_requirements(analysis)

        # 3. Match against profile
        if profile:
            self._match_profile(analysis, profile)

        # 4. Generate strategy (LLM)
        if self.llm.is_available() and not isinstance(self.llm, NoLLM):
            self._generate_strategy(analysis, profile)

        return analysis

    def _fetch_jd(self, url: str) -> tuple[str, str, str]:
        """Fetch and extract text from a JD URL."""
        try:
            resp = httpx.get(
                url, timeout=15, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit)"},
            )
            soup = BeautifulSoup(resp.text, "lxml")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title else ""
            text = soup.get_text(separator="\n", strip=True)

            # Try to extract company name from common patterns
            company = ""
            og_site = soup.find("meta", property="og:site_name")
            if og_site:
                company = og_site.get("content", "")

            return text[:8000], title, company
        except Exception:
            return "", "", ""

    def _extract_requirements(self, analysis: JDAnalysis) -> None:
        """Extract skills and requirements from JD text."""
        text = analysis.raw_text
        if not text:
            return

        # Use LLM for structured extraction if available
        if self.llm.is_available() and not isinstance(self.llm, NoLLM):
            self._llm_extract(analysis)
            return

        # Rule-based extraction (fallback)
        lines = text.split("\n")
        in_required = False
        in_preferred = False
        in_responsibility = False

        required_keywords = [
            "자격요건", "필수", "required", "requirements",
            "자격 요건", "지원자격", "필수 요건",
        ]
        preferred_keywords = [
            "우대", "preferred", "nice to have", "bonus",
            "우대사항", "우대 사항", "플러스",
        ]
        responsibility_keywords = [
            "담당업무", "주요업무", "responsibilities", "what you",
            "담당 업무", "주요 업무", "이런 일",
        ]

        for line in lines:
            lower = line.lower().strip()

            if any(k in lower for k in required_keywords):
                in_required, in_preferred, in_responsibility = True, False, False
                continue
            if any(k in lower for k in preferred_keywords):
                in_required, in_preferred, in_responsibility = False, True, False
                continue
            if any(k in lower for k in responsibility_keywords):
                in_required, in_preferred, in_responsibility = False, False, True
                continue

            # Empty line resets section
            if not lower:
                continue

            # Collect bullet points
            cleaned = re.sub(r"^[-•·\d.)\s]+", "", line).strip()
            if not cleaned or len(cleaned) < 3:
                continue

            if in_required:
                analysis.required_skills.append(cleaned)
            elif in_preferred:
                analysis.preferred_skills.append(cleaned)
            elif in_responsibility:
                analysis.responsibilities.append(cleaned)

        # Extract experience years
        exp_match = re.search(
            r"(\d+)\s*[년~\-+]\s*(?:이상|경력|years?)", text
        )
        if exp_match:
            analysis.experience_years = f"{exp_match.group(1)}년 이상"

    def _llm_extract(self, analysis: JDAnalysis) -> None:
        """Use LLM for structured JD extraction."""
        prompt = (
            "다음 채용공고에서 정보를 추출해주세요.\n\n"
            f"```\n{analysis.raw_text[:4000]}\n```\n\n"
            "다음 형식으로 추출:\n"
            "1. 필수 자격요건 (bullet list)\n"
            "2. 우대사항 (bullet list)\n"
            "3. 담당업무 (bullet list)\n"
            "4. 요구 경력 연차\n"
            "5. 학력 요건\n"
        )
        resp = self.llm.generate(prompt=prompt, temperature=0.1)
        if resp.text:
            # Parse LLM response into structured fields
            self._parse_llm_extraction(analysis, resp.text)

    def _parse_llm_extraction(
        self, analysis: JDAnalysis, text: str
    ) -> None:
        """Parse LLM extraction response."""
        sections = re.split(r"\n(?=\d+\.)", text)
        for section in sections:
            items = re.findall(r"[-•]\s*(.+)", section)
            if "필수" in section or "자격요건" in section:
                analysis.required_skills.extend(items)
            elif "우대" in section:
                analysis.preferred_skills.extend(items)
            elif "담당" in section or "업무" in section:
                analysis.responsibilities.extend(items)

    def _match_profile(
        self, analysis: JDAnalysis, profile: dict[str, Any]
    ) -> None:
        """Match JD requirements against user profile."""
        user_skills: set[str] = set()
        for category in ["technical", "domain", "soft"]:
            user_skills.update(
                s.lower() for s in profile.get("skills", {}).get(category, [])
            )

        # Also extract keywords from career assets
        for asset in profile.get("career_assets", []):
            user_skills.add(asset.get("asset", "").lower())

        matched_count = 0
        total_required = len(analysis.required_skills)

        for skill in analysis.required_skills:
            skill_lower = skill.lower()
            is_matched = any(us in skill_lower or skill_lower in us for us in user_skills)
            evidence = ""
            if is_matched:
                matched_count += 1
                # Find matching asset for evidence
                for asset in profile.get("career_assets", []):
                    if asset.get("asset", "").lower() in skill_lower:
                        evidence = asset.get("source", "")
                        break

            analysis.skill_matches.append(SkillMatch(
                skill=skill, required=True, matched=is_matched,
                user_evidence=evidence,
            ))

        for skill in analysis.preferred_skills:
            skill_lower = skill.lower()
            is_matched = any(us in skill_lower or skill_lower in us for us in user_skills)
            analysis.skill_matches.append(SkillMatch(
                skill=skill, required=False, matched=is_matched,
            ))

        # Calculate match score
        if total_required > 0:
            required_ratio = matched_count / total_required
        else:
            required_ratio = 0.5  # No clear requirements extracted

        preferred_matched = sum(
            1 for m in analysis.skill_matches if not m.required and m.matched
        )
        preferred_total = len(analysis.preferred_skills)
        preferred_ratio = (
            preferred_matched / preferred_total if preferred_total > 0 else 0
        )

        analysis.match_score = (required_ratio * 0.7 + preferred_ratio * 0.3) * 100

        # Identify gaps and strengths
        analysis.gaps = [
            m.skill for m in analysis.skill_matches
            if m.required and not m.matched
        ]
        analysis.strengths = [
            m.skill for m in analysis.skill_matches
            if m.matched
        ]

    def _generate_strategy(
        self,
        analysis: JDAnalysis,
        profile: dict[str, Any] | None,
    ) -> None:
        """Generate application strategy via LLM."""
        profile_summary = ""
        if profile:
            skills = profile.get("skills", {})
            assets = profile.get("career_assets", [])
            profile_summary = (
                f"기술: {', '.join(skills.get('technical', []))}\n"
                f"도메인: {', '.join(skills.get('domain', []))}\n"
                f"경력 자산: {', '.join(a['asset'] for a in assets)}\n"
            )

        gaps_text = "\n".join(f"- {g}" for g in analysis.gaps) or "없음"
        strengths_text = "\n".join(f"- {s}" for s in analysis.strengths) or "없음"

        prompt = (
            f"채용공고: {analysis.title} ({analysis.company})\n\n"
            f"나의 프로필:\n{profile_summary}\n"
            f"강점(매칭됨):\n{strengths_text}\n"
            f"갭(부족):\n{gaps_text}\n\n"
            "위 정보를 바탕으로 지원 전략을 작성해주세요:\n"
            "1. 자기소개서/커버레터에서 강조할 포인트 3개\n"
            "2. 갭을 보완하는 전략 (어떻게 프레이밍할지)\n"
            "3. 면접에서 예상되는 질문 3개와 답변 방향\n"
            "4. 이 포지션 지원을 추천하는지 (점수 기반)"
        )

        resp = self.llm.generate(prompt=prompt, temperature=0.3)
        if resp.text:
            analysis.strategy = resp.text
