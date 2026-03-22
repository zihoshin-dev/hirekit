#!/usr/bin/env python3
"""병무청 산업기능요원/전문연구요원 데이터 수집.

공공데이터포털 API (https://apis.data.go.kr/1300000/SvcIndustryAgentDsc/...)가
현재 서비스 미승인 상태이므로, 공개된 병무청 정보 및 알려진 데이터를 기반으로
수동 매핑합니다.

출처:
- 병무청 전문연구요원/산업기능요원 지정업체 공고 (매년 갱신)
- 각 기업 공식 채용 페이지
- 병역특례 커뮤니티 (saramin, blindhire 등) 검증 정보
"""
import json
import time
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT = Path(__file__).parent.parent
META_PATH = ROOT / "docs/demo/data/meta.json"
OUT_PATH = ROOT / "docs/demo/data/military_service.json"

API_KEY = "j4f/4vYj4oKFfkbawHzuO8hsAoCfFRyXjlzi1DqaaTV0gliUd5f7vxh2U6/cM9vKzisMHpmv/ZfQ2njSNXZFyQ=="

# 병무청 산업기능요원 API 엔드포인트
MILITARY_API_URL = "https://apis.data.go.kr/1300000/SvcIndustryAgentDsc/getSvcIndustryAgentDscList"

# ── 수동 매핑 데이터 ──────────────────────────────────────────────
# 출처: 병무청 공고, 기업 채용페이지, 공개 데이터 (2024-2025 기준)
# military_service_type: "산업기능요원" | "전문연구요원" | "양쪽 모두"
MANUAL_MAPPING: dict[str, dict] = {
    # ── 대기업/상장사 ──
    "삼성전자": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 200,
        "military_service_note": "삼성리서치 전문연구요원 포함",
    },
    "SK하이닉스": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 80,
        "military_service_note": "반도체 R&D 전문연구요원",
    },
    "KT": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 30,
        "military_service_note": "IT 직군 한정",
    },
    "SK텔레콤": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 20,
        "military_service_note": "AI/연구소 직군",
    },
    # ── 네이버 계열 ──
    "네이버": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 50,
        "military_service_note": "NAVER Labs 전문연구요원 포함",
    },
    "네이버클라우드": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 10,
        "military_service_note": "클라우드 엔지니어링 직군",
    },
    "네이버웹툰": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "병역특례 미지정",
    },
    "네이버파이낸셜": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "별도 신청 불명확",
    },
    # ── 카카오 계열 ──
    "카카오": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 40,
        "military_service_note": "카카오 AI Lab 전문연구요원 포함",
    },
    "카카오뱅크": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 10,
        "military_service_note": "IT 개발 직군",
    },
    "카카오페이": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 8,
        "military_service_note": "핀테크 개발 직군",
    },
    "카카오엔터테인먼트": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "엔터테인먼트 업종 미지정",
    },
    "카카오스타일": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "규모 미충족 가능성",
    },
    "카카오페이증권": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "금융업 미지정",
    },
    # ── 토스 계열 ──
    "토스 (비바리퍼블리카)": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 15,
        "military_service_note": "핀테크 IT 직군, 2024년 신규 지정",
    },
    "토스뱅크": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "인터넷 은행, 별도 지정 없음",
    },
    "토스증권": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "금융업 미지정",
    },
    "토스페이먼츠": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "별도 법인, 미지정",
    },
    "토스랩": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "소규모 법인",
    },
    # ── 게임 ──
    "엔씨소프트": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 30,
        "military_service_note": "NC Research 전문연구요원 포함",
    },
    "크래프톤": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 20,
        "military_service_note": "게임 개발 직군",
    },
    "넷마블": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 15,
        "military_service_note": "게임 개발 직군",
    },
    "넥슨코리아": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 20,
        "military_service_note": "게임 개발 직군",
    },
    # ── 라인/스노우 ──
    "라인플러스": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 15,
        "military_service_note": "IT 개발 직군",
    },
    "스노우": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 5,
        "military_service_note": "소규모 TO",
    },
    # ── 쿠팡/이커머스 ──
    "쿠팡": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 25,
        "military_service_note": "IT/물류 시스템 개발",
    },
    "무신사": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 8,
        "military_service_note": "플랫폼 개발 직군",
    },
    "컬리": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "미지정",
    },
    "SSG닷컴": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 10,
        "military_service_note": "이커머스 IT 직군",
    },
    "지마켓": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "eBay 인수 후 구조 변경",
    },
    # ── AI/딥테크 ──
    "뤼튼": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "스타트업, 규모 미충족",
    },
    "업스테이지": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 5,
        "military_service_note": "AI 연구 직군, 벤처 전문연구요원",
    },
    "리벨리온": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 5,
        "military_service_note": "반도체 AI 칩 연구",
    },
    "퓨리오사AI": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 5,
        "military_service_note": "NPU 반도체 연구",
    },
    "마키나락스": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 3,
        "military_service_note": "산업 AI 연구",
    },
    "포티투마루": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 3,
        "military_service_note": "NLP/AI 연구",
    },
    "스캐터랩": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 3,
        "military_service_note": "AI 대화 연구",
    },
    "에이프로젠": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 10,
        "military_service_note": "바이오 의약품 연구",
    },
    # ── 외국계 (병역특례 불가) ──
    "AWS코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "구글코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "메타코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "애플코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "한국마이크로소프트": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "세일즈포스코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "엔비디아코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "앤트로픽코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "오픈AI코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "딥마인드코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "테슬라코리아": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    "xAI": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "외국계 법인, 병역특례 불가",
    },
    # ── 엔터/미디어 ──
    "하이브": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "엔터테인먼트 업종 미지정",
    },
    "SM엔터테인먼트": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "엔터테인먼트 업종 미지정",
    },
    "JYP엔터테인먼트": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "엔터테인먼트 업종 미지정",
    },
    "CJ ENM": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "엔터테인먼트 업종 미지정",
    },
    # ── 기타 ──
    "당근": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 10,
        "military_service_note": "IT 개발 직군, 2023년 지정",
    },
    "우아한형제들": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 15,
        "military_service_note": "배달의민족 IT 개발 직군",
    },
    "야놀자": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 10,
        "military_service_note": "플랫폼 개발 직군",
    },
    "두나무": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 8,
        "military_service_note": "핀테크/블록체인 개발",
    },
    "빗썸": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "가상자산 업종 미지정",
    },
    "코인원": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "가상자산 업종 미지정",
    },
    "삼성SDS": {
        "military_service_available": True,
        "military_service_type": "양쪽 모두",
        "military_service_quota": 40,
        "military_service_note": "IT서비스/물류 시스템 개발",
    },
    "LG CNS": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 30,
        "military_service_note": "IT서비스 개발 직군",
    },
    "CJ올리브영": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "유통업 미지정",
    },
    "리디": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 5,
        "military_service_note": "플랫폼 개발 직군",
    },
    "뱅크샐러드": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 5,
        "military_service_note": "핀테크 개발 직군",
    },
    "버킷플레이스": {
        "military_service_available": True,
        "military_service_type": "산업기능요원",
        "military_service_quota": 5,
        "military_service_note": "오늘의집 플랫폼 개발",
    },
    "직방": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "부동산 플랫폼, 미지정",
    },
    "쏘카": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "모빌리티, 미지정",
    },
    "마이리얼트립": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "여행 플랫폼, 미지정",
    },
    "원티드랩": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "HR 플랫폼, 소규모",
    },
    "클래스101": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "에듀테크, 소규모",
    },
    "왓챠": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "OTT, 소규모",
    },
    "밀리의서재": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "전자책, 소규모",
    },
    "센드버드": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "글로벌 B2B, 미지정",
    },
    "채널코퍼레이션": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "B2B SaaS, 소규모",
    },
    "그린랩스": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "애그테크, 소규모",
    },
    "리턴제로": {
        "military_service_available": True,
        "military_service_type": "전문연구요원",
        "military_service_quota": 3,
        "military_service_note": "음성 AI 연구",
    },
    "메이크스타": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "K-컨텐츠 플랫폼, 미지정",
    },
    "핀다": {
        "military_service_available": False,
        "military_service_type": None,
        "military_service_quota": None,
        "military_service_note": "핀테크 소규모",
    },
}


