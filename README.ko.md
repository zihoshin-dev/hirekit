<p align="center">
  <h1 align="center">HireKit</h1>
  <p align="center">
    <strong>면접 가서 "왜 우리 회사?"라는 질문에 자신 있게 답할 수 있게 해주는 CLI</strong>
  </p>
  <p align="center">
    기업 분석. 직무 매칭. 면접 준비.
  </p>
</p>

---

## 왜 필요한가

면접장에 앉았습니다. 면접관이 묻습니다: **"왜 우리 회사에 지원하셨나요?"**

당신은 잠깐 멈춥니다. 채용공고와 회사 소개 페이지만 봤거든요.

**한국 취업 시장 현실:**
- 면접 탈락 피드백 1위: "회사 분석 부족"
- 기업 조사에 소비하는 시간: 4-8시간 (DART + 뉴스 + 블라인드 + 잡플래닛 + GitHub + 연봉공시 등)
- 자료의 위치: 10개 이상의 사이트에 분산됨
- 현실: 시간도 많이 들고, 자료도 모순됨 ("뉴스는 호황 보도인데 DART는 빚이 늘어남?")

**HireKit이 해결합니다:** 한 줄의 명령어, 2분의 시간, 8개 데이터 소스, 1개의 의사결정 리포트.

```bash
$ hirekit analyze 카카오
# 2분 뒤: 12섹션 분석 리포트 완성
# 이제 당신은 확신 있게 답할 수 있습니다.
```

---

## 어떻게 작동하는가

### Step 1: 설치 (30초)

```bash
pip install hirekit
```

### Step 2: 설정 (1분, 처음 한 번만)

```bash
hirekit configure
```

