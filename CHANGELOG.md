# Changelog

All notable changes to HireKit are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.0] - 2026-03-22

### Added
- **JD Analysis Engine** — tech taxonomy 60개+, URL/파일 지원, 3단계 갭 분석 (`hirekit jd`)
- **Interview Prep** — 200개+ 질문 DB, 직무별 맞춤 STAR 가이드, 시뮬레이션 모드 (`hirekit interview`)
- **Resume Feedback Engine** — 정량 피드백, ATS 호환성 점수, JD 대비 키워드 갭 분석 (`hirekit resume`)
- **Cliché Detector** — 100개+ 클리셰 패턴 감지, 4항목 차별화 점수 (자소서)
- **Vision & AI Strategy Sections** — 기업 분석에 비전·AI전략 섹션 추가
- **IR Report Source** — IR 리포트, 글로벌 분석, 사업부문 데이터 수집
- **Security Hardening** — defusedxml, 입력 검증, 안전한 파일 처리
- **Content-based Scoring** — 데이터 기반 스코어카드 알고리즘 재설계
- **CI/CD Overhaul** — GitHub Actions 파이프라인 완전 재구성

### Changed
- README 전면 재작성 (v0.3.0 기능 반영, 30초 규칙 구조)
- `StrEnum` 마이그레이션, line-length 120 적용
- CLI UX 개선: 명령어 충돌 해소, 오류 메시지 개선
- 80개 기업 DB에 industry, tech stack, scorecard, vision, AI strategy 데이터 추가

### Fixed
- CLI coexistence 이슈 (타 CLI 도구와 충돌) 해결
- 4개 버그 수정, 테스트 160개 추가 (커버리지 23% → 55%)

### Tests
- **344 tests passing** (0.93s)

---

## [0.2.0] - 2026-03-22

### Added
- **LLM Pipeline** — OpenAI(GPT-4o-mini), Anthropic(Claude) 어댑터, litellm 통합
- **Integrated Pipeline Command** — 분석→매칭→면접→이력서→자소서 5단계 통합 (`hirekit pipeline`)
- **Jinja2 Report Rendering** — MarkdownRenderer, JSONRenderer, TerminalRenderer
- **6 New Data Sources** — 총 14개 소스 (8→14): credible_news, company_website, tech_blog, medium_velog, career_page, linkedin_search
- **Data Normalizer** — 재무 데이터 정규화 + 템플릿 포매팅
- **자기소개서 Coach Engine** — 한국어 자소서 분석·코칭
- **80-company Demo DB** — Phase A/B/C 완성, 인터랙티브 데모 페이지

### Changed
- v0.1.0 8개 소스 → v0.2.0 14개 소스로 확장
- 재무 테이블 템플릿 정규화 데이터 포맷 정렬

### Removed
- Gemini/Ollama/OpenRouter/Groq 어댑터 제거 (litellm으로 통합)

---

## [0.1.0] - 2026-03-21

### Added
- **Initial project scaffold** — HireKit v0.1.0
- **8 Data Sources** — DART, GitHub, Naver News, Naver Search, Google News, Brave Search, Exa Search, Community Review
- **5-Dimension Scorecard** — 재무·기술·문화·성장·보상 스코어카드
- **JD Matcher** — 채용공고 매칭 기본 엔진
- **Interview Prep** — 기본 면접 준비 모듈
- **Resume Advisor** — 이력서 분석 기본 기능
- **Phase 2 Engine Tests** — 20개 테스트 (총 39개)
- **DART corp_code Resolution** — 기업코드 자동 조회 및 5개 추가 소스

### Architecture
- `hatchling` 기반 빌드 시스템
- `pyproject.toml` dynamic version (`src/hirekit/__init__.py`)
- Python 3.11+ 지원
- Entry-points 플러그인 아키텍처 (sources, outputs)

---

[0.3.0]: https://github.com/zihoshin-dev/hirekit/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/zihoshin-dev/hirekit/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zihoshin-dev/hirekit/releases/tag/v0.1.0