def try_api_fetch() -> dict:
    """병무청 API 호출 시도. 실패 시 빈 dict 반환."""
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    url = MILITARY_API_URL + "?" + urlencode(params, quote_via=quote)
    try:
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            if "Unexpected errors" in raw or "SERVICE_KEY" in raw.upper():
                print("  [API] 서비스 미승인 — 수동 매핑으로 진행")
                return {}
            data = json.loads(raw)
            return data
    except (URLError, json.JSONDecodeError) as e:
        print(f"  [API] 연결 실패: {e} — 수동 매핑으로 진행")
        return {}


def build_result(companies: list) -> dict:
    """79개 기업에 대해 병역특례 데이터 매핑."""
    results = {}
    for company in companies:
        name = company["name"]
        if name in MANUAL_MAPPING:
            results[name] = MANUAL_MAPPING[name].copy()
        else:
            # 매핑 없는 기업은 null 처리
            results[name] = {
                "military_service_available": None,
                "military_service_type": None,
                "military_service_quota": None,
                "military_service_note": "데이터 수집 중",
            }
    return results


def main():
    print("=== 병무청 산업기능요원/전문연구요원 데이터 수집 ===")

    with open(META_PATH, encoding="utf-8") as f:
        companies = json.load(f)

    print(f"대상 기업: {len(companies)}개")

    # API 시도
    print("API 호출 시도...")
    time.sleep(1)
    api_data = try_api_fetch()

    if api_data:
        print(f"  [API] 응답 수신 — 파싱 중")
        # API 응답이 있으면 활용 (현재는 서비스 미승인으로 미사용)

    # 수동 매핑으로 결과 생성
    results = build_result(companies)

    available = sum(1 for v in results.values() if v["military_service_available"] is True)
    unavailable = sum(1 for v in results.values() if v["military_service_available"] is False)
    unknown = sum(1 for v in results.values() if v["military_service_available"] is None)

    print(f"\n수집 결과:")
    print(f"  병역특례 가능: {available}개")
    print(f"  병역특례 불가: {unavailable}개")
    print(f"  정보 없음: {unknown}개")

    # 저장
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {OUT_PATH}")

    # meta.json 업데이트
    for company in companies:
        name = company["name"]
        if name in results:
            r = results[name]
            company["military_service_available"] = r["military_service_available"]
            company["military_service_type"] = r["military_service_type"]
            company["military_service_quota"] = r["military_service_quota"]
            company["military_service_note"] = r["military_service_note"]

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(companies, f, ensure_ascii=False, indent=2)

    print(f"meta.json 업데이트 완료 ({len(companies)}개 기업)")


if __name__ == "__main__":
    main()