필요한 것:
- **DART API 키**: [여기서 신청](https://opendart.fss.or.kr/)
- **네이버 Client ID**: [네이버 개발자 센터](https://developers.naver.com/)

### Step 3: 분석 (2분)

```bash
$ hirekit analyze 카카오
# 또는 네이버, 쿠팡, 현대차, 삼성전자 등 모든 한국 상장사
```

**전체 시간: 3분 vs 기존 4-8시간**

---

## 뭘 얻게 되나

### 한 개의 점수: 0-100 직무 적합도

```
82/100 = 강력 추천 (지원하세요)
75/100 = 경쟁력 있음 (준비하고 지원하세요)
60/100 = 주의 (리스크 존재 — 면접에서 확인하세요)
```

### 12섹션 의사결정 리포트

| 섹션 | 면접 준비에서의 역할 |
|------|------------------|
| **재무 건강도** | 연봉 인상 가능성, 구조조정 위험 |
| **기술 스택** | 면접에서 깊이있는 질문 예상, 당신의 강점 파악 |
| **최근 뉴스** | 회사 방향성, 리더십 변화, 이슈 상황 |
| **문화 & 팀** | 실제 근무 환경, 야근 문화, 재택 현황 (블라인드 기반) |
| **경쟁 위치** | 시장에서의 입지, 경쟁 회사와의 차이 |
| **리스크 플래그** | 주의할 점, 면접에서 물어볼 질문 |
| **면접 준비 팁** | 이 회사에 맞는 STAR 질문 템플릿 |

### 데이터 검증 기준

- **DART 공시**: 공식 재무 데이터 (신뢰도 100%)
- **블라인드 평가**: 현직자 45명 이상, 호평률 포함
- **뉴스**: 최근 6개월, 출처 명시
- **GitHub**: 기술 깊이 객관적 스코어

충돌 시 명시: *"뉴스는 성장 전망, DART는 부채 증가 — 확인 필요"*

---

## 실제 사용 사례

### Before (기존 방식)

```
월요일 오전 10시: 원티드에서 공고 발견
→ 월요일 2시간: 뉴스 검색 (5개 사이트)
→ 월요일 1시간: 블라인드, 잡플래닛 읽기
→ 화요일 1시간: DART 공시 읽기
→ 화요일 1시간: GitHub 프로젝트 분석
→ 화요일 1시간: 면접관 LinkedIn 검색

총 6-8시간 소비
지원까지 2-3일 소요
면접 가서도 "잠깐, 이게 뭐였더라?" 하며 버벅거림
```

### After (HireKit)

```
월요일 오전 10시: 원티드에서 공고 발견
→ 같은 시간: hirekit analyze 명령어 실행
→ 2분 뒤: 12섹션 리포트 받음
→ 5분간 읽음

총 7분 소비
즉시 지원 가능
면접에서 "당신이 저희 기술 스택을 알고 계신가요?" 물으면 자신 있게 대답 가능
```

---

## 빠른 시작

```bash
# 설치
pip install hirekit

# 설정 (API 키 입력)
hirekit configure

# 기업 분석
hirekit analyze 카카오

# 사용 가능한 데이터 소스 확인
hirekit sources
```

---

## 다음 단계

기업 분석 후 다음 명령어들을 사용할 수 있습니다:

```bash
# 회사 비교 (카카오 vs 네이버, 연봉과 성장성 중심)
$ hirekit compare 카카오 네이버 --focus salary,growth

# 채용공고와 이력서 매칭 (공고에 나온 요구사항 검토)
$ hirekit match https://wanted.co.kr/job-123 resume.pdf

# 이 회사의 면접 준비 (직무별 STAR 질문 생성)
$ hirekit interview 카카오 --role backend-engineer

# 이력서 리뷰 (이 회사에 맞춘 이력서 피드백)
$ hirekit resume review resume.pdf --company 카카오
```

👉 **[사용 설명서](docs/tutorial.md)** | **[CLI 명령어](docs/cli-reference.md)** | **[FAQ](docs/faq.md)**

---

## 핵심 기능

- **8개 데이터 소스 병렬 수집** — DART 공시, 네이버/구글/Brave/Exa 뉴스, Reuters, 한국 경제 전문지, GitHub 기술 스코어, 글래스도어 리뷰 (모두 동시에 수집)
- **12섹션 구조화 리포트** — 경영진 요약, 재무 건강, 기술 스택, 뉴스/궤적, 문화, 보상, 성장 가능성, 리스크, 면접 준비, 스코어카드, 유사 회사, 액션 아이템
- **5차원 가중 스코어카드** — 직무 적합도(30%), 경력 활용(20%), 성장 가능성(20%), 보상(15%), 문화(15%) = 100점 의사결정 점수
- **LLM 선택 사항** — AI 없이도 작동 (템플릿 모드), OpenAI/Anthropic/Ollama로 분석 강화 가능
- **플러그인 아키텍처** — 20줄의 Python으로 새 데이터 소스 추가 가능, 핵심 변경 없음
- **프라이버시 우선** — 모든 데이터 로컬 처리, 클라우드 업로드 없음, 외부 추적 없음

---

## 데이터 소스

| 소스 | 지역 | 데이터 종류 | API 키 필요 |
|------|------|-----------|----------|
| **DART** | 한국 | 공시 재무, 임원진, 인력 데이터 | `DART_API_KEY` |
| **네이버 뉴스** | 한국 | 최근 뉴스 기사 | `NAVER_CLIENT_ID` |
| **네이버 검색** | 한국 | 블로그, 카페, 웹 (문화/면접 정보) | `NAVER_CLIENT_ID` |
| **GitHub** | 글로벌 | 기술 성숙도 스코어링 | gh CLI |
| **구글 뉴스** | 글로벌 | RSS 뉴스 (별도 키 없음) | - |
| **신뢰할 수 있는 뉴스** | 글로벌 | Reuters, Bloomberg, FT, WSJ + 한국 경제지 | - |
| **Brave Search** | 글로벌 | 웹 + 뉴스 의미론적 검색 | `BRAVE_API_KEY` |
| **Exa Search** | 글로벌 | AI 의미론적 심층 검색 | `EXA_API_KEY` |

---

## 설정

`~/.hirekit/config.toml`에서 설정합니다:

```toml
[analysis]
default_region = "kr"
cache_ttl_hours = 168  # 7일

[llm]
provider = "none"  # openai, anthropic, ollama, none
model = "gpt-4o-mini"

[sources]
enabled = ["dart", "github", "naver_news"]

[output]
format = "markdown"
directory = "./reports"
```

---

## LLM 지원

HireKit은 LLM 없이도 작동합니다 (템플릿 기반 리포트). AI로 분석을 강화하려면:

```bash
# OpenAI
pip install hirekit[openai]
# ~/.hirekit/.env에 OPENAI_API_KEY 설정

# Anthropic
pip install hirekit[anthropic]

# Ollama (로컬 모델)
pip install hirekit[ollama]

# 또는 litellm (100+ 공급자)
pip install hirekit[llm]
```

---

## 로드맵

- [x] **Phase 1**: DART + GitHub + 뉴스 분석, 스코어카드, Markdown 리포트
- [x] **Phase 2**: JD 매칭 (`hirekit match`), 면접 준비 (`hirekit interview`), 이력서 리뷰 (`hirekit resume`)
- [ ] **Phase 3**: 미국 기업 (SEC Edgar), 웹 UI, 커뮤니티 플러그인, PyPI 공식 배포

---

## 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

**좋은 첫 기여:**
- 새 데이터 소스 플러그인 추가
- 리포트 템플릿 개선
- i18n 지원 추가

---

## 라이선스

MIT License. [LICENSE](LICENSE)를 참고해주세요.

---

<p align="center">
  <sub>모든 취업 준비자를 위해 만든 도구입니다.</sub>
</p>
