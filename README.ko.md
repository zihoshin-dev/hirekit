<p align="center">
  <h1 align="center">HireKit</h1>
  <p align="center">
    <strong>취업/이직 준비자를 위한 AI 기반 기업 분석 & 면접 준비 CLI</strong>
  </p>
  <p align="center">
    기업을 분석하고, 공고를 매칭하고, 면접을 준비하세요.
  </p>
</p>

---

## HireKit이란?

HireKit은 취업/이직 준비자를 위한 오픈소스 CLI 도구입니다.
DART 공시, 뉴스, GitHub, 채용공고 등 다중 소스에서 기업 데이터를 자동 수집하고,
구조화된 분석 리포트를 생성하며, 면접 준비까지 도와줍니다.

**문제**: 기업 하나를 제대로 조사하려면 4-8시간이 걸립니다.

**해결**: `hirekit analyze 카카오` 한 줄이면 종합 리포트가 나옵니다.

## 핵심 기능

- **다중 소스 자동 수집** — DART 공시, 뉴스, GitHub 기술 스코어링 등
- **12섹션 구조화 리포트** — 재무, 문화, 기술, 경쟁 구도 등 종합 분석
- **가중 스코어카드** — 5차원 100점 만점 평가 (감이 아닌 데이터 기반)
- **LLM 선택적** — AI 없이도 동작 (템플릿 모드), OpenAI/Anthropic/Ollama로 강화
- **플러그인 아키텍처** — Python 인터페이스로 데이터 소스 추가
- **프라이버시 우선** — 모든 데이터 로컬 처리, 외부 전송 없음

## 빠른 시작

```bash
# 설치
pip install hirekit

# 설정 (API 키 등)
hirekit configure

# 기업 분석
hirekit analyze 카카오

# 사용 가능한 데이터 소스 확인
hirekit sources
```

## 데이터 소스

| 소스 | 지역 | 데이터 | API 키 |
|------|------|--------|--------|
| DART | 한국 | 공시, 재무, 인력 데이터 | 필요 |
| 네이버 뉴스 | 한국 | 최근 뉴스 기사 | 필요 |
| GitHub | 글로벌 | 기술 성숙도 스코어링 | gh CLI |

## 로드맵

- [x] **Phase 1 (MVP)**: DART + GitHub + 뉴스 분석, 스코어카드, Markdown 리포트
- [ ] **Phase 2**: JD 매칭, 면접 준비, 이력서 리뷰
- [ ] **Phase 3**: 해외 기업 (SEC Edgar), 웹 UI, 커뮤니티 플러그인

## 기여하기

기여를 환영합니다! [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해주세요.

## 라이선스

MIT License
