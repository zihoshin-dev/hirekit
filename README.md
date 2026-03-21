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
  <a href="https://pypi.org/project/hirekit/"><img src="https://img.shields.io/pypi/v/hirekit?color=4F8EF7&label=PyPI" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-4F8EF7.svg" alt="Python"></a>
  <a href="https://github.com/zihoshin-dev/hirekit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/zihoshin-dev/hirekit/actions"><img src="https://img.shields.io/github/actions/workflow/status/zihoshin-dev/hirekit/ci.yml?label=tests" alt="Tests"></a>
  <a href="https://zihoshin-dev.github.io/hirekit"><img src="https://img.shields.io/badge/demo-live-FF6B6B.svg" alt="Demo"></a>
</p>

<p align="center">
  한국어 | <a href="README.ko.md">한국어 (상세)</a> | <a href="https://zihoshin-dev.github.io/hirekit">데모</a>
</p>

---

> 🔗 **[라이브 데모 — 79개 한국 테크 기업 분석 결과 보기](https://zihoshin-dev.github.io/hirekit)**

---

기업 하나를 제대로 파악하려면 DART 공시, 뉴스, 기술 블로그, 커뮤니티 리뷰... 탭을 10개 넘게 열어야 해요.
HireKit은 그 작업을 2분으로 줄여줘요.

```bash
pip install hirekit
hirekit analyze 카카오
```

---

## 아키텍처

```mermaid
graph LR
    A[hirekit analyze 카카오] --> B[14개 데이터 소스]
    B --> C1[DART 재무]
    B --> C2[GitHub 기술]
    B --> C3[뉴스/블로그]
    B --> C4[커뮤니티 리뷰]
    C1 --> D[5차원 스코어카드]
    C2 --> D
    C3 --> D
    C4 --> D
    D --> E[분석 리포트]
```

---

## 분석 파이프라인

```mermaid
flowchart TD
    A[기업명 입력] --> B[데이터 수집]
    B --> B1[Tier 1: DART·GitHub — 2초]
    B --> B2[Tier 2: 뉴스·검색 — 10초]
    B --> B3[Tier 3: 커뮤니티 — 30초]
    B1 --> C[스코어링]
    B2 --> C
    B3 --> C
    C --> D{LLM 사용?}
    D -->|Yes| E[AI 심층 분석]
    D -->|No| F[데이터 기반 리포트]
    E --> G[최종 리포트]
    F --> G
```

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

## 5차원 스코어카드

| 차원 | 가중치 | 데이터 소스 | 측정 방법 |
|------|--------|------------|----------|
| 🎯 **Job Fit** | 30% | GitHub, 기술블로그 | 기술 성숙도, 오픈소스 활동 |
| 📈 **Growth** | 20% | DART 재무 | 매출/영업이익 성장률 |
| 💰 **Compensation** | 15% | DART 인사 | 평균 연봉, 근속연수 |
| 🤝 **Culture Fit** | 15% | 네이버, Exa | 리뷰 다양성, 블로그 분석 |
| 🚀 **Career Leverage** | 20% | 종합 | 기업 규모, 브랜드, 뉴스 |

---

## 명령어 가이드

| 명령어 | 설명 | 주요 기능 |
|--------|------|----------|
| `hirekit analyze 카카오` | 기업 종합 분석 | 14개 소스, 5차원 스코어, 12섹션 리포트 |
| `hirekit match --jd "URL"` | JD 매칭 | 60+ 기술 taxonomy, 3단계 매칭, 학습 로드맵 |
| `hirekit interview 카카오` | 면접 준비 | 200+ 질문, STAR 가이드, 기업별 문화핏 |
| `hirekit resume --file resume.txt` | 이력서 분석 | 정량 피드백, ATS 최적화, Before→After |
| `hirekit coverletter --file cl.txt` | 자소서 분석 | 클리셰 감지 100+, 차별화 점수 |
| `hirekit pipeline 카카오` | 통합 파이프라인 | 5단계 순차 분석 + Go/Hold/Pass 판정 |

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

## Claude Code에서 바로 사용하기

HireKit은 Claude Code 세션 안에서 자연스럽게 동작해요.

### 슬래시 명령어

```
/analyze 카카오        — 기업 분석 + AI 해석
/interview 카카오      — 면접 질문 생성 + STAR 가이드
/match <JD-URL>       — JD 매칭 + 갭 분석
```

### 자연어 자동 트리거

"카카오 어떤 회사야?", "면접 준비해줘" 같은 자연어로도 HireKit이 자동 호출돼요.

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
