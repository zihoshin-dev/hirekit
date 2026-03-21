# HireKit — AI-Powered Company Analysis & Interview Prep CLI

## Project Vision

취업/이직 준비자를 위한 **엔드투엔드 기업 분석 + 면접 준비 CLI 도구**.
다중 소스에서 기업 데이터를 자동 수집 → AI로 종합 분석 → 맞춤 면접 전략까지 원스톱으로 제공한다.

> "8시간 걸리던 기업 분석을 30분으로."

---

## 1. 왜 이 프로젝트인가 (Why)

### 시장 공백 (Blue Ocean)

| 기존 도구 | 한계 |
|-----------|------|
| 잡플래닛/블라인드 | 리뷰 편향 (불만 과대), 정량 분석 부재 |
| 원티드/사람인 | JD 나열만, 매칭도/전략 분석 없음 |
| DART/공시 | 재무 원시 데이터, 취업 관점 해석 없음 |
| 이력서 빌더 (Reactive Resume 등) | 기업 분석과 연결 안 됨 |
| 면접 질문 모음 (GitHub) | Markdown 정적 자료, 기업별 맞춤 불가 |

**HireKit이 채우는 공백**: 다중 소스 자동 수집 → 구조화된 분석 → JD 매칭 → 면접 코칭까지 하나의 파이프라인.

### 경쟁 현황 (GitHub 조사 결과)

- **면접 준비**: Coding Interview University (338K★), Tech Interview Handbook (138K★) — 전부 정적 Markdown
- **이력서**: Reactive Resume (34.6K★), JSONResume CLI (4.7K★) — 기업 분석과 무관
- **DART**: OpenDartReader (430★), dart-fss (360★) — API 래퍼만, 취업 관점 분석 없음
- **AI 취업 도구**: ResuLLMe (459★), ResumeFlow (203★) — 이력서만, 기업 분석 없음

→ **기업 분석 + AI + 면접 준비를 통합한 오픈소스는 전무**

---

## 2. 네이밍 후보

| 이름 | 의미 | 장점 | 단점 |
|------|------|------|------|
| **HireKit** | Hire + Kit (채용 도구) | 짧고 직관적, 글로벌 통용 | hire 단어 흔함 |
| **JobIntel** | Job + Intelligence | 분석 도구 느낌 강함 | intel 상표 연상 |
| **CareerScope** | Career + Scope | 범위/깊이 의미 | 다소 길다 |
| **HireScout** | Hire + Scout | 정찰/탐색 의미 | scout 다른 도구 존재 |
| **CompanyLens** | Company + Lens | 기업을 들여다보는 렌즈 | 기업 분석에 한정 |
| **JobCraft** | Job + Craft | 장인정신 의미 | Minecraft 연상 |

**추천**: `HireKit` — 짧고, 기억하기 쉽고, pip install hirekit으로 자연스럽고, PyPI 미사용 확인 필요.

### Tagline 후보

1. "Your AI copilot for job hunting"
2. "Research companies. Match jobs. Ace interviews."
3. "From DART filings to interview prep — one CLI"
4. "Open-source company intelligence for job seekers"
5. "Know the company before they know you"

---

## 3. 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Layer (typer)                     │
│  hirekit analyze <company>   hirekit match <jd-url>     │
│  hirekit compare <c1> <c2>   hirekit interview <company>│
│  hirekit resume review <file>                           │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│              Orchestrator + Config Layer                 │
│  Pipeline executor │ Parallel collector │ Cache manager  │
│  ~/.hirekit/config.toml │ profile.yaml │ secrets.env    │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                   Core Engine Layer                      │
│  CompanyAnalyzer │ JDMatcher │ InterviewPrep │ Resume   │
│  TrendAnalyzer   │ Comparator │ Scorer                  │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┴──────────┐
    ▼                    ▼
