<p align="center">
  <h1 align="center">🎯 HireKit</h1>
  <p align="center">
    <strong>취업 준비, 데이터로 시작하세요</strong>
  </p>
  <p align="center">
    14개 소스 자동 수집 → 5차원 스코어카드 → 면접까지 원스톱
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/hirekit/"><img src="https://img.shields.io/pypi/v/hirekit?color=blue" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"></a>
  <a href="https://github.com/zihoshin-dev/hirekit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/zihoshin-dev/hirekit/actions"><img src="https://img.shields.io/github/actions/workflow/status/zihoshin-dev/hirekit/ci.yml?label=tests" alt="Tests"></a>
</p>

<p align="center">
  한국어 | <a href="README.ko.md">한국어 (상세)</a> | <a href="https://zihoshin-dev.github.io/hirekit">데모</a>
</p>

---

## 취업 준비, 데이터로 시작하세요

기업 하나를 제대로 파악하려면 DART 공시, 뉴스, 기술 블로그, 커뮤니티 리뷰... 탭을 10개 넘게 열어야 해요.
HireKit은 그 작업을 2분으로 줄여줘요.

```bash
pip install hirekit
hirekit analyze 카카오
```

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🏢 **기업 분석** | 14개 소스, 5차원 스코어카드 (재무·기술·문화·성장·보상) |
| 📋 **JD 매칭** | 기술 taxonomy 60개+, URL·파일 모두 지원, 3단계 갭 분석 |
| 🎤 **면접 준비** | 200개+ 질문 DB, 직무별 맞춤 STAR 가이드 |
| 📄 **이력서 분석** | 정량 피드백, ATS 호환성, JD 대비 키워드 갭 |
| ✍️ **자소서 분석** | 클리셰 감지 100개+, 4항목 차별화 점수 |
| 🔄 **파이프라인** | 분석→매칭→면접→이력서→자소서 5단계 통합 |

---

## Quick Start

### 1. 설치

```bash
pip install hirekit
```

Python 3.11 이상이면 충분해요. 기본 기능에 별도 설정은 없어요.

### 2. (선택) API 키 설정

```bash
hirekit configure
# ~/.hirekit/.env 파일에 키를 붙여넣으세요
```

### 3. 첫 분석

```bash
hirekit analyze 카카오
```

```
                   카카오 Scorecard
┌─────────────────────┬────────┬────────┬──────────────────┐
│ 평가 항목           │ 가중치 │  점수  │ 근거             │
├─────────────────────┼────────┼────────┼──────────────────┤
│ 직무 적합도         │    30% │  3.5/5 │ 기술 스택 확인됨 │
│ 경력 레버리지       │    20% │  4.6/5 │ 15개 데이터 수집 │
│ 성장 가능성         │    20% │  4.5/5 │ 재무+뉴스 확인   │
│ 보상/복지           │    15% │  3.5/5 │ DART 연봉 데이터 │
│ 문화 적합도         │    15% │  4.5/5 │ 리뷰+Exa 분석    │
│ 종합                │        │ 82/100 │ 등급 S           │
└─────────────────────┴────────┴────────┴──────────────────┘
```

리포트는 `./reports/카카오_analysis.md`에 저장돼요.

---

## 사용 예시

### `hirekit analyze` — 기업 분석

```bash
# 기본 분석 (Markdown 리포트 저장)
hirekit analyze 카카오

# 터미널에서 바로 확인
hirekit analyze 네이버 -o terminal

# JSON 출력 (스크립트 연동)
hirekit analyze 토스 -o json

# 간단 분석 (핵심 섹션만)
hirekit analyze 쿠팡 --tier 3
```

**결과물**: 12섹션 구조화 리포트 + 5차원 100점 스코어카드

---

### `hirekit match` — JD 매칭

```bash
# 채용공고 URL
hirekit match "https://www.wanted.co.kr/wd/12345"

# 텍스트 파일
hirekit match jd.txt

# 내 프로필과 함께 (맞춤 매칭)
hirekit match jd.txt --profile ~/.hirekit/profile.yaml
```

**결과물**: 매칭 점수(0–100), 스킬 갭, 강점, 지원 전략

---

### `hirekit interview` — 면접 준비

```bash
# 기업 맞춤 면접 질문 생성
hirekit interview 카카오

# 직무 지정 (더 구체적인 질문)
hirekit interview 카카오 --position "백엔드 개발자"

# 터미널 출력
hirekit interview 네이버 --position PM -o terminal
```

