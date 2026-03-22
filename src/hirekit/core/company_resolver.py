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
    corp_name: str = ""   # 법인 정식 명칭 (예: "비바리퍼블리카")
    brand_name: str = ""  # 브랜드명 (예: "토스")
    # 외국계 한국 지사 전용 필드
    is_foreign: bool = False          # 외국계 한국 지사 여부
    parent_company: str = ""          # 본사 정식 명칭 (예: "Alphabet Inc.")
    parent_ticker: str = ""           # 본사 티커 (비상장이면 "")
    parent_revenue: str = ""          # 본사 글로벌 매출 요약 (공개 정보)
    kr_revenue: str = ""              # 한국 매출 (공정위 공시 등 알려진 경우)


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
        dart_code="01244601",
        github_orgs=["kakaopay"],
        aliases=["kakaopay"],
    ),
    "카카오뱅크": CompanyInfo(
        name="카카오뱅크",
        dart_code="01133217",
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
        dart_code="01212921",
        github_orgs=["toss"],
        aliases=["비바리퍼블리카", "viva republica", "toss"],
        corp_name="비바리퍼블리카",
        brand_name="토스",
    ),
    "비바리퍼블리카": CompanyInfo(
        name="비바리퍼블리카",
        dart_code="01212921",
        github_orgs=["toss"],
        aliases=["토스", "toss"],
        corp_name="비바리퍼블리카",
        brand_name="토스",
    ),
    "토스뱅크": CompanyInfo(
        name="토스뱅크",
        dart_code="01529195",
        github_orgs=[],
        aliases=["tossbank"],
    ),
    "토스증권": CompanyInfo(
        name="토스증권",
        dart_code="01527984",
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
        dart_code="00777272",
        github_orgs=["NaverCloudPlatform"],
        aliases=["naver cloud"],
    ),
    "네이버웹툰": CompanyInfo(
        name="네이버웹툰",
        dart_code="01485846",
        github_orgs=[],
        aliases=["webtoon"],
    ),
    "쿠팡": CompanyInfo(
        name="쿠팡",
        dart_code="01019166",
        github_orgs=["coupang"],
        aliases=["coupang"],
    ),
    "우아한형제들": CompanyInfo(
        name="우아한형제들",
        dart_code="01063273",
        github_orgs=["woowabros"],
        aliases=["배달의민족", "baemin", "woowahan"],
        corp_name="우아한형제들",
        brand_name="배달의민족",
    ),
    "배달의민족": CompanyInfo(
        name="배달의민족",
        dart_code="01063273",
        github_orgs=["woowabros"],
        aliases=["우아한형제들", "baemin"],
        corp_name="우아한형제들",
        brand_name="배달의민족",
    ),
    "당근": CompanyInfo(
        name="당근",
        dart_code="01547845",
        github_orgs=["daangn"],
        aliases=["당근마켓", "daangn", "karrot"],
        corp_name="당근마켓",
        brand_name="당근",
    ),
    "당근마켓": CompanyInfo(
        name="당근마켓",
        dart_code="01547845",
        github_orgs=["daangn"],
        aliases=["당근", "daangn", "karrot"],
        corp_name="당근마켓",
        brand_name="당근",
    ),
    "무신사": CompanyInfo(
        name="무신사",
        dart_code="01137727",
        github_orgs=["musinsa"],
        aliases=["musinsa"],
    ),
    "라인플러스": CompanyInfo(
        name="라인플러스",
        dart_code="01026731",
        github_orgs=["line"],
        aliases=["라인", "line"],
    ),
    "라인": CompanyInfo(
        name="라인",
        dart_code="01026731",
        github_orgs=["line"],
        aliases=["라인플러스", "line"],
    ),
    "야놀자": CompanyInfo(
        name="야놀자",
        dart_code="00907864",
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
        dart_code="00126186",
        github_orgs=[],
        aliases=["samsung sds", "삼성에스디에스"],
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
        dart_code="00265324",
        github_orgs=[],
        aliases=["cj enm", "씨제이이엔엠"],
    ),
    "두나무": CompanyInfo(
        name="두나무",
        dart_code="01310241",
        github_orgs=[],
        aliases=["dunamu", "업비트"],
        corp_name="두나무",
        brand_name="업비트",
    ),
    "뤼튼": CompanyInfo(
        name="뤼튼",
        dart_code="01921445",
        github_orgs=[],
        aliases=["wrtn", "뤼튼테크놀로지스", "wrtn technologies"],
        corp_name="뤼튼테크놀로지스",
        brand_name="뤼튼",
    ),
    # ── 외국계 한국 지사 ──────────────────────────────────────────────────────
    "구글코리아": CompanyInfo(
        name="구글코리아",
        corp_name="구글코리아 유한회사",
        brand_name="구글코리아",
        aliases=["google korea", "googlekorea", "google kr"],
        is_foreign=True,
        parent_company="Alphabet Inc.",
        parent_ticker="GOOGL",
        parent_revenue="글로벌 매출 $3,482억 (FY2024)",
        kr_revenue="약 3,653억 원 (2023년 감사보고서 기준)",
    ),
    "딥마인드코리아": CompanyInfo(
        name="딥마인드코리아",
        corp_name="딥마인드코리아 유한회사",
        brand_name="딥마인드코리아",
        aliases=["deepmind korea", "deepmindkorea", "google deepmind kr"],
        is_foreign=True,
        parent_company="Alphabet Inc. (Google DeepMind)",
        parent_ticker="GOOGL",
        parent_revenue="글로벌 매출 $3,482억 (FY2024, Alphabet 연결)",
        kr_revenue="",
    ),
    "애플코리아": CompanyInfo(
        name="애플코리아",
        corp_name="애플코리아 유한회사",
        brand_name="애플코리아",
        aliases=["apple korea", "applekorea", "apple kr"],
        is_foreign=True,
        parent_company="Apple Inc.",
        parent_ticker="AAPL",
        parent_revenue="글로벌 매출 $3,911억 (FY2024)",
        kr_revenue="약 7,556억 원 (2023년 감사보고서 기준)",
    ),
    "메타코리아": CompanyInfo(
        name="메타코리아",
        corp_name="메타코리아 유한회사",
        brand_name="메타코리아",
        aliases=["meta korea", "metakorea", "facebook korea", "meta kr"],
        is_foreign=True,
        parent_company="Meta Platforms Inc.",
        parent_ticker="META",
        parent_revenue="글로벌 매출 $1,648억 (FY2024)",
        kr_revenue="약 570억 원 (2023년 감사보고서 기준)",
    ),
    "엔비디아코리아": CompanyInfo(
        name="엔비디아코리아",
        corp_name="엔비디아코리아 유한회사",
        brand_name="엔비디아코리아",
        aliases=["nvidia korea", "nvidiakorea", "nvidia kr"],
        is_foreign=True,
        parent_company="NVIDIA Corporation",
        parent_ticker="NVDA",
        parent_revenue="글로벌 매출 $1,303억 (FY2025)",
        kr_revenue="약 1,200억 원 (2023년 추정)",
    ),
    "테슬라코리아": CompanyInfo(
        name="테슬라코리아",
        corp_name="테슬라코리아 유한회사",
        brand_name="테슬라코리아",
        aliases=["tesla korea", "teslakorea", "tesla kr"],
        is_foreign=True,
        parent_company="Tesla Inc.",
        parent_ticker="TSLA",
        parent_revenue="글로벌 매출 $977억 (FY2024)",
        kr_revenue="약 6,200억 원 (2023년 추정, 차량 판매 포함)",
    ),
    "세일즈포스코리아": CompanyInfo(
        name="세일즈포스코리아",
        corp_name="세일즈포스코리아 유한회사",
        brand_name="세일즈포스코리아",
        aliases=["salesforce korea", "salesforcekorea", "salesforce kr"],
        is_foreign=True,
        parent_company="Salesforce Inc.",
        parent_ticker="CRM",
        parent_revenue="글로벌 매출 $347억 (FY2024)",
        kr_revenue="",
    ),
    "한국마이크로소프트": CompanyInfo(
        name="한국마이크로소프트",
        corp_name="한국마이크로소프트 유한회사",
        brand_name="한국마이크로소프트",
        aliases=["microsoft korea", "microsoftkorea", "ms korea", "mskorea"],
        is_foreign=True,
        parent_company="Microsoft Corporation",
        parent_ticker="MSFT",
        parent_revenue="글로벌 매출 $2,454억 (FY2024)",
        kr_revenue="약 8,000억 원 (2023년 추정)",
    ),
    "AWS코리아": CompanyInfo(
        name="AWS코리아",
        corp_name="아마존웹서비스코리아 유한책임회사",
        brand_name="AWS코리아",
        aliases=["aws korea", "awskorea", "amazon web services korea", "amazon korea"],
        is_foreign=True,
        parent_company="Amazon.com Inc.",
        parent_ticker="AMZN",
        parent_revenue="글로벌 매출 $6,380억 (FY2024), AWS 매출 $1,079억",
        kr_revenue="약 1조 4,000억 원 (2023년 추정)",
    ),
    "앤트로픽코리아": CompanyInfo(
        name="앤트로픽코리아",
        corp_name="앤트로픽코리아 유한회사",
        brand_name="앤트로픽코리아",
        aliases=["anthropic korea", "anthropickorea", "anthropic kr"],
        is_foreign=True,
        parent_company="Anthropic PBC",
        parent_ticker="",  # 비상장
        parent_revenue="비상장 — 연간 ARR $10억+ (2024년 추정)",
        kr_revenue="",
    ),
    "오픈AI코리아": CompanyInfo(
        name="오픈AI코리아",
        corp_name="오픈AI코리아 유한회사",
        brand_name="오픈AI코리아",
        aliases=["openai korea", "openaikorea", "openai kr"],
        is_foreign=True,
        parent_company="OpenAI LLC",
        parent_ticker="",  # 비상장
        parent_revenue="비상장 — 연간 ARR $37억 (2024년 추정)",
        kr_revenue="",
    ),
    "xAI": CompanyInfo(
        name="xAI",
        corp_name="xAI Korea",
        brand_name="xAI",
        aliases=["xai korea", "x.ai", "elon ai"],
        is_foreign=True,
        parent_company="xAI Corp",
        parent_ticker="",  # 비상장
        parent_revenue="비상장 — 기업가치 $500억 (2024년 시리즈B 기준)",
        kr_revenue="",
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
