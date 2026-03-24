<p align="center">
  <h1 align="center">HireKit</h1>
  <p align="center">
    <strong>취업/이직 준비를 위한 AI 기업 분석 & 면접 준비 CLI</strong>
  </p>
  <p align="center">
    기업을 분석하고. 공고를 매칭하고. 면접을 준비하세요.
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/hirekit/"><img src="https://img.shields.io/pypi/v/hirekit" alt="PyPI"></a>
  <a href="https://github.com/zihoshin-dev/hirekit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"></a>
  <a href="https://github.com/zihoshin-dev/hirekit"><img src="https://img.shields.io/github/stars/zihoshin-dev/hirekit?style=social" alt="Stars"></a>
</p>

<p align="center">
  한국어 | <a href="README.md">English</a>
</p>

---

## 이런 경험, 있지 않나요?

면접장에 앉았습니다. 면접관이 묻습니다.

> **"왜 우리 회사에 지원하셨나요?"**

머릿속이 하얘집니다. 채용공고랑 회사 소개 페이지만 봤거든요.

기업 하나를 제대로 조사하려면:
- DART 공시 읽기 (재무제표, 직원수, 연봉...)
- 뉴스 10개 사이트 뒤지기
- 블라인드, 잡플래닛에서 리뷰 찾기
- GitHub에서 기술 스택 확인
- 그리고 이걸 하나로 정리하기

**평균 4-8시간.** 회사 3곳만 준비해도 일주일이 날아갑니다.

## HireKit이 해결합니다

```bash
pip install hirekit
hirekit analyze 카카오
```

**2분 후**: 8개 소스에서 자동 수집한 데이터로 만든 종합 분석 리포트 + 100점 만점 스코어카드가 나옵니다.

---

## 시작하기

### 1단계: 설치하기

```bash
pip install hirekit
```

> Python 3.11 이상이 필요합니다. 그 외 별도 설치는 없습니다.

### 2단계: API 키 준비하기 (선택사항)

API 키가 **하나도 없어도** 기본 분석이 가능합니다 (Google News + 해외 주요 언론은 키 없이 동작). 더 풍부한 분석을 원하면 아래 무료 키를 발급받으세요:

