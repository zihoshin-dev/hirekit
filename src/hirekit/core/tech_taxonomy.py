"""Technology taxonomy — categories, similarity groups, and seniority level mapping."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Similarity groups: techs that are interchangeable / closely related
# Keys are canonical names; values are aliases / similar technologies.
# ---------------------------------------------------------------------------

TECH_SIMILARITY_GROUPS: dict[str, list[str]] = {
    # Frontend frameworks
    "react": ["react.js", "reactjs", "react native"],
    "vue": ["vue.js", "vuejs", "vue 3", "nuxt", "nuxt.js"],
    "angular": ["angularjs", "angular 2", "angular cli"],
    "svelte": ["sveltekit"],
    "next.js": ["nextjs", "next js"],
    # Backend frameworks
    "django": ["drf", "django rest framework"],
    "fastapi": ["starlette"],
    "flask": [],
    "spring": ["spring boot", "springboot", "spring framework"],
    "express": ["express.js", "expressjs"],
    "nestjs": ["nest.js"],
    "rails": ["ruby on rails", "ror"],
    "laravel": [],
    # Languages
    "python": ["python3", "python 3"],
    "java": ["java 8", "java 11", "java 17", "java 21"],
    "javascript": ["js", "es6", "es2015", "ecmascript"],
    "typescript": ["ts"],
    "kotlin": [],
    "swift": [],
    "go": ["golang"],
    "rust": [],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp", ".net"],
    "scala": [],
    "ruby": [],
    "php": [],
    "r": ["r language"],
    # Databases
    "postgresql": ["postgres", "pg"],
    "mysql": ["mariadb"],
    "mongodb": ["mongo"],
    "redis": [],
    "elasticsearch": ["elastic", "es", "opensearch"],
    "cassandra": [],
    "dynamodb": [],
    "bigquery": [],
    "snowflake": [],
    # Cloud
    "aws": ["amazon web services", "amazon aws"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    # DevOps / Infra
    "docker": ["containerization"],
    "kubernetes": ["k8s", "kube"],
    "terraform": [],
    "ansible": [],
    "jenkins": [],
    "github actions": ["github ci", "gh actions"],
    "gitlab ci": ["gitlab ci/cd"],
    "argocd": ["argo cd"],
    "graphql": [],
    "grpc": ["g rpc"],
    # Data / ML
    "pytorch": ["torch"],
    "tensorflow": ["tf", "keras"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "pandas": [],
    "spark": ["apache spark", "pyspark"],
    "airflow": ["apache airflow"],
    "kafka": ["apache kafka"],
    "dbt": [],
    "mlflow": [],
    "llm": ["large language model", "large language models"],
    "machine learning": ["ml"],
    # Mobile
    "react native": ["rn"],
    "flutter": [],
    "android": [],
    "ios": [],
    # Testing
    "pytest": [],
    "jest": [],
    "cypress": [],
    "selenium": [],
    "junit": [],
}

# Reverse map: alias → canonical name
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in TECH_SIMILARITY_GROUPS.items():
    _ALIAS_TO_CANONICAL[_canonical] = _canonical
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canonical


# ---------------------------------------------------------------------------
# Category taxonomy
# ---------------------------------------------------------------------------

TECH_CATEGORIES: dict[str, list[str]] = {
    "Frontend": [
        "react",
        "vue",
        "angular",
        "svelte",
        "javascript",
        "typescript",
        "html",
        "css",
        "sass",
        "tailwind",
        "webpack",
        "vite",
        "next.js",
        "nextjs",
    ],
    "Backend": [
        "python",
        "java",
        "go",
        "ruby",
        "php",
        "scala",
        "c#",
        "kotlin",
        "django",
        "fastapi",
        "flask",
        "spring",
        "express",
        "nestjs",
        "rails",
        "laravel",
    ],
    "Database": [
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "cassandra",
        "dynamodb",
        "bigquery",
        "snowflake",
        "sql",
        "nosql",
    ],
    "DevOps": [
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "jenkins",
        "github actions",
        "gitlab ci",
        "argocd",
        "ci/cd",
        "linux",
        "bash",
        "shell",
    ],
    "Cloud": ["aws", "gcp", "azure", "s3", "ec2", "lambda"],
    "Data": [
        "spark",
        "airflow",
        "kafka",
        "dbt",
        "pandas",
        "etl",
        "data pipeline",
        "warehouse",
    ],
    "ML/AI": [
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "mlflow",
        "llm",
        "nlp",
        "computer vision",
        "deep learning",
        "machine learning",
    ],
    "Mobile": ["react native", "flutter", "android", "ios", "swift", "kotlin"],
    "Testing": ["pytest", "jest", "cypress", "selenium", "junit", "tdd", "bdd"],
}

# Reverse map: tech → category
_TECH_TO_CATEGORY: dict[str, str] = {}
for _cat, _techs in TECH_CATEGORIES.items():
    for _t in _techs:
        _TECH_TO_CATEGORY[_t.lower()] = _cat

_TEXT_EXTRACT_CANONICAL: dict[str, str] = dict(_ALIAS_TO_CANONICAL)
for _techs in TECH_CATEGORIES.values():
    for _tech in _techs:
        _tech_key = _tech.lower()
        if _tech_key not in _TEXT_EXTRACT_CANONICAL:
            _TEXT_EXTRACT_CANONICAL[_tech_key] = _tech_key

_AMBIGUOUS_TEXT_TECHS = {"go", "r"}
_TEXT_EXTRACT_PATTERNS: list[tuple[str, re.Pattern[str], str]] = []
for _term, _canonical in sorted(
    _TEXT_EXTRACT_CANONICAL.items(),
    key=lambda item: (-len(item[0]), item[0]),
):
    if _term in _AMBIGUOUS_TEXT_TECHS:
        continue
    _TEXT_EXTRACT_PATTERNS.append(
        (
            _term,
            re.compile(rf"(?<![a-z0-9]){re.escape(_term)}(?![a-z0-9])", re.IGNORECASE),
            _canonical,
        ),
    )

_ROLE_ADJACENT_CATEGORIES = {"Cloud", "DevOps", "Testing"}

_AUTHORITY_WEIGHTS = {
    "official": 1.0,
    "company_operated": 0.8,
    "credible_reporting": 0.7,
    "secondary_research": 0.55,
    "community": 0.4,
    "generated": 0.2,
}

_WORK_PATTERN_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    (
        "data_platform",
        "데이터 파이프라인/스트리밍 운영",
        (
            "data pipeline",
            "데이터 파이프라인",
            "streaming",
            "stream",
            "spark",
            "airflow",
            "etl",
            "warehouse",
            "real-time data",
            "실시간 데이터",
        ),
    ),
    (
        "platform_infrastructure",
        "플랫폼/인프라 운영",
        (
            "kubernetes",
            "k8s",
            "docker",
            "terraform",
            "sre",
            "observability",
            "ci/cd",
            "github actions",
            "argo cd",
            "deployment",
            "배포",
            "인프라",
            "플랫폼 운영",
            "운영 자동화",
        ),
    ),
    (
        "payments_systems",
        "결제/정산 시스템",
        (
            "payment",
            "payments",
            "settlement",
            "결제",
            "정산",
            "송금",
            "wallet",
            "fraud",
        ),
    ),
    (
        "ml_platform",
        "ML/LLM 시스템",
        (
            "llm",
            "rag",
            "mlops",
            "machine learning",
            "머신러닝",
            "딥러닝",
            "model serving",
            "inference",
            "gpt",
            "transformer",
        ),
    ),
    (
        "frontend_product",
        "프론트엔드/사용자 경험",
        (
            "frontend",
            "react",
            "typescript",
            "design system",
            "web app",
            "ui",
            "ux",
            "프론트",
        ),
    ),
    (
        "mobile_product",
        "모바일 제품 개발",
        (
            "android",
            "ios",
            "flutter",
            "react native",
            "mobile",
            "앱",
        ),
    ),
    (
        "backend_service",
        "백엔드/API 서비스 운영",
        (
            "backend",
            "api",
            "microservice",
            "msa",
            "distributed system",
            "분산 시스템",
            "server",
            "서버",
        ),
    ),
]


ROLE_FAMILIES: dict[str, set[str]] = {
    "backend": {"backend", "백엔드", "server", "서버", "be", "api"},
    "frontend": {"frontend", "프론트", "fe", "ui", "web"},
    "fullstack": {"fullstack", "풀스택", "full-stack"},
    "data": {"data", "데이터", "analytics", "analyst", "data engineer", "data analyst"},
    "ml": {"ml", "machine learning", "ai", "머신러닝", "ml engineer"},
    "devops": {"devops", "sre", "infra", "인프라", "platform"},
    "pm": {"pm", "product manager", "기획", "po", "product owner", "program manager"},
    "designer": {"designer", "design", "ux", "uiux", "product designer"},
    "mobile": {"mobile", "android", "ios", "앱"},
    "security": {"security", "보안"},
}

ADJACENT_ROLE_FAMILIES: dict[str, set[str]] = {
    "backend": {"fullstack", "devops", "data"},
    "frontend": {"fullstack", "designer"},
    "fullstack": {"backend", "frontend", "devops"},
    "data": {"backend", "ml", "pm"},
    "ml": {"data", "backend"},
    "devops": {"backend", "fullstack", "security"},
    "pm": {"data", "designer"},
    "designer": {"frontend", "pm"},
    "mobile": {"frontend", "backend"},
    "security": {"devops", "backend"},
}


# ---------------------------------------------------------------------------
# Seniority levels
# ---------------------------------------------------------------------------


@dataclass
class SeniorityLevel:
    name: str
    min_years: int
    max_years: int | None  # None = no upper bound
    label_kr: str
    label_en: str


SENIORITY_LEVELS: list[SeniorityLevel] = [
    SeniorityLevel("junior", min_years=0, max_years=3, label_kr="주니어", label_en="Junior"),
    SeniorityLevel("mid", min_years=3, max_years=7, label_kr="미드레벨", label_en="Mid-level"),
    SeniorityLevel("senior", min_years=7, max_years=None, label_kr="시니어", label_en="Senior"),
]

# Korean keywords that indicate seniority
_SENIORITY_KR_PATTERNS: dict[str, str] = {
    "주니어": "junior",
    "신입": "junior",
    "경력 1": "junior",
    "경력 2": "junior",
    "경력 3": "junior",
    "미드": "mid",
    "중급": "mid",
    "경력 4": "mid",
    "경력 5": "mid",
    "경력 6": "mid",
    "시니어": "senior",
    "고급": "senior",
    "수석": "senior",
    "리드": "senior",
    "lead": "senior",
    "principal": "senior",
    "staff": "senior",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_tech(tech: str) -> str:
    """Return canonical tech name, lower-cased. Unknown techs pass through."""
    key = tech.strip().lower()
    return _ALIAS_TO_CANONICAL.get(key, key)


def get_category(tech: str) -> str | None:
    """Return category name for a tech, or None if unknown."""
    canonical = normalize_tech(tech)
    return _TECH_TO_CATEGORY.get(canonical)


def techs_are_similar(a: str, b: str) -> bool:
    """Return True if two tech names belong to the same canonical group."""
    return normalize_tech(a) == normalize_tech(b)


def get_similar_group(tech: str) -> list[str]:
    """Return all known aliases for a tech (including itself)."""
    canonical = normalize_tech(tech)
    if canonical not in TECH_SIMILARITY_GROUPS:
        return [canonical]
    return [canonical] + TECH_SIMILARITY_GROUPS[canonical]


def is_role_adjacent_tech(tech: str) -> bool:
    category = get_category(tech)
    return category in _ROLE_ADJACENT_CATEGORIES


def build_stack_signal(
    tech: str,
    *,
    source_name: str,
    source_authority: str,
    evidence: str,
    confidence: float = 0.6,
    signal_type: str = "mention",
) -> dict[str, Any]:
    canonical = normalize_tech(tech)
    return {
        "tech": canonical,
        "category": get_category(canonical),
        "source_name": source_name,
        "source_authority": source_authority,
        "evidence": evidence.strip(),
        "confidence": round(max(0.0, min(confidence, 0.95)), 2),
        "signal_type": signal_type,
        "bucket": "adjacent" if is_role_adjacent_tech(canonical) else "core",
        "trust_label": "supporting",
    }


def extract_stack_signals(
    texts: list[str],
    *,
    source_name: str,
    source_authority: str,
    signal_type: str = "mention",
    base_confidence: float = 0.62,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for text in texts:
        if not text:
            continue
        for tech, matched in _detect_tech_mentions(text):
            signals.append(
                build_stack_signal(
                    tech,
                    source_name=source_name,
                    source_authority=source_authority,
                    evidence=text,
                    confidence=base_confidence + (0.04 if matched == tech else 0.0),
                    signal_type=signal_type,
                ),
            )
    return _dedupe_signals(signals, key="tech")


def build_stack_reality(signals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {"confirmed": [], "likely": [], "adjacent": []}
    grouped: dict[str, list[dict[str, Any]]] = {}

    for signal in signals:
        tech = normalize_tech(str(signal.get("tech", "")).strip())
        if not tech:
            continue
        normalized = dict(signal)
        normalized["tech"] = tech
        normalized.setdefault("category", get_category(tech))
        normalized.setdefault("source_name", "unknown")
        normalized.setdefault("source_authority", "secondary_research")
        normalized.setdefault("signal_type", "mention")
        normalized.setdefault("bucket", "adjacent" if is_role_adjacent_tech(tech) else "core")
        normalized.setdefault("evidence", tech)
        normalized.setdefault("confidence", 0.6)
        grouped.setdefault(tech, []).append(normalized)

    for tech, group in grouped.items():
        unique_sources = sorted({str(item.get("source_name", "unknown")) for item in group})
        unique_authorities = sorted({str(item.get("source_authority", "secondary_research")) for item in group})
        evidence = _unique_nonempty(str(item.get("evidence", "")).strip() for item in group)[:3]
        signal_types = sorted({str(item.get("signal_type", "mention")) for item in group})
        avg_confidence = sum(float(item.get("confidence", 0.6)) for item in group) / len(group)
        authority_total = sum(
            max(
                _AUTHORITY_WEIGHTS.get(str(item.get("source_authority", "secondary_research")), 0.55)
                for item in group
                if str(item.get("source_name", "unknown")) == source_name
            )
            for source_name in unique_sources
        )
        adjacent = all(str(item.get("bucket", "core")) == "adjacent" for item in group)

        if adjacent:
            boundary = "adjacent"
            trust_label = "supporting"
            confidence = min(0.65, avg_confidence)
        elif len(unique_sources) >= 2 and authority_total >= 1.35:
            boundary = "confirmed"
            trust_label = "verified"
            confidence = min(0.95, avg_confidence + 0.12)
        else:
            boundary = "likely"
            trust_label = "supporting"
            confidence = min(0.79, avg_confidence + 0.05)

        buckets[boundary].append(
            {
                "tech": tech,
                "category": get_category(tech),
                "confidence": round(confidence, 2),
                "trust_label": trust_label,
                "source_count": len(unique_sources),
                "signal_count": len(group),
                "sources": unique_sources,
                "source_authority": unique_authorities,
                "signal_types": signal_types,
                "evidence": evidence,
            },
        )

    for key in buckets:
        buckets[key].sort(key=lambda item: (-float(item["confidence"]), item["tech"]))
    return buckets


def extract_work_signals(
    texts: list[str],
    *,
    source_name: str,
    source_authority: str,
    base_confidence: float = 0.58,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for text in texts:
        normalized_text = text.strip()
        if not normalized_text:
            continue
        lowered = normalized_text.lower()
        for pattern, label, keywords in _WORK_PATTERN_RULES:
            matched = [keyword for keyword in keywords if keyword.lower() in lowered]
            if not matched:
                continue
            confidence = min(0.8, base_confidence + (0.04 * (len(matched) - 1)))
            signals.append(
                {
                    "pattern": pattern,
                    "label": label,
                    "source_name": source_name,
                    "source_authority": source_authority,
                    "evidence": normalized_text,
                    "matched_keywords": matched,
                    "confidence": round(confidence, 2),
                    "trust_label": "supporting",
                },
            )

    return _dedupe_signals(signals, key="pattern")


def build_actual_work_profile(signals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {"confirmed": [], "likely": []}
    grouped: dict[str, list[dict[str, Any]]] = {}

    for signal in signals:
        pattern = str(signal.get("pattern", "")).strip()
        if not pattern:
            continue
        grouped.setdefault(pattern, []).append(dict(signal))

    for pattern, group in grouped.items():
        unique_sources = sorted({str(item.get("source_name", "unknown")) for item in group})
        unique_authorities = sorted({str(item.get("source_authority", "secondary_research")) for item in group})
        evidence = _unique_nonempty(str(item.get("evidence", "")).strip() for item in group)[:3]
        avg_confidence = sum(float(item.get("confidence", 0.58)) for item in group) / len(group)
        authority_total = sum(
            max(
                _AUTHORITY_WEIGHTS.get(str(item.get("source_authority", "secondary_research")), 0.55)
                for item in group
                if str(item.get("source_name", "unknown")) == source_name
            )
            for source_name in unique_sources
        )
        boundary = "confirmed" if len(unique_sources) >= 2 and authority_total >= 1.35 else "likely"

        buckets[boundary].append(
            {
                "pattern": pattern,
                "label": str(group[0].get("label", pattern)),
                "confidence": round(min(0.92 if boundary == "confirmed" else 0.78, avg_confidence + 0.05), 2),
                "trust_label": "verified" if boundary == "confirmed" else "supporting",
                "source_count": len(unique_sources),
                "sources": unique_sources,
                "source_authority": unique_authorities,
                "matched_keywords": _unique_nonempty(
                    keyword
                    for item in group
                    for keyword in item.get("matched_keywords", [])
                    if isinstance(keyword, str)
                )[:6],
                "evidence": evidence,
            },
        )

    for key in buckets:
        buckets[key].sort(key=lambda item: (-float(item["confidence"]), item["pattern"]))
    return buckets


def _detect_tech_mentions(text: str) -> list[tuple[str, str]]:
    lowered = text.lower()
    spans: list[tuple[int, int]] = []
    matches: list[tuple[int, str, str]] = []

    for term, pattern, canonical in _TEXT_EXTRACT_PATTERNS:
        match = pattern.search(lowered)
        if match is None:
            continue
        span = (match.start(), match.end())
        if any(_spans_overlap(span, existing) for existing in spans):
            continue
        spans.append(span)
        matches.append((match.start(), canonical, term))

    matches.sort(key=lambda item: (item[0], item[1]))
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for _, canonical, term in matches:
        if canonical in seen:
            continue
        seen.add(canonical)
        result.append((canonical, term))
    return result


def _spans_overlap(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] < second[1] and second[0] < first[1]


def _unique_nonempty(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def _dedupe_signals(signals: list[dict[str, Any]], *, key: str) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        primary = str(signal.get(key, "")).strip()
        evidence = str(signal.get("evidence", "")).strip()
        dedupe_key = (primary, evidence)
        if not primary or dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(signal)
    return deduped


def classify_experience(years: int) -> SeniorityLevel:
    """Map years of experience to a SeniorityLevel."""
    for level in reversed(SENIORITY_LEVELS):
        if years >= level.min_years:
            return level
    return SENIORITY_LEVELS[0]


def normalize_role_family(role: str) -> str | None:
    normalized = role.strip().lower()
    for family, keywords in ROLE_FAMILIES.items():
        if any(keyword in normalized for keyword in keywords):
            return family
    return None


def role_similarity_score(current_role: str, target_role: str) -> float:
    current_family = normalize_role_family(current_role)
    target_family = normalize_role_family(target_role)

    if not current_family or not target_family:
        return 0.4
    if current_family == target_family:
        return 1.0
    if target_family in ADJACENT_ROLE_FAMILIES.get(current_family, set()):
        return 0.75
    return 0.4


def parse_experience_requirement(text: str) -> tuple[int, int | None]:
    """Parse a raw experience string like '3년 이상', '5~7년' into (min, max) years.

    Returns (min_years, max_years) where max_years is None for open-ended.
    """
    import re

    text = text.strip()

    # "3~5년" or "3-5년"
    range_match = re.search(r"(\d+)\s*[~\-]\s*(\d+)\s*년", text)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))

    # "3+ years" or "3 + years"
    plus_match = re.search(r"(\d+)\s*\+\s*years?", text)
    if plus_match:
        return int(plus_match.group(1)), None
    kr_min_match = re.search(r"(\d+)\s*년\s*(?:이상|이상의)", text)
    if kr_min_match:
        return int(kr_min_match.group(1)), None

    # Plain "3년" → treat as minimum
    plain_match = re.search(r"(\d+)\s*년", text)
    if plain_match:
        return int(plain_match.group(1)), None

    return 0, None
