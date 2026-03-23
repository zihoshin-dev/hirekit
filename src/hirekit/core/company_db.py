"""Dynamic company data loader from demo JSON files.

Loads company information from docs/demo/data/meta.json (and individual
company JSON files as a secondary source). Provides a unified interface
for the engine modules so they don't maintain parallel hard-coded dicts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Default data directory
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = (
    Path(__file__).parent.parent.parent.parent  # project root
    / "docs" / "demo" / "data"
)


def _normalize(name: str) -> str:
    """Normalize a company name for alias lookup.

    Strips legal suffixes, punctuation, and spaces; lowercases.
    Mirrors the logic in company_resolver._normalize_company_token.
    """
    normalized = name.strip().lower()
    for token in (
        "(주)",
        "주식회사",
        "유한회사",
        "유한책임회사",
        ".",
        ",",
        "(",
        ")",
        "-",
        "_",
        " ",
    ):
        normalized = normalized.replace(token, "")
    return normalized


def _extract_primary_name(raw_name: str) -> str:
    """Extract the primary brand name from composite names like '토스 (비바리퍼블리카)'."""
    # Take the part before ' (' if present
    match = re.match(r"^(.+?)\s*\(", raw_name)
    if match:
        return match.group(1).strip()
    return raw_name.strip()


def _size_label_to_key(size: str) -> str:
    """Map Korean size label to comparator size key."""
    mapping = {
        "스타트업": "startup",
        "중소기업": "startup",
        "중견기업": "mid",
        "유니콘": "mid",
        "대기업": "large",
        "글로벌": "enterprise",
        "외국계": "enterprise",
    }
    size_lower = size.lower()
    for label, key in mapping.items():
        if label in size_lower:
            return key
    return "mid"


def _industry_to_key(industry: str) -> str:
    """Normalize industry string to a short key."""
    mapping = {
        "핀테크": "fintech",
        "금융": "fintech",
        "이커머스": "ecommerce",
        "커머스": "ecommerce",
        "게임": "gaming",
        "엔터": "entertainment",
        "클라우드": "cloud",
        "반도체": "semiconductor",
        "플랫폼": "tech",
        "IT": "tech",
        "소프트웨어": "tech",
    }
    for label, key in mapping.items():
        if label in industry:
            return key
    return industry.lower().replace("/", "_").replace(" ", "_")


def _scorecard_score(scorecard: dict[str, Any], dim: str) -> float:
    """Extract a score from scorecard dict, return 3.0 if missing."""
    entry = scorecard.get(dim)
    if isinstance(entry, dict):
        return float(entry.get("score", 3.0))
    return 3.0


# ---------------------------------------------------------------------------
# Subsidiary group definitions
# ---------------------------------------------------------------------------

SUBSIDIARY_GROUPS: dict[str, dict[str, Any]] = {
    "카카오": {
        "parent": "카카오",
        "subsidiaries": [
            "카카오뱅크",
            "카카오페이",
            "카카오스타일",
            "카카오엔터테인먼트",
            "카카오페이증권",
        ],
        "corp_codes": {
            "카카오": "00918444",
            "카카오뱅크": "00531578",
            "카카오페이": "01426928",
            "카카오스타일": "01246133",
            "카카오엔터테인먼트": "00527765",
            "카카오페이증권": "00239401",
        },
    },
    "토스": {
        "parent": "비바리퍼블리카",
        "subsidiaries": ["토스뱅크", "토스증권", "토스페이먼츠", "토스랩"],
        "corp_codes": {},
    },
    "네이버": {
        "parent": "네이버",
        "subsidiaries": [
            "네이버웹툰",
            "네이버클라우드",
            "네이버파이낸셜",
            "스노우",
            "라인플러스",
        ],
        "corp_codes": {
            "네이버": "00266360",
            "스노우": "01408806",
        },
    },
}

# Convenience lookup: member name → group name
_MEMBER_TO_GROUP: dict[str, str] = {}
for _grp_name, _grp_def in SUBSIDIARY_GROUPS.items():
    _MEMBER_TO_GROUP[_grp_def["parent"]] = _grp_name
    for _sub in _grp_def["subsidiaries"]:
        _MEMBER_TO_GROUP[_sub] = _grp_name


class CompanyDB:
    """Dynamic company data loader from demo data JSON.

    On first access, loads docs/demo/data/meta.json and builds an alias
    index.  Individual company files under docs/demo/data/companies/ are
    not parsed; the rich meta.json is the authoritative source.

    Thread-safety: single-threaded use only (no locking).
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or _DEFAULT_DATA_DIR
        self._companies: dict[str, dict[str, Any]] = {}   # primary key → raw record
        self._alias_index: dict[str, str] = {}             # normalized alias → primary key
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_company(self, name: str) -> dict[str, Any] | None:
        """Return raw company record by name or alias. None if not found."""
        self._ensure_loaded()
        key = self._resolve_key(name)
        if key is None:
            return None
        return self._companies[key]

    def get_tech_stack(self, name: str) -> list[str]:
        """Return tech stack list for a company (lowercased). Empty list if unknown."""
        record = self.get_company(name)
        if record is None:
            return []
        stack = record.get("tech_stack", [])
        if isinstance(stack, list):
            return [s.lower() for s in stack]
        return []

    def get_culture_hints(self, name: str) -> dict[str, Any]:
        """Return culture hints dict compatible with interview_prep._COMPANY_CULTURE_HINTS."""
        from hirekit.engine.interview_questions import QuestionCategory  # lazy import

        record = self.get_company(name)
        if record is None:
            return {}

        # Build keywords from key_products, vision, business_direction
        keywords: list[str] = []
        for field in ("key_products",):
            val = record.get(field, [])
            if isinstance(val, list):
                keywords.extend(str(v) for v in val[:4])
        for field in ("industry", "sub_industry"):
            val = record.get(field, "")
            if val:
                keywords.append(val)

        # Determine culture category (startup vs large corp)
        size_raw = record.get("size", "")
        is_startup = size_raw in ("스타트업", "유니콘")

        # Industry-aware category
        culture_category = QuestionCategory.STARTUP if is_startup else QuestionCategory.LARGE_CORP

        return {
            "keywords": keywords[:5],
            "culture_category": culture_category,
            "is_startup": is_startup,
        }

    def get_comparator_data(self, name: str) -> dict[str, Any]:
        """Return comparator-compatible data dict for a company.

        Maps meta.json scorecard fields → company_comparator dimension keys:
          scorecard.growth          → growth
          scorecard.compensation    → compensation
          scorecard.culture_fit     → culture
          scorecard.career_leverage → tech_level (career/tech reputation proxy)
          scorecard.job_fit         → brand (company brand proxy)
        wlb and remote are approximated from culture_fit / size.
        """
        record = self.get_company(name)
        if record is None:
            return {}

        scorecard = record.get("scorecard", {})
        # scorecard can be dict-of-dicts or flat; handle both formats
        if isinstance(scorecard, dict) and "dimensions" in scorecard:
            # Old per-company format: {'dimensions': [{'name': ..., 'score': ...}]}
            dims_list = scorecard.get("dimensions", [])
            scorecard_flat = {d["name"]: {"score": d["score"]} for d in dims_list if "name" in d}
        else:
            scorecard_flat = scorecard

        growth = _scorecard_score(scorecard_flat, "growth")
        compensation = _scorecard_score(scorecard_flat, "compensation")
        culture = _scorecard_score(scorecard_flat, "culture_fit")
        # career_leverage is the best proxy for technical reputation / tech_level
        tech_level = _scorecard_score(scorecard_flat, "career_leverage")
        brand = _scorecard_score(scorecard_flat, "job_fit")

        # wlb: approximate from culture score (no direct field)
        wlb = round(culture * 0.85, 1)
        # remote: approximate — large corps tend to be lower
        size_raw = record.get("size", "")
        remote = 3.5 if size_raw in ("스타트업", "유니콘") else 3.0

        # Size mapping
        size_key = _size_label_to_key(size_raw)
        employees = record.get("employee_count") or 0
        if not employees and size_raw:
            # Rough approximations if employee_count is 0
            employees = {
                "startup": 200,
                "mid": 1500,
                "large": 10000,
                "enterprise": 50000,
            }.get(size_key, 1000)

        industry = _industry_to_key(record.get("industry", ""))

        return {
            "industry": industry,
            "size": size_key,
            "size_employees": int(employees),
            "growth": growth,
            "compensation": compensation,
            "culture": culture,
            "tech_level": tech_level,
            "brand": brand,
            "wlb": wlb,
            "remote": remote,
            "region": record.get("_meta", {}).get("region", "kr") if isinstance(record.get("_meta"), dict) else "kr",
        }

    def list_companies(self) -> list[str]:
        """Return list of all primary company names."""
        self._ensure_loaded()
        return list(self._companies.keys())

    # ------------------------------------------------------------------
    # Subsidiary relationship API
    # ------------------------------------------------------------------

    def get_parent(self, name: str) -> str | None:
        """Return the parent company name for a subsidiary, or None.

        Returns None if *name* is itself a parent or not in any group.
        """
        grp_name = _MEMBER_TO_GROUP.get(name)
        if grp_name is None:
            return None
        grp_def = SUBSIDIARY_GROUPS[grp_name]
        parent = grp_def["parent"]
        # Parent has no parent
        if name == parent:
            return None
        return parent

    def get_subsidiaries(self, name: str) -> list[str]:
        """Return list of subsidiary names for a parent company.

        Returns empty list if *name* is not a known parent.
        """
        grp_name = _MEMBER_TO_GROUP.get(name)
        if grp_name is None:
            return []
        grp_def = SUBSIDIARY_GROUPS[grp_name]
        if grp_def["parent"] != name:
            return []
        return list(grp_def["subsidiaries"])

    def is_subsidiary(self, name: str) -> bool:
        """Return True if *name* is a subsidiary (not a parent) in a known group."""
        grp_name = _MEMBER_TO_GROUP.get(name)
        if grp_name is None:
            return False
        return SUBSIDIARY_GROUPS[grp_name]["parent"] != name

    def get_group(self, name: str) -> list[str]:
        """Return all group members (parent + subsidiaries) for the given company.

        Returns empty list if *name* is not in any group.
        """
        grp_name = _MEMBER_TO_GROUP.get(name)
        if grp_name is None:
            return []
        grp_def = SUBSIDIARY_GROUPS[grp_name]
        return [grp_def["parent"]] + list(grp_def["subsidiaries"])

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self) -> None:
        """Load meta.json and build the alias index."""
        meta_path = self._data_dir / "meta.json"
        if not meta_path.exists():
            return

        try:
            with meta_path.open(encoding="utf-8") as f:
                records: list[dict[str, Any]] = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if not isinstance(records, list):
            return

        for record in records:
            raw_name = record.get("name", "")
            if not raw_name:
                continue

            primary = _extract_primary_name(raw_name)
            self._companies[primary] = record

            # Build alias candidates from the record
            candidates: list[str] = [raw_name, primary]

            # corp_name field
            corp = record.get("corp_name", "")
            if corp:
                candidates.append(corp)

            # For records like "토스 (비바리퍼블리카)" also register "비바리퍼블리카"
            paren_match = re.search(r"\(([^)]+)\)", raw_name)
            if paren_match:
                candidates.append(paren_match.group(1).strip())

            for candidate in candidates:
                norm = _normalize(candidate)
                if norm and norm not in self._alias_index:
                    self._alias_index[norm] = primary

    def _resolve_key(self, name: str) -> str | None:
        """Resolve name/alias to primary key. None if not found."""
        norm = _normalize(name)

        # 1. Exact match in alias index
        if norm in self._alias_index:
            return self._alias_index[norm]

        # 2. Substring match (longer keys first to prefer more specific)
        for key in sorted(self._alias_index, key=len, reverse=True):
            if norm in key or key in norm:
                return self._alias_index[key]

        return None


# ---------------------------------------------------------------------------
# Module-level singleton — shared across all callers in a process
# ---------------------------------------------------------------------------

_default_db: CompanyDB | None = None


def get_default_db() -> CompanyDB:
    """Return the shared default CompanyDB instance."""
    global _default_db
    if _default_db is None:
        _default_db = CompanyDB()
    return _default_db