| 키 | 발급처 | 어떤 데이터를 얻나요? |
|----|--------|---------------------|
| DART API 키 | [opendart.fss.or.kr](https://opendart.fss.or.kr/) | 재무제표, 직원수, 평균연봉 (공식 공시) |
| 네이버 Client ID | [developers.naver.com](https://developers.naver.com/) | 뉴스, 블로그 면접후기, 카페 리뷰 |
| Brave API 키 | [brave.com/search/api](https://brave.com/search/api/) | 웹+뉴스 시맨틱 검색 |
| Exa API 키 | [exa.ai](https://exa.ai/) | AI 기반 딥서치 |

### 3단계: 설정하기

```bash
hirekit configure
```

이 명령어를 실행하면 `~/.hirekit/` 폴더에 설정 파일이 생깁니다.
`~/.hirekit/.env` 파일을 열어서 발급받은 키를 넣어주세요:

```bash
# ~/.hirekit/.env 파일 내용
DART_API_KEY=여기에_DART_키_붙여넣기
NAVER_CLIENT_ID=여기에_네이버_ID_붙여넣기
NAVER_CLIENT_SECRET=여기에_네이버_시크릿_붙여넣기
```

### 4단계: 기업 분석하기

```bash
hirekit analyze 카카오
```

이런 스코어카드가 나옵니다:

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

분석 리포트는 `./reports/카카오_analysis.md` 에 저장됩니다.

---

## 전체 명령어 가이드

HireKit은 취업 준비의 전 과정을 도와주는 7개 명령어를 제공합니다.

### `hirekit analyze` — 기업 분석

```bash
# 기본 분석 (Markdown 리포트 저장)
hirekit analyze 카카오

# 터미널에서 바로 확인
hirekit analyze 네이버 -o terminal

# JSON 출력 (다른 도구와 연동할 때)
hirekit analyze 토스 -o json

# 간단 분석 (핵심 섹션만)
hirekit analyze 쿠팡 --tier 3
```

**얻는 것**: 12섹션 구조화 리포트 + 5차원 100점 스코어카드.

### `hirekit match` — 채용공고 매칭

```bash
# 채용공고 URL을 넣으면 자동으로 파싱합니다
hirekit match "https://www.wanted.co.kr/wd/12345"

# 텍스트 파일로도 가능합니다
hirekit match jd.txt

# 내 프로필과 매칭하면 더 정확합니다
hirekit match jd.txt --profile ~/.hirekit/profile.yaml
```

**얻는 것**: 매칭 점수(0-100), 내가 부족한 역량(갭), 내 강점, 지원 전략.

### `hirekit interview` — 면접 준비

```bash
# 기업에 맞는 면접 질문 생성
hirekit interview 카카오

# 지원 포지션을 지정하면 더 구체적인 질문이 나옵니다
hirekit interview 카카오 --position "백엔드 개발자"

# 터미널에서 바로 확인
hirekit interview 네이버 --position PM -o terminal
```

**얻는 것**: 공통 질문 5개 + 직무 질문 + STAR 답변 프레임 + 역질문 5개.

### `hirekit coverletter` — 자기소개서 작성

```bash
# 기업에 맞는 자소서 4항목 초안 생성
hirekit coverletter 카카오 --position PM

# 내 프로필로 맞춤 자소서
hirekit coverletter 토스 --position PM --profile profile.yaml

# 터미널에서 미리보기
hirekit coverletter 네이버 -o terminal
```

**얻는 것**: 4항목 초안 (성장과정, 지원동기, 직무역량/입사후포부, 성격의장단점) + 항목별 피드백 + 점수.

### `hirekit proof` — 실행 메모

```bash
# 기업 분석을 바로 액션 메모로 압축
hirekit proof 카카오 --no-llm

# JD / 이력서 / 커리어 정보까지 반영
hirekit proof 토스 --jd jd.txt --resume resume.md --role 백엔드 --experience 5 --skills "python,aws,kafka"
```

**얻는 것**: verdict, 핵심 근거, 바로 할 일, low-confidence guardrail, 개인화 전략 요약.

### `hirekit resume` — 이력서 리뷰

```bash
# 이력서 파일을 분석합니다 (md, txt, pdf 지원)
hirekit resume 이력서.md

# 특정 채용공고 대비 리뷰 (키워드 갭 분석)
hirekit resume 이력서.md --jd "https://wanted.co.kr/wd/12345"

# 프로필과 함께
hirekit resume 이력서.pdf --profile profile.yaml
```

**얻는 것**: ATS 호환성 체크, 구조 분석, JD 대비 키워드 갭, 콘텐츠 품질 점수, 개선 제안.

### `hirekit strategy` — 커리어 전략

```bash
# 목표 기업 기준 적합도/갭 분석
hirekit strategy 카카오 --role PM --experience 5 --skills "sql,python,product"

# 프로필 YAML 기본값 사용 (경력/트랙/스킬 자동 반영)
hirekit strategy 토스 --profile ~/.hirekit/profile.yaml

# 자동화용 JSON 출력
hirekit strategy 네이버 --role backend --skills "python,aws,kafka" --output json
```

**얻는 것**: 적합도 점수, 접근 전략, 스킬 갭, 준비 기간, 대안 기업.

프로필 YAML을 주면 `years_of_experience`, `current_role`, `tracks`, `skills`, `education`
기본값을 읽어 와서 입력 반복을 줄여줍니다. CLI에서 직접 준 값이 있으면 그 값이 우선합니다.

### `hirekit compare` — 기업 비교

```bash
# 2개 기업 비교
hirekit compare 카카오 네이버

# 3개 기업 비교 + JSON 출력
hirekit compare 카카오 네이버 토스 --output json
```

**얻는 것**: 성장/보상/문화/기술/브랜드/WLB/원격근무 7차원 비교 + 종합 추천.

### `hirekit pipeline` — 워룸 파이프라인

```bash
# 기본 파이프라인
hirekit pipeline 카카오 --no-llm

# 현재 회사/경력/기술을 함께 넣어 전략까지 연결
hirekit pipeline 카카오 --current 라인 --current-role 백엔드 --position 백엔드 --experience 4 --skills "python,kafka,aws"

# 비교 기업까지 넣어 워룸처럼 판단
hirekit pipeline 카카오 --position PM --skills "sql,python,product" --compare 네이버 --compare 당근
```

**얻는 것**: Hero Verdict + Proof of Work + 개인화 전략 + 비교 요약이 한 리포트에 같이 들어갑니다. `--compare`를 생략해도 전략 엔진이 대안 기업을 제시하면 워룸 비교에 자동으로 연결됩니다.

### `hirekit jobs` — 채용 공고 탐색

```bash
# 터미널에서 현재 공고 확인
hirekit jobs 쿠팡

# JSON으로 전체 공고 추출
hirekit jobs 네이버 --output json
```

**얻는 것**: 현재 채용 포지션 목록, 부서/위치/고용형태/게시일 정보.

### `hirekit sources` — 데이터 소스 확인

```bash
hirekit sources
```

어떤 소스가 설정되어 있고 사용 가능한지 한눈에 보여줍니다:

```
                    Data Sources
┌────────────┬────────┬─────────────────┬────────────────┐
│ 이름       │ 지역   │ API 키          │ 상태           │
├────────────┼────────┼─────────────────┼────────────────┤
│ dart       │ KR     │ DART_API_KEY    │ Ready          │
│ github     │ GLOBAL │ -               │ Ready          │
│ google_news│ GLOBAL │ -               │ Ready          │
│ naver_news │ KR     │ NAVER_CLIENT_ID │ Not configured │
└────────────┴────────┴─────────────────┴────────────────┘
```

> "Not configured"로 표시된 소스는 API 키를 설정하면 활성화됩니다.

### `hirekit configure` — 초기 설정

```bash
hirekit configure
```

설정 파일(`config.toml`)과 환경변수 파일(`.env`)을 생성합니다.

---

## 데이터 소스 (8개 내장)

| 소스 | 지역 | 어떤 데이터? | API 키 | 무료? |
|------|------|-------------|--------|-------|
| **DART** | 한국 | 재무제표, 직원수, 평균연봉 (금감원 공시) | `DART_API_KEY` | 무료 |
| **네이버 뉴스** | 한국 | 최신 뉴스 기사 | `NAVER_CLIENT_ID` | 무료 |
| **네이버 검색** | 한국 | 블로그 면접후기, 카페 리뷰, 기업문화 정보 | `NAVER_CLIENT_ID` | 무료 |
| **GitHub** | 글로벌 | 기술 성숙도 스코어 (리포 수, 스타, 언어 다양성) | gh CLI 인증 | 무료 |
| **구글 뉴스** | 글로벌 | RSS 기반 최신 뉴스 | 키 불필요 | 무료 |
| **해외 주요 언론** | 글로벌 | Reuters, Bloomberg, FT, WSJ + 한경, 조선비즈 | 키 불필요 | 무료 |
| **Brave Search** | 글로벌 | 웹 + 뉴스 시맨틱 검색 | `BRAVE_API_KEY` | 무료 티어 |
| **Exa Search** | 글로벌 | AI 기반 시맨틱 딥서치 | `EXA_API_KEY` | 무료 티어 |

> API 키가 **하나도 없어도** 구글 뉴스 + 해외 주요 언론 + GitHub (gh CLI 설치 시)는 바로 사용 가능합니다.

---

## AI 분석 강화 (선택사항)

HireKit은 AI 없이도 잘 동작합니다 (템플릿 + 규칙 기반 리포트).
더 깊은 분석을 원하면 AI를 연결해보세요:

```bash
# OpenAI 사용
pip install "hirekit[openai]"

# Anthropic Claude 사용
pip install "hirekit[anthropic]"

# Ollama (로컬 모델, 완전 오프라인, 무료)
pip install "hirekit[ollama]"
```

`~/.hirekit/.env`에 키를 추가하고:

```bash
OPENAI_API_KEY=sk-...
```

`~/.hirekit/config.toml`에서 활성화합니다:

```toml
[llm]
provider = "openai"   # "anthropic", "ollama"도 가능
model = "gpt-4o-mini"
```

---

## 커리어 프로필 설정 (선택사항)

`~/.hirekit/profile.yaml` 파일을 만들면 매칭과 면접 준비가 개인화됩니다:

```yaml
name: "홍길동"
years_of_experience: 5

tracks:
  - name: "Product Manager"
    priority: 1

career_assets:
  - asset: "결제 시스템 구축"
    source: "전 직장"
    applicable_industries: ["핀테크", "이커머스"]

skills:
  technical: ["Python", "SQL", "데이터 분석"]
  domain: ["결제 시스템", "이커머스"]
  soft: ["크로스펑셔널 커뮤니케이션"]

preferences:
  regions: ["kr"]
  industries: ["핀테크", "플랫폼"]
  work_style: ["하이브리드"]
```

`--profile` 옵션과 함께 사용하면 내 경력에 맞춘 맞춤형 분석을 받을 수 있습니다.

---

## 자주 묻는 질문

**Q: Windows에서도 되나요?**
A: 네, Python 3.11+ 이 설치되어 있으면 Windows, macOS, Linux 모두 지원합니다.

**Q: API 키 없이도 사용할 수 있나요?**
A: 네. Google News, 해외 주요 언론, GitHub(gh CLI 설치 시)는 키 없이 동작합니다.

**Q: 분석 결과가 외부로 전송되나요?**
A: 아니요. 모든 데이터는 로컬에서만 처리됩니다. 외부 서버로 업로드하지 않습니다.

**Q: LLM(AI) 없이 쓰면 리포트 품질이 떨어지나요?**
A: 데이터 수집과 스코어링은 동일합니다. AI는 수집된 데이터를 종합 해석하는 부분만 강화합니다.

**Q: 어떤 기업을 분석할 수 있나요?**
A: DART에 등록된 모든 한국 상장사 + 주요 비상장 IT 기업 (토스, 당근, 무신사 등 30+개 사전 매핑).

---

## 커스텀 데이터 소스 만들기

나만의 데이터 소스를 추가하고 싶다면? Python 클래스 하나만 만들면 됩니다:

```python
from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult

@SourceRegistry.register
class MySource(BaseSource):
    name = "my_source"
    region = "global"
    sections = ["culture"]

    def is_available(self) -> bool:
        return True

    def collect(self, company, **kwargs):
        # 여기에 데이터 수집 로직을 작성합니다
        return [SourceResult(
            source_name=self.name,
            section="culture",
            data={"rating": 4.2},
            raw="회사 평점: 4.2/5",
        )]
```

자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

---

## 로드맵

- [x] **v0.1** — 기업 분석, 스코어카드, 8개 데이터 소스
- [x] **v0.1** — JD 매칭, 면접 준비, 이력서 리뷰, 자기소개서 코치
- [ ] **v0.2** — 미국 기업 지원 (SEC Edgar), 리포트 품질 개선
- [ ] **v0.3** — 웹 UI, 커뮤니티 플러그인, 에이전트 아키텍처

---

## 기여하기

기여를 환영합니다! 시작하기 좋은 작업들:

- 새로운 데이터 소스 추가 (Glassdoor, LinkedIn, SEC Edgar)
- 자기소개서 템플릿 개선
- 일본어/중국어 취업 시장 지원
- 스코어링 알고리즘 개선

[CONTRIBUTING.md](CONTRIBUTING.md)에서 개발 환경 설정 방법을 확인하세요.

---

## 라이선스

MIT License. [LICENSE](LICENSE) 참고.

<p align="center">
  <sub>더 나은 도구를 가질 자격이 있는 모든 취업 준비자를 위해 만들었습니다.</sub>
</p>
