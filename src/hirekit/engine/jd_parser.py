"""Structured JD parser — extracts requirements, tech stack, and metadata from raw JD text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from hirekit.core.tech_taxonomy import TECH_SIMILARITY_GROUPS, get_category, normalize_tech

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ParsedJD:
    """Fully structured representation of a parsed job description."""

    # Basic metadata
    title: str = ""
    company: str = ""
    team: str = ""

    # Sections
    required_qualifications: list[str] = field(default_factory=list)
    preferred_qualifications: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)

    # Tech stack (normalized canonical names)
    required_tech: list[str] = field(default_factory=list)
    preferred_tech: list[str] = field(default_factory=list)
    tech_stack_lines: list[str] = field(default_factory=list)

    # Experience
    experience_years_raw: str = ""  # raw string e.g. "3년 이상"
    experience_min_years: int = 0
    experience_max_years: int | None = None

    # Structured requirements
    tech_categories: dict[str, list[str]] = field(default_factory=dict)  # category → [tech]
    must_have_expectations: list[str] = field(default_factory=list)
    inferred_expectations: list[str] = field(default_factory=list)
    unknown_expectations: list[str] = field(default_factory=list)

    def all_required_tech(self) -> list[str]:
        return list(dict.fromkeys(self.required_tech))  # deduplicated, order-preserving

    def all_preferred_tech(self) -> list[str]:
        return list(dict.fromkeys(self.preferred_tech))


# ---------------------------------------------------------------------------
# Section header patterns
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "required",
        [
            r"자격\s*요건",
            r"필수\s*요건",
            r"지원\s*자격",
            r"필수\s*자격",
            r"requirements?",
            r"qualifications?",
            r"must\s*have",
            r"필수\s*조건",
            r"기본\s*자격",
        ],
    ),
    (
        "preferred",
        [
            r"우대\s*사항",
            r"우대\s*조건",
            r"우대\s*자격",
            r"preferred",
            r"nice[\s\-]to[\s\-]have",
            r"bonus",
            r"플러스",
            r"우대",
            r"가점",
        ],
    ),
    (
        "responsibilities",
        [
            r"담당\s*업무",
            r"주요\s*업무",
            r"업무\s*내용",
            r"수행\s*업무",
            r"이런\s*일",
            r"하는\s*일",
            r"역할",
            r"responsibilities?",
            r"what\s*you.ll\s*do",
            r"your\s*role",
            r"job\s*duties",
            r"duties",
        ],
    ),
    (
        "tech_stack",
        [
            r"기술\s*스택",
            r"사용\s*기술",
            r"기술\s*환경",
            r"개발\s*환경",
            r"tech\s*stack",
            r"technologies?",
            r"tools?\s*&\s*technologies?",
        ],
    ),
    (
        "team",
        [
            r"팀\s*소개",
            r"팀\s*정보",
            r"조직\s*소개",
            r"우리\s*팀",
            r"about\s*the\s*team",
            r"our\s*team",
        ],
    ),
]

# All known tech names for extraction (canonical + aliases)
_ALL_TECH_TERMS: set[str] = set()
for _canon, _aliases in TECH_SIMILARITY_GROUPS.items():
    _ALL_TECH_TERMS.add(_canon)
    _ALL_TECH_TERMS.update(a.lower() for a in _aliases)

# Extra common techs not in similarity groups
_EXTRA_TECHS = {
    "html",
    "css",
    "sass",
    "scss",
    "less",
    "tailwind",
    "tailwindcss",
    "webpack",
    "vite",
    "babel",
    "eslint",
    "prettier",
    "next.js",
    "nextjs",
    "nuxt.js",
    "nuxtjs",
    "graphql",
    "rest",
    "restful",
    "grpc",
    "websocket",
    "git",
    "github",
    "gitlab",
    "bitbucket",
    "nginx",
    "apache",
    "linux",
    "ubuntu",
    "centos",
    "bash",
    "shell",
    "zsh",
    "sql",
    "nosql",
    "etl",
    "dbt",
    "jira",
    "confluence",
    "notion",
    "figma",
    "sketch",
    "postman",
    "swagger",
    "sentry",
    "datadog",
    "grafana",
    "prometheus",
    "rabbitmq",
    "celery",
}
_ALL_TECH_TERMS.update(_EXTRA_TECHS)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class JDParser:
    """Parse a raw JD text into a structured ParsedJD object.

    Works rule-based with no LLM dependency. Supports Korean and English JDs.
    """

    def parse(self, text: str, title: str = "", company: str = "") -> ParsedJD:
        """Parse raw JD text and return structured ParsedJD."""
        jd = ParsedJD(title=title, company=company)
        if not text.strip():
            return jd

        lines = [l.rstrip() for l in text.splitlines()]
        self._parse_sections(jd, lines)
        self._extract_experience(jd, text)
        self._extract_tech_stack(jd)
        self._build_tech_categories(jd)
        self._build_role_expectations(jd)
        return jd

    # ------------------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------------------

    def _parse_sections(self, jd: ParsedJD, lines: list[str]) -> None:
        current_section: str | None = None
        section_buffers: dict[str, list[str]] = {
            "required": [],
            "preferred": [],
            "responsibilities": [],
            "tech_stack": [],
            "team": [],
        }

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            detected = self._detect_section(stripped)
            if detected:
                current_section = detected
                continue

            if current_section:
                cleaned = self._clean_bullet(stripped)
                if cleaned and len(cleaned) >= 2:
                    section_buffers[current_section].append(cleaned)

        jd.required_qualifications = section_buffers["required"]
        jd.preferred_qualifications = section_buffers["preferred"]
        jd.responsibilities = section_buffers["responsibilities"]

        # tech_stack section items merge into required_tech later
        jd.tech_stack_lines = section_buffers["tech_stack"]

    def _detect_section(self, line: str) -> str | None:
        """Return section key if this line is a section header, else None."""
        lower = line.lower()
        # Strip common decoration: brackets, colons, bullets
        cleaned = re.sub(r"^[#\[\]▶■●▪◆\-\*\s]+", "", lower)
        cleaned = re.sub(r"[\[\]:：]+", "", cleaned).strip()

        for section_key, patterns in _SECTION_PATTERNS:
            for pat in patterns:
                if re.search(pat, cleaned):
                    return section_key
        return None

    @staticmethod
    def _clean_bullet(line: str) -> str:
        """Remove leading bullet/numbering characters."""
        # Remove bullets, numbers, dashes, dots
        cleaned = re.sub(r"^[\-\*•·‣▸▹◦⦿⚫●▪■□\d]+[.):\s]*", "", line)
        return cleaned.strip()

    # ------------------------------------------------------------------
    # Experience extraction
    # ------------------------------------------------------------------

    def _extract_experience(self, jd: ParsedJD, text: str) -> None:
        from hirekit.core.tech_taxonomy import parse_experience_requirement

        # Patterns: "3년 이상", "3~5년", "3-5년 경력", "3+ years"
        patterns = [
            r"\d+\s*[~\-]\s*\d+\s*년",  # range KR
            r"\d+\s*년\s*(?:이상|이상의)",  # min KR
            r"\d+\s*\+?\s*years?\s*(?:of\s*experience)?",  # EN
            r"경력\s*\d+\s*년",  # "경력 N년"
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                jd.experience_years_raw = m.group(0).strip()
                min_y, max_y = parse_experience_requirement(jd.experience_years_raw)
                jd.experience_min_years = min_y
                jd.experience_max_years = max_y
                break

    # ------------------------------------------------------------------
    # Tech stack extraction
    # ------------------------------------------------------------------

    def _extract_tech_stack(self, jd: ParsedJD) -> None:
        """Scan qualification lines + tech_stack section for known tech terms."""

        def _extract_from_lines(lines: list[str]) -> list[str]:
            found: list[str] = []
            for line in lines:
                found.extend(self._find_techs_in_line(line))
            return found

        required_techs = _extract_from_lines(jd.required_qualifications)
        preferred_techs = _extract_from_lines(jd.preferred_qualifications)

        # Deduplicate preferred first (order-preserving)
        preferred_set = set(dict.fromkeys(preferred_techs))

        # Tech stack section → treat as required only if not already in preferred
        for tech in _extract_from_lines(jd.tech_stack_lines):
            if tech not in preferred_set:
                required_techs.append(tech)

        # Deduplicate required, then exclude anything already in preferred
        jd.required_tech = [t for t in dict.fromkeys(required_techs) if t not in preferred_set]
        jd.preferred_tech = list(dict.fromkeys(preferred_techs))

    def _find_techs_in_line(self, line: str) -> list[str]:
        """Return normalized tech names mentioned in a single line."""
        found: list[str] = []
        lower = line.lower()

        # Try to match each known tech term (longest first to avoid partial matches)
        sorted_terms = sorted(_ALL_TECH_TERMS, key=len, reverse=True)
        matched_spans: list[tuple[int, int]] = []

        for term in sorted_terms:
            # Word-boundary aware search
            pattern = r"(?<![a-z0-9\-\.])" + re.escape(term) + r"(?![a-z0-9\-\.])"
            for m in re.finditer(pattern, lower):
                start, end = m.start(), m.end()
                # Ensure not already covered by a longer match
                if not any(s <= start and end <= e for s, e in matched_spans):
                    matched_spans.append((start, end))
                    found.append(normalize_tech(term))

        return found

    # ------------------------------------------------------------------
    # Category grouping
    # ------------------------------------------------------------------

    def _build_tech_categories(self, jd: ParsedJD) -> None:
        """Group extracted techs by category."""
        categories: dict[str, list[str]] = {}
        for tech in jd.required_tech + jd.preferred_tech:
            cat = get_category(tech) or "Other"
            categories.setdefault(cat, [])
            if tech not in categories[cat]:
                categories[cat].append(tech)
        jd.tech_categories = categories

    def _build_role_expectations(self, jd: ParsedJD) -> None:
        must_have = list(dict.fromkeys(jd.required_qualifications))
        if jd.experience_years_raw:
            must_have.append(f"경력 요구: {jd.experience_years_raw}")
        if jd.required_tech:
            must_have.append("필수 기술: " + ", ".join(jd.required_tech[:6]))

        inferred = list(dict.fromkeys(jd.responsibilities))
        if jd.preferred_tech:
            inferred.append("우대 기술: " + ", ".join(jd.preferred_tech[:6]))

        unknown: list[str] = []
        if not jd.required_qualifications:
            unknown.append("필수 역량 기준 확인 필요")
        if not jd.responsibilities:
            unknown.append("실제 업무 범위 확인 필요")

        jd.must_have_expectations = must_have
        jd.inferred_expectations = inferred
        jd.unknown_expectations = unknown