**결과물**: 공통 질문 5개 + 직무 질문 + STAR 답변 프레임 + 역질문 5개

---

### `hirekit resume` — 이력서 분석

```bash
# 이력서 파일 분석 (md, txt, pdf)
hirekit resume 이력서.md

# JD 대비 분석 (키워드 갭 포함)
hirekit resume 이력서.md --jd "https://wanted.co.kr/wd/12345"
```

**결과물**: ATS 호환성, 구조 분석, 키워드 갭, 콘텐츠 점수, 개선 제안

---

### `hirekit coverletter` — 자소서 분석

```bash
# 자소서 4항목 초안 + 피드백
hirekit coverletter 카카오 --position PM

# 내 프로필로 맞춤 자소서
hirekit coverletter 토스 --position PM --profile profile.yaml
```

**결과물**: 4항목 초안 (성장과정·지원동기·직무역량·장단점) + 클리셰 감지 + 항목별 점수

---

### `hirekit sources` — 소스 상태 확인

```bash
hirekit sources
```

```
                   Data Sources
┌──────────────────┬────────┬─────────────────┬──────────────┐
│ 소스             │ 지역   │ API 키          │ 상태         │
├──────────────────┼────────┼─────────────────┼──────────────┤
│ dart             │ KR     │ DART_API_KEY    │ Ready        │
│ github           │ GLOBAL │ -               │ Ready        │
│ google_news      │ GLOBAL │ -               │ Ready        │
│ naver_news       │ KR     │ NAVER_CLIENT_ID │ 미설정       │
│ tech_blog        │ KR     │ -               │ Ready        │
│ community_review │ KR     │ -               │ Ready        │
└──────────────────┴────────┴─────────────────┴──────────────┘
```

---

## 데이터 소스 (14개)

| 소스 | 지역 | 데이터 | API 키 필요 |
|------|------|--------|:-----------:|
| **DART** | 🇰🇷 | 재무제표, 직원수, 평균연봉 (금감원 공시) | ✅ |
| **네이버 뉴스** | 🇰🇷 | 최신 뉴스 기사 | ✅ |
| **네이버 검색** | 🇰🇷 | 블로그 면접후기, 카페 리뷰 | ✅ |
| **기술 블로그** | 🇰🇷 | 사내 기술 블로그, 개발 문화 | ❌ |
| **커뮤니티 리뷰** | 🇰🇷 | 블라인드·잡플래닛 요약 | ❌ |
| **GitHub** | 🌐 | 기술 성숙도 (리포·스타·언어) | ❌ (gh CLI) |
| **Google News** | 🌐 | RSS 기반 최신 뉴스 | ❌ |
| **해외 주요 언론** | 🌐 | Reuters, Bloomberg, FT, WSJ, 한경 | ❌ |
| **회사 공식 웹사이트** | 🌐 | 비전, 미션, 주요 공지 | ❌ |
| **채용 페이지** | 🌐 | JD, 복지, 채용 문화 | ❌ |
| **Medium / Velog** | 🌐 | 개발자 기고, 기술 트렌드 | ❌ |
| **LinkedIn 검색** | 🌐 | 팀 규모, 직군 분포 | ❌ |
| **Brave Search** | 🌐 | 웹+뉴스 시맨틱 검색 | ✅ |
| **Exa Search** | 🌐 | AI 기반 딥서치 | ✅ |

> API 키가 **하나도 없어도** Google News, 해외 주요 언론, 기술 블로그, 커뮤니티 리뷰, GitHub(gh CLI 설치 시) 등 8개 소스가 바로 동작해요.

---

## 프라이버시

- 모든 데이터 처리는 **로컬**에서 실행돼요
- 수집한 데이터를 외부 서버로 전송하지 않아요
- API 키는 `~/.hirekit/.env`에 직접 관리해요
- LLM(AI)을 연결해도 프롬프트만 해당 API에 전달돼요

---

## Contributing

기여를 환영해요! 시작하기 좋은 작업들:

- 새로운 데이터 소스 추가 (Glassdoor, SEC Edgar 등)
- 자소서 템플릿·클리셰 DB 확장
- 스코어링 알고리즘 개선

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

---

## 라이선스

MIT License — [LICENSE](LICENSE)

<p align="center">
  <sub>더 나은 도구를 가질 자격이 있는 모든 취업 준비자를 위해.</sub>
</p>