┌────────────┐   ┌──────────────────────────────────────┐
│ LLM Layer  │   │      Data Source Plugin Layer         │
│            │   │                                      │
│ OpenAI     │   │ [KR] dart, naver_news, wanted        │
│ Anthropic  │   │ [US] sec_edgar, google_news           │
│ Ollama     │   │ [GL] github, linkedin, crunchbase     │
│ No-LLM    │   │ [User] ~/.hirekit/plugins/*.py        │
└────────────┘   └──────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                 Output Backend Layer                     │
│  Markdown │ JSON │ Terminal (rich) │ Notion │ Obsidian  │
└─────────────────────────────────────────────────────────┘
```

### 핵심 설계 원칙

1. **Plugin-first**: 데이터 소스, LLM, 출력 포맷 모두 플러그인
2. **LLM-agnostic**: OpenAI/Anthropic/Ollama/없이도 동작
3. **Privacy-first**: API 키 로컬만, 데이터 외부 전송 없음, PII 마스킹
4. **No-LLM 모드**: LLM 없어도 데이터 수집 + 구조화 리포트 생성
5. **Region-aware**: kr/us/global 소스 모듈 분리

### 기술 스택

| 영역 | 선택 | 이유 |
|------|------|------|
| CLI | typer + rich | 타입 힌트 기반, 자동 도움말, 터미널 UI |
| HTTP | httpx (async) | 비동기 병렬 수집, HTTP/2 |
| 파싱 | beautifulsoup4 + lxml | 웹 스크래핑 표준 |
| LLM | litellm (optional) | 100+ LLM 통합, 유지보수 최소 |
| 검증 | pydantic v2 | 설정/프로필 스키마 검증 |
| 템플릿 | jinja2 | 프롬프트 + 리포트 생성 |
| 캐시 | sqlite3 (stdlib) | 제로 의존성, TTL 관리 |
| 테스트 | pytest + respx | 비동기 HTTP 모킹 |
| 패키징 | hatchling | PEP 621, 모던 빌드 |

---

## 4. 로드맵

### Phase 1: MVP (4주)

**목표**: `pip install hirekit && hirekit analyze 카카오` 한 줄로 기업 분석 리포트 생성

**기능 범위**:
- [ ] DART 공시 데이터 수집 (재무, 인력, 연봉)
- [ ] GitHub 기술 성숙도 스코어링
- [ ] 뉴스 수집 (네이버 검색 API)
- [ ] 12섹션 Markdown 리포트 생성 (No-LLM 템플릿)
- [ ] LLM 종합 해석 모드 (optional)
- [ ] 가중 스코어카드 (5차원 100점)
- [ ] CLI 기본 명령어: analyze, configure
- [ ] 캐시 시스템 (7일 TTL)

**제외** (Phase 2로):
- JD 매칭, 면접 준비, 이력서 도구
- 잡플래닛/블라인드/Glassdoor 스크래핑
- 웹 UI, Notion/Obsidian 연동
- 해외 기업 분석 (SEC Edgar)

### Phase 2: Growth (8주)

- [ ] `hirekit match <jd-url>` — JD 파싱 + 이력서 매칭도 분석
- [ ] `hirekit interview <company>` — 기업별 예상 질문 + STAR 코칭
- [ ] `hirekit resume review <file>` — 이력서 리뷰/피드백
- [ ] `hirekit compare <c1> <c2>` — 복수 기업 교차 비교
- [ ] 원티드/사람인 채용공고 파싱
- [ ] Notion/Obsidian 출력 플러그인
- [ ] 사용자 프로필 시스템 (경력 자산 관리)
- [ ] 영어 리포트 출력 옵션

### Phase 3: Ecosystem (12주+)

- [ ] SEC Edgar (미국 기업)
- [ ] LinkedIn/Glassdoor 연동 (커뮤니티 플러그인)
- [ ] 웹 UI (Streamlit or Next.js)
- [ ] 채용 시장 트렌드 분석
- [ ] 커뮤니티 플러그인 마켓플레이스
- [ ] 다국어 (일본어, 중국어)
- [ ] GitHub Actions 기반 자동 분석 (스케줄)

---

## 5. GitHub Star 전략

### 런칭 전 체크리스트

```
필수 파일
├── README.md (영문, 30초 룰)
├── README.ko.md (한국어)
├── LICENSE (MIT)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── .github/ISSUE_TEMPLATE/ (bug, feature)
├── .github/PULL_REQUEST_TEMPLATE.md
└── examples/ (config, profile, output 샘플)
```

### README 30초 룰

1. 로고 + 한 줄 설명 + 배지
2. 데모 GIF (터미널에서 분석 실행 → 리포트 생성)
3. 핵심 기능 5개 bullet
4. Quick Start 5줄 (`pip install → configure → analyze`)
5. 실제 출력 예시 스크린샷

### 런칭 타임라인

```
D-14: 한국 개발자 커뮤니티 사전 피드백 (GeekNews, OKKY)
D-7:  BetaList 제출
D-0 (화~목):
  오전: Product Hunt 런칭 (데모 GIF + 웹사이트)
  오후: Hacker News "Show HN" (GitHub 직링크)
D+1: Reddit r/programming, r/SideProject
D+3: DEV.to 기술 블로그 포스팅 (빌드 스토리)
D+7: LinkedIn 성과 공유
```

### Content Flywheel

1. 기업 분석 예시 output을 블로그로 → SEO 유입
2. 주간 릴리스 노트 → Twitter/X 공유
3. `good first issue` 10개+ → 기여자 유입
4. "Made with HireKit" 사용자 사례 갤러리

---

## 6. 리스크 & 대응

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| 잡플래닛/블라인드 크롤링 TOS 위반 | 높음 | MVP에서 제외, 플러그인으로 커뮤니티 위임 |
| LLM 환각 (가짜 재무 수치) | 높음 | 수치는 API 소스만, LLM은 해석만 |
| CLI → 비개발자 접근 불가 | 중간 | Phase 3에서 웹 UI 추가 |
| DART API 일일 한도 (10,000건) | 낮음 | 캐시 7일 + rate limit |
| 비상장사 DART 데이터 부재 | 중간 | 대체 소스(Crunchbase, 뉴스) 매핑 |
| 동명 기업 혼동 | 낮음 | 기업코드 기반 disambiguation |

---

## 7. 차별화 요소 (vs 기존 도구)

| 차별점 | 설명 |
|--------|------|
| **엔드투엔드** | 데이터 수집 → 분석 → JD 매칭 → 면접 코칭 한 파이프라인 |
| **다중 소스 교차 검증** | DART + 뉴스 + GitHub + 공식사이트를 교차해 편향 제거 |
| **정량 스코어카드** | 감이 아닌 데이터 기반 5차원 100점 평가 |
| **LLM 없이도 동작** | API 키 없어도 구조화된 리포트 생성 |
| **플러그인 확장** | pip install로 데이터 소스/출력 포맷 추가 |
| **프라이버시 퍼스트** | 모든 데이터 로컬 처리, 외부 전송 없음 |

---

## 8. 성공 지표

| 지표 | 3개월 | 6개월 | 12개월 |
|------|-------|-------|--------|
| GitHub Stars | 500+ | 2,000+ | 5,000+ |
| PyPI 다운로드 | 1,000+ | 5,000+ | 20,000+ |
| Contributors | 5+ | 15+ | 30+ |
| 지원 기업 수 | DART 전체 | + US Top 100 | + JP/EU |
| 플러그인 수 | 3 (내장) | 8+ | 15+ |
