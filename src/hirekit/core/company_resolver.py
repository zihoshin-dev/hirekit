"""Company name resolver — central registry for disambiguating companies.

Consolidates DART corp codes and GitHub org mappings so individual sources
don't maintain their own hard-coded dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CompanyInfo:
    """Canonical company record used across all sources."""

    name: str
    dart_code: str = ""
    github_orgs: list[str] = field(default_factory=list)
    region: str = "kr"  # "kr" | "us" | "global"
    aliases: list[str] = field(default_factory=list)


# Central registry: canonical name → CompanyInfo
_REGISTRY: dict[str, CompanyInfo] = {
    "카카오": CompanyInfo(
        name="카카오",
        dart_code="00258801",
        github_orgs=["kakao"],
        aliases=["kakao"],
    ),
    "카카오페이": CompanyInfo(
        name="카카오페이",
        dart_code="01445295",
        github_orgs=["kakaopay"],
        aliases=["kakaopay"],
    ),
    "카카오뱅크": CompanyInfo(
        name="카카오뱅크",
        dart_code="01456825",
        github_orgs=[],
        aliases=["kakaobank"],
    ),
    "카카오게임즈": CompanyInfo(
        name="카카오게임즈",
        dart_code="01137383",
        github_orgs=[],
        aliases=["kakaogames"],
    ),
    "카카오엔터테인먼트": CompanyInfo(
        name="카카오엔터테인먼트",
        dart_code="00130949",
        github_orgs=[],
        aliases=["kakaoent"],
    ),
    "토스": CompanyInfo(
        name="토스",
        dart_code="00783965",
        github_orgs=["toss"],
        aliases=["비바리퍼블리카", "viva republica", "toss"],
    ),
    "비바리퍼블리카": CompanyInfo(
        name="비바리퍼블리카",
        dart_code="00783965",
        github_orgs=["toss"],
        aliases=["토스", "toss"],
    ),
    "토스뱅크": CompanyInfo(
        name="토스뱅크",
        dart_code="01652068",
        github_orgs=[],
        aliases=["tossbank"],
    ),
    "토스증권": CompanyInfo(
        name="토스증권",
        dart_code="00264498",
        github_orgs=[],
        aliases=["tosssecurities"],
    ),
    "네이버": CompanyInfo(
        name="네이버",
        dart_code="00266961",
        github_orgs=["naver", "navercorp"],
        aliases=["naver"],
    ),
    "네이버클라우드": CompanyInfo(
        name="네이버클라우드",
        dart_code="01347498",
        github_orgs=["NaverCloudPlatform"],
        aliases=["naver cloud"],
    ),
    "네이버웹툰": CompanyInfo(
        name="네이버웹툰",
        dart_code="01655498",
        github_orgs=[],
        aliases=["webtoon"],
    ),
    "쿠팡": CompanyInfo(
        name="쿠팡",
        dart_code="01347901",
        github_orgs=["coupang"],
        aliases=["coupang"],
    ),
    "우아한형제들": CompanyInfo(
        name="우아한형제들",
        dart_code="00832628",
        github_orgs=["woowabros"],
        aliases=["배달의민족", "baemin", "woowahan"],
    ),
    "배달의민족": CompanyInfo(
        name="배달의민족",
        dart_code="00832628",
        github_orgs=["woowabros"],
        aliases=["우아한형제들", "baemin"],
    ),
    "당근": CompanyInfo(
        name="당근",
        dart_code="01444039",
        github_orgs=["daangn"],
        aliases=["당근마켓", "daangn", "karrot"],
    ),
    "당근마켓": CompanyInfo(
        name="당근마켓",
        dart_code="01444039",
        github_orgs=["daangn"],
        aliases=["당근", "daangn", "karrot"],
    ),
    "무신사": CompanyInfo(
        name="무신사",
        dart_code="01203942",
        github_orgs=["musinsa"],
        aliases=["musinsa"],
    ),
    "라인플러스": CompanyInfo(
        name="라인플러스",
        dart_code="01231396",
        github_orgs=["line"],
        aliases=["라인", "line"],
    ),
    "라인": CompanyInfo(
        name="라인",
        dart_code="01231396",
        github_orgs=["line"],
        aliases=["라인플러스", "line"],
    ),
    "야놀자": CompanyInfo(
        name="야놀자",
        dart_code="00991498",
        github_orgs=["yanolja"],
        aliases=["yanolja"],
    ),
    "삼성전자": CompanyInfo(
        name="삼성전자",
        dart_code="00126380",
        github_orgs=[],
        aliases=["samsung electronics", "samsung"],
    ),
    "삼성SDS": CompanyInfo(
        name="삼성SDS",
        dart_code="00260155",
        github_orgs=[],
        aliases=["samsung sds"],
    ),
    "LG전자": CompanyInfo(
        name="LG전자",
        dart_code="00401731",
        github_orgs=[],
        aliases=["lg electronics"],
    ),
    "SK하이닉스": CompanyInfo(
        name="SK하이닉스",
        dart_code="00164779",
        github_orgs=[],
        aliases=["sk hynix"],
    ),
    "현대자동차": CompanyInfo(
        name="현대자동차",
        dart_code="00164742",
        github_orgs=[],
        aliases=["hyundai", "현대차"],
    ),
    "CJ ENM": CompanyInfo(
        name="CJ ENM",
        dart_code="00105464",
        github_orgs=[],
        aliases=["cj enm"],
    ),
}

# Build alias lookup on module load
_ALIAS_INDEX: dict[str, str] = {}
for _canonical, _info in _REGISTRY.items():
    _normalized_canonical = _canonical.strip().replace("(주)", "").replace(" ", "").lower()
    _ALIAS_INDEX[_normalized_canonical] = _canonical
    for _alias in _info.aliases:
        _alias_key = _alias.strip().replace("(주)", "").replace(" ", "").lower()
        if _alias_key not in _ALIAS_INDEX:
            _ALIAS_INDEX[_alias_key] = _canonical


def resolve_company(name: str, region: str = "kr") -> CompanyInfo | None:
    """Resolve a company name to its canonical CompanyInfo record.

    Lookup order:
    1. Exact canonical key (normalized)
    2. Alias index (normalized)
    3. Substring match against canonical names and aliases

    Returns None when no match is found.
    """
    normalized = name.strip().replace("(주)", "").replace(" ", "").lower()

    # 1. Exact match (canonical or alias)
    if normalized in _ALIAS_INDEX:
        return _REGISTRY[_ALIAS_INDEX[normalized]]

    # 2. Substring match — input contains a known key or vice versa
    for key, canonical in _ALIAS_INDEX.items():
        if normalized in key or key in normalized:
            return _REGISTRY[canonical]

    return None


# ---------------------------------------------------------------------------
# Backwards-compat exports for existing imports in dart.py / github.py
# ---------------------------------------------------------------------------

KNOWN_CORPS: dict[str, str] = {
    canonical: info.dart_code
    for canonical, info in _REGISTRY.items()
    if info.dart_code
}

DEFAULT_ORG_MAP: dict[str, list[str]] = {
    canonical: info.github_orgs
    for canonical, info in _REGISTRY.items()
    if info.github_orgs
}
