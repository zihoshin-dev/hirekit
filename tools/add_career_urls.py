#!/usr/bin/env python3
"""80개 기업 공식 채용 페이지 URL을 meta.json과 companies/*.json에 추가."""

import json
from pathlib import Path

CAREER_URLS: dict[str, str] = {
    "AWS코리아": "https://aws.amazon.com/ko/careers/",
    "CJ ENM": "https://recruit.cjenm.com/",
    "CJ올리브영": "https://career.oliveyoung.com/ko/home",
    "JYP엔터테인먼트": "https://recruit.jype.com/",
    "KT": "https://recruit.kt.com/",
    "LG CNS": "https://careers.lg.com/apply?c=CNS",
    "SK텔레콤": "https://careers.sktelecom.com/",
    "SK하이닉스": "https://recruit.skhynix.com/",
    "SM엔터테인먼트": "https://recruit.smentertainment.com/ko/home",
    "SSG닷컴": "https://ssg.career.greetinghr.com/ko/career",
    "xAI": "https://x.ai/careers",
    "구글코리아": "https://www.google.com/about/careers/applications/locations/seoul/",
    "그린랩스": "https://greenlabs.co.kr/careers/",
    "네이버": "https://recruit.navercorp.com/",
    "네이버웹툰": "https://recruit.webtoonscorp.com/",
    "네이버클라우드": "https://career.navercloudcorp.com/navercloud/",
    "네이버파이낸셜": "https://recruit.naverfincorp.com/",
    "넥슨코리아": "https://careers.nexon.com/",
    "넷마블": "https://career.netmarble.com/",
    "당근": "https://about.daangn.com/jobs/",
    "두나무": "https://careers.dunamu.com/",
    "딥마인드코리아": "https://deepmind.google/about/careers/",
    "라인플러스": "https://careers.linecorp.com/ko/",
    "뤼튼": "https://wrtn.io/career/",
    "리디": "https://ridi.career.greetinghr.com/ko/home",
    "리벨리온": "https://rebellions.career.greetinghr.com/ko/accelerate-your-career",
    "리턴제로": "https://www.rtzr.ai/recruit",
    "마이리얼트립": "https://myrealtrip.career.greetinghr.com/ko/home",
    "마키나락스": "https://makinarocks.career.greetinghr.com/ko/home",
    "메이크스타": "https://makestar.career.greetinghr.com/process",
    "메타코리아": "https://www.metacareers.com/",
    "무신사": "https://corp.musinsa.com/ko/career/",
    "밀리의서재": "https://www.millie.town/careers/",
    "뱅크샐러드": "https://corp.banksalad.com/jobs/",
    "버킷플레이스": "https://www.bucketplace.com/careers/",
    "비바리퍼블리카": "https://careers.toss.im/",
    "빗썸": "https://www.bithumb-careers.com/",
    "삼성SDS": "https://www.samsungsds.com/en/careers/overview/about_care_over.html",
    "삼성전자": "https://www.samsungcareers.com/",
    "세일즈포스코리아": "https://www.salesforce.com/kr/company/careers/",
    "센드버드": "https://sendbird.com/ko/careers",
    "스노우": "https://recruit.snowcorp.com/",
    "스캐터랩": "https://www.scatterlab.co.kr/ko/recruiting",
    "쏘카": "https://corp.socar.me/careers/jobs",
    "애플코리아": "https://jobs.apple.com/en-us/search?location=korea-republic-of-KOR",
    "앤트로픽코리아": "https://www.anthropic.com/careers",
    "야놀자": "https://careers.yanolja.co/",
    "업스테이지": "https://careers.upstage.ai",
    "에이프로젠": "https://aprogen.recruiter.co.kr/",
    "엔비디아코리아": "https://www.nvidia.com/en-us/about-nvidia/careers/",
    "엔씨소프트": "https://careers.ncsoft.com/",
    "오픈AI코리아": "https://openai.com/careers/",
    "왓챠": "https://watcha.team/",
    "우아한형제들": "https://career.woowahan.com/",
    "원티드랩": "https://www.wantedlab.team/",
    "지마켓": "https://careers.gmarket.com/",
    "직방": "https://career.zigbang.com/",
    "채널코퍼레이션": "https://channel.io/ko/jobs",
    "카카오": "https://careers.kakao.com/",
    "카카오뱅크": "https://recruit.kakaobank.com/",
    "카카오스타일": "https://career.kakaostyle.com/jobs",
    "카카오엔터테인먼트": "https://careers.kakaoent.com/ko/main",
    "카카오페이": "https://kakaopay.career.greetinghr.com/ko/main",
    "카카오페이증권": "https://career.kakaopaysec.com/",
    "컬리": "https://kurly.career.greetinghr.com/ko/home",
    "코인원": "https://recruit.coinonecorp.com/",
    "쿠팡": "https://www.coupang.jobs/en/",
    "크래프톤": "https://www.krafton.com/en/careers/jobs/",
    "클래스101": "https://jobs.class101.net/",
    "테슬라코리아": "https://www.tesla.com/ko_KR/careers",
    "토스": "https://toss.im/career/jobs",
    "토스랩": "https://team.tosslab.com/",
    "토스뱅크": "https://recruit.tossbank.com/",
    "토스증권": "https://recruit.tossinvest.com/",
    "토스페이먼츠": "https://toss.im/career/tosspayments",
    "포티투마루": "https://www.42maru.ai/kr/about-us/careers/",
    "퓨리오사AI": "https://furiosa.ai/careers",
    "핀다": "https://finda.co.kr/careers",
    "하이브": "https://careers.hybecorp.com/ko/home",
    "한국마이크로소프트": "https://careers.microsoft.com/",
}

