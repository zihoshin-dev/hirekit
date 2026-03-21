"""Technology taxonomy — categories, similarity groups, and seniority level mapping."""

from __future__ import annotations

from dataclasses import dataclass

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
        "react", "vue", "angular", "svelte",
        "javascript", "typescript",
        "html", "css", "sass", "tailwind", "webpack", "vite", "next.js", "nextjs",
    ],
    "Backend": [
        "python", "java", "go", "ruby", "php", "scala", "c#", "kotlin",
        "django", "fastapi", "flask", "spring", "express", "nestjs", "rails", "laravel",
    ],
    "Database": [
        "postgresql", "mysql", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "bigquery", "snowflake",
        "sql", "nosql",
    ],
    "DevOps": [
        "docker", "kubernetes", "terraform", "ansible",
        "jenkins", "github actions", "gitlab ci", "argocd",
        "ci/cd", "linux", "bash", "shell",
    ],
    "Cloud": ["aws", "gcp", "azure", "s3", "ec2", "lambda"],
    "Data": [
        "spark", "airflow", "kafka", "dbt", "pandas",
        "etl", "data pipeline", "warehouse",
    ],
    "ML/AI": [
        "pytorch", "tensorflow", "scikit-learn", "mlflow",
        "llm", "nlp", "computer vision", "deep learning", "machine learning",
    ],
    "Mobile": ["react native", "flutter", "android", "ios", "swift", "kotlin"],
    "Testing": ["pytest", "jest", "cypress", "selenium", "junit", "tdd", "bdd"],
}

# Reverse map: tech → category
_TECH_TO_CATEGORY: dict[str, str] = {}
for _cat, _techs in TECH_CATEGORIES.items():
    for _t in _techs:
        _TECH_TO_CATEGORY[_t.lower()] = _cat


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
    SeniorityLevel("junior",  min_years=0, max_years=3,    label_kr="주니어",  label_en="Junior"),
    SeniorityLevel("mid",     min_years=3, max_years=7,    label_kr="미드레벨", label_en="Mid-level"),
    SeniorityLevel("senior",  min_years=7, max_years=None, label_kr="시니어",  label_en="Senior"),
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


def classify_experience(years: int) -> SeniorityLevel:
    """Map years of experience to a SeniorityLevel."""
    for level in reversed(SENIORITY_LEVELS):
        if years >= level.min_years:
            return level
    return SENIORITY_LEVELS[0]


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
