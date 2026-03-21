"""JD (Job Description) matcher — parse job postings and match against user profile."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import httpx
from bs4 import BeautifulSoup

from hirekit.core.tech_taxonomy import (
    normalize_tech,
    techs_are_similar,
)
from hirekit.engine.jd_parser import JDParser, ParsedJD
from hirekit.llm.base import BaseLLM, NoLLM

# ---------------------------------------------------------------------------
# Learning roadmap suggestions for common gaps
# ---------------------------------------------------------------------------

_LEARNING_ROADMAP: dict[str, str] = {
    "docker": "Docker 공식 튜토리얼 → Docker Compose 실습 (1-2주)",
    "kubernetes": "K8s 공식 튜토리얼 → CKA 준비 (2-3개월)",
    "aws": "AWS Free Tier 실습 → AWS SAA 자격증 (1-2개월)",
    "react": "React 공식 문서 → 토이 프로젝트 1개 (2-4주)",
    "typescript": "TypeScript Handbook → 기존 JS 프로젝트 마이그레이션 (1-2주)",
    "pytorch": "PyTorch 튜토리얼 → Kaggle 참여 (1개월)",
    "terraform": "Terraform 공식 튜토리얼 → 인프라 코드화 실습 (2-3주)",
    "graphql": "How to GraphQL 튜토리얼 → API 실습 (1주)",
    "kafka": "Confluent Kafka 101 → 스트리밍 파이프라인 실습 (2주)",
    "spark": "Spark 공식 퀵스타트 → PySpark 실습 (2주)",
}


@dataclass
class SkillMatch:
    """A single skill requirement and its match status."""

    skill: str
    required: bool = True       # required vs preferred
    matched: bool = False
    match_type: str = ""        # "exact", "similar", "partial", ""
    user_evidence: str = ""     # from profile
    learning_roadmap: str = ""  # suggested learning path if not matched


@dataclass
class ExperienceMatch:
    """Experience requirement vs user profile comparison."""

    required_min: int = 0
    required_max: int | None = None
    user_years: int = 0
    meets_requirement: bool = True
    note: str = ""


@dataclass
class JDAnalysis:
    """Structured analysis of a job description."""

    title: str = ""
    company: str = ""
    url: str = ""
    raw_text: str = ""

    # Extracted requirements (legacy + new parsed)
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_years: str = ""
    education: str = ""
    responsibilities: list[str] = field(default_factory=list)
    qualifications: list[str] = field(default_factory=list)

    # Enhanced parsed data
    parsed: ParsedJD | None = None

    # Match results (filled after matching)
    skill_matches: list[SkillMatch] = field(default_factory=list)
    experience_match: ExperienceMatch | None = None
    match_score: float = 0.0    # 0-100
    gaps: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    gap_roadmaps: dict[str, str] = field(default_factory=dict)  # gap → learning path
    strategy: str = ""          # LLM-generated application strategy

    @property
    def match_grade(self) -> str:
        from hirekit.core.scoring import score_to_grade
        return score_to_grade(self.match_score)

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

        if self.experience_match:
            em = self.experience_match
            status = "충족" if em.meets_requirement else "미충족"
            lines.append(
                f"\n**경력 적합도:** 요구 {em.required_min}년+ / "
                f"보유 {em.user_years}년 → {status}"
            )
            if em.note:
                lines.append(f"  {em.note}")

        if self.strengths:
            lines.append("\n### Strengths (what you bring)")
            for s in self.strengths:
                lines.append(f"- {s}")

        if self.gaps:
            lines.append("\n### Gaps (what to address)")
            for g in self.gaps:
                roadmap = self.gap_roadmaps.get(g, "")
                if roadmap:
                    lines.append(f"- {g}  →  _{roadmap}_")
                else:
                    lines.append(f"- {g}")

        if self.skill_matches:
            lines.append("\n### Skill Matching Detail")
            lines.append("| Skill | Required | Matched | Type | Evidence |")
            lines.append("|-------|----------|---------|------|----------|")
            for m in self.skill_matches:
                req = "Required" if m.required else "Preferred"
                matched = "O" if m.matched else "X"
                lines.append(
                    f"| {m.skill} | {req} | {matched} | {m.match_type} | {m.user_evidence} |"
                )

        if self.strategy:
            lines.append("\n---\n")
            lines.append("## Application Strategy")
            lines.append(self.strategy)

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class JDMatcher:
    """Parse job descriptions and match against user profile."""

    def __init__(self, llm: BaseLLM | None = None):
        self.llm = llm or NoLLM()
        self._parser = JDParser()

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

        # 2. Structured parse
        parsed = self._parser.parse(raw_text, title=title, company=company)
        analysis.parsed = parsed
        analysis.required_skills = parsed.required_qualifications
        analysis.preferred_skills = parsed.preferred_qualifications
        analysis.responsibilities = parsed.responsibilities
        analysis.experience_years = parsed.experience_years_raw

        # 3. LLM enhancement (optional)
        if self.llm.is_available():
            self._llm_extract(analysis)

        # 4. Match against profile
        if profile:
            self._match_profile(analysis, profile)

        # 5. Generate strategy (LLM)
        if self.llm.is_available():
            self._generate_strategy(analysis, profile)

        return analysis

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def _fetch_jd(self, url: str) -> tuple[str, str, str]:
        """Fetch and extract text from a JD URL."""
        try:
            resp = httpx.get(
                url, timeout=15, follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HireKit)"},
            )
            soup = BeautifulSoup(resp.text, "lxml")

            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title else ""
            text = soup.get_text(separator="\n", strip=True)

            company = ""
            og_site = soup.find("meta", property="og:site_name")
            if og_site:
                company = og_site.get("content", "")

            return text[:8000], title, company
        except Exception:
            return "", "", ""

    # ------------------------------------------------------------------
    # LLM extraction
    # ------------------------------------------------------------------

    def _llm_extract(self, analysis: JDAnalysis) -> None:
        """Use LLM to fill gaps left by rule-based parser."""
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
            self._parse_llm_extraction(analysis, resp.text)

    def _parse_llm_extraction(self, analysis: JDAnalysis, text: str) -> None:
        """Parse LLM extraction response, merging with existing parsed data."""
        sections = re.split(r"\n(?=\d+\.)", text)
        for section in sections:
            items = re.findall(r"[-•]\s*(.+)", section)
            if "필수" in section or "자격요건" in section:
                # Only add items not already captured by rule-based parser
                existing = set(analysis.required_skills)
                for item in items:
                    if item not in existing:
                        analysis.required_skills.append(item)
            elif "우대" in section:
                existing = set(analysis.preferred_skills)
                for item in items:
                    if item not in existing:
                        analysis.preferred_skills.append(item)
            elif "담당" in section or "업무" in section:
                existing = set(analysis.responsibilities)
                for item in items:
                    if item not in existing:
                        analysis.responsibilities.append(item)

    # ------------------------------------------------------------------
    # Profile matching
    # ------------------------------------------------------------------

    def _match_profile(
        self, analysis: JDAnalysis, profile: dict[str, Any]
    ) -> None:
        """Match JD requirements against user profile using enhanced algorithm."""
        user_skills = self._collect_user_skills(profile)
        user_years = self._get_user_years(profile)

        # Experience match
        if analysis.parsed and analysis.parsed.experience_min_years > 0:
            em = ExperienceMatch(
                required_min=analysis.parsed.experience_min_years,
                required_max=analysis.parsed.experience_max_years,
                user_years=user_years,
            )
            em.meets_requirement = user_years >= em.required_min
            if not em.meets_requirement:
                gap = em.required_min - user_years
                em.note = f"{gap}년 경력 부족 — 프로젝트·오픈소스 기여로 보완 가능"
            elif em.required_max and user_years > em.required_max:
                em.note = "요구 연차 상한 초과 — 역할 적합성 어필 필요"
            analysis.experience_match = em

        # Tech-aware skill matching
        required_matched = 0
        total_required = 0

        # Use parsed tech lists if available, fall back to raw required_skills
        parsed = analysis.parsed
        required_tech = parsed.required_tech if parsed else []
        preferred_tech = parsed.preferred_tech if parsed else []

        # Match required tech
        for tech in required_tech:
            total_required += 1
            matched, match_type, evidence = self._match_skill(tech, user_skills, profile)
            if matched:
                required_matched += 1
            roadmap = "" if matched else _LEARNING_ROADMAP.get(tech, "")
            analysis.skill_matches.append(SkillMatch(
                skill=tech, required=True, matched=matched,
                match_type=match_type, user_evidence=evidence,
                learning_roadmap=roadmap,
            ))

        # Match required qualifications (non-tech lines)
        for qual in analysis.required_skills:
            qual_lower = qual.lower()
            # Skip if already covered by tech matching
            if any(m.skill in qual_lower for m in analysis.skill_matches if m.required):
                continue
            total_required += 1
            matched, match_type, evidence = self._match_skill(qual_lower, user_skills, profile)
            if matched:
                required_matched += 1
            analysis.skill_matches.append(SkillMatch(
                skill=qual, required=True, matched=matched,
                match_type=match_type, user_evidence=evidence,
            ))

        # Match preferred tech
        for tech in preferred_tech:
            matched, match_type, evidence = self._match_skill(tech, user_skills, profile)
            analysis.skill_matches.append(SkillMatch(
                skill=tech, required=False, matched=matched,
                match_type=match_type, user_evidence=evidence,
            ))

        # Calculate score
        analysis.match_score = self._calculate_score(
            analysis, required_matched, total_required, user_years
        )

        # Gaps and strengths
        analysis.gaps = [
            m.skill for m in analysis.skill_matches if m.required and not m.matched
        ]
        analysis.strengths = [
            m.skill for m in analysis.skill_matches if m.matched
        ]
        analysis.gap_roadmaps = {
            m.skill: m.learning_roadmap
            for m in analysis.skill_matches
            if not m.matched and m.learning_roadmap
        }

    def _collect_user_skills(self, profile: dict[str, Any]) -> set[str]:
        """Build normalized set of user skills from profile."""
        skills: set[str] = set()
        for category in ["technical", "domain", "soft"]:
            for s in profile.get("skills", {}).get(category, []):
                skills.add(normalize_tech(s.lower()))
                skills.add(s.lower())  # keep raw too
        for asset in profile.get("career_assets", []):
            raw = asset.get("asset", "").lower()
            skills.add(raw)
            skills.add(normalize_tech(raw))
        return skills

    def _get_user_years(self, profile: dict[str, Any]) -> int:
        """Extract years of experience from profile."""
        # Support 'experience_years' int or string field
        raw = profile.get("experience_years", profile.get("years_of_experience", 0))
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            m = re.search(r"\d+", raw)
            return int(m.group(0)) if m else 0
        return 0

    def _match_skill(
        self,
        skill: str,
        user_skills: set[str],
        profile: dict[str, Any],
    ) -> tuple[bool, str, str]:
        """Return (matched, match_type, evidence) for a skill.

        Match types: "exact", "similar", "partial", ""
        """
        skill_norm = normalize_tech(skill.lower())

        # 1. Exact / canonical match
        if skill_norm in user_skills or skill.lower() in user_skills:
            evidence = self._find_evidence(skill_norm, profile)
            return True, "exact", evidence

        # 2. Similar tech group match (e.g. React matches Vue in Frontend Framework)
        for user_skill in user_skills:
            if techs_are_similar(skill_norm, user_skill):
                evidence = self._find_evidence(user_skill, profile)
                return True, "similar", f"유사 기술: {user_skill} → {skill_norm}"

        # 3. Partial text match (for non-tech qualifications)
        for user_skill in user_skills:
            if (len(user_skill) >= 3 and user_skill in skill.lower()) or \
               (len(skill_norm) >= 3 and skill_norm in user_skill):
                evidence = self._find_evidence(user_skill, profile)
                return True, "partial", evidence

        return False, "", ""

    def _find_evidence(self, skill: str, profile: dict[str, Any]) -> str:
        """Find career asset evidence for a skill."""
        for asset in profile.get("career_assets", []):
            asset_name = normalize_tech(asset.get("asset", "").lower())
            if asset_name == skill or skill in asset_name or asset_name in skill:
                return asset.get("source", "")
        return ""

    def _calculate_score(
        self,
        analysis: JDAnalysis,
        required_matched: int,
        total_required: int,
        user_years: int,
    ) -> float:
        """Calculate weighted match score (0-100).

        Weights:
        - Required skills: 70%
        - Preferred skills: 20%
        - Experience seniority: 10%
        """
        # Required ratio
        required_ratio = required_matched / total_required if total_required > 0 else 0.5

        # Preferred ratio
        preferred_matched = sum(
            1 for m in analysis.skill_matches if not m.required and m.matched
        )
        preferred_total = sum(1 for m in analysis.skill_matches if not m.required)
        preferred_ratio = preferred_matched / preferred_total if preferred_total > 0 else 0.0

        # Experience score
        exp_score = 1.0
        if analysis.experience_match:
            em = analysis.experience_match
            if not em.meets_requirement:
                gap = em.required_min - user_years
                # Penalize proportionally; max 40% penalty
                penalty = min(gap * 0.1, 0.4)
                exp_score = 1.0 - penalty
            elif em.required_max and user_years > em.required_max:
                exp_score = 0.9  # slight penalty for over-qualification

        raw = (required_ratio * 0.7 + preferred_ratio * 0.2 + exp_score * 0.1) * 100
        return round(min(raw, 100.0), 2)

    # ------------------------------------------------------------------
    # LLM strategy generation
    # ------------------------------------------------------------------

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