# meta.json 기업명 → CAREER_URLS 키 매핑 (표기 차이 대응)
NAME_ALIASES: dict[str, str] = {
    "cj_enm": "CJ ENM",
    "cj올리브영": "CJ올리브영",
    "jyp엔터테인먼트": "JYP엔터테인먼트",
    "kt": "KT",
    "lg_cns": "LG CNS",
    "sk텔레콤": "SK텔레콤",
    "sk하이닉스": "SK하이닉스",
    "sm엔터테인먼트": "SM엔터테인먼트",
    "ssg닷컴": "SSG닷컴",
    "xai": "xAI",
    "삼성sds": "삼성SDS",
    "오픈ai코리아": "오픈AI코리아",
    "퓨리오사ai": "퓨리오사AI",
}


def _find_url(name: str) -> str | None:
    """기업명으로 채용 URL 조회."""
    if name in CAREER_URLS:
        return CAREER_URLS[name]
    lower = name.lower()
    if lower in NAME_ALIASES:
        return CAREER_URLS.get(NAME_ALIASES[lower])
    for key, url in CAREER_URLS.items():
        if key.lower() == lower:
            return url
    return None


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    meta_path = base / "docs" / "demo" / "data" / "meta.json"
    companies_dir = base / "docs" / "demo" / "data" / "companies"

    # 1. Update meta.json
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    updated_meta = 0
    for entry in meta:
        name = entry.get("name", "")
        url = _find_url(name)
        if url:
            entry["career_url"] = url
            updated_meta += 1
        elif "career_url" not in entry:
            entry["career_url"] = None

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"meta.json: {updated_meta}/{len(meta)} 기업에 career_url 추가")

    # 2. Update companies/*.json
    updated_companies = 0
    for json_file in sorted(companies_dir.glob("*.json")):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        company_name = data.get("company", json_file.stem)
        url = _find_url(company_name) or _find_url(json_file.stem)
        if url:
            data["career_url"] = url
            updated_companies += 1
        elif "career_url" not in data:
            data["career_url"] = None

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print(f"companies/: {updated_companies} 파일에 career_url 추가")


if __name__ == "__main__":
    main()
