# HireKit 파괴적 고도화 — 최종 마스터 플랜

> **3개 전문 에이전트 (Critic + Architect + Analyst) 교차 검토 후 통합**
>
> 원본: 문서 A (sisyphus trust-first 실행계획, 18 tasks) + 문서 B (외부연구 보강판, 35+ 논문)
>
> 원칙: **A의 골격 (trust-first, TDD, 의존성 DAG) + B의 근육 (데이터, 연구, UX)**

---

## 핵심 결정 사항

### 통합 원칙

| 결정 | 근거 |
|------|------|
| **문서 A가 실행 프레임워크** | TDD, 의존성 관리, 보안 경계, QA 프로토콜이 없으면 B의 기능들이 신뢰할 수 없는 블랙박스가 됨 |
| **문서 B가 전략적 방향** | 시장 분석, 경쟁 포지셔닝, 학술 근거, UX 연구가 없으면 A는 "무엇을 왜 만드는지" 설명 불가 |
| **MVP 3-4주, 전체 8-10주** | 40+ 태스크 병합은 비현실적. MVP로 핵심 가치 증명 후 확장 |

### 버린 것 (에이전트 합의)

세 에이전트 모두 동의한 제거 항목:

| 제거 항목 | 이유 |
|----------|------|
| **3-Agent Debate + Graph of Thoughts** | 비용 3x, 레이턴시 3x, TDD 불가. 단일 LLM + structured multi-pass로 동등 효과 (Architect) |
| **LightRAG + Neo4j** | 79개 기업에 과잉. pre-computed JSON이 80% 효과에 5% 복잡도 (Architect) |
| **면접 시뮬레이터 + 1000+ 질문 뱅크** | 별도 제품 규모. 기존 prep에 기업별 10-20개 추가로 충분 (Analyst) |
| **커리어 경로 예측 (LABOR-LLM)** | 7B fine-tuning + 한국어 데이터셋 부재. 학술 수준이지 제품 수준 아님 (Analyst) |
| **PWA + Service Worker** | 오프라인 기업 프로필 열람의 사용자 수요 근거 없음 (Critic) |
| **연례 Korea Career Report** | 마케팅 활동이지 제품 기능 아님 (Critic) |
| **나라장터/KIPRIS/Google for Jobs/국세청** | 통합 비용 대비 79개 기업 분석 기여도 미미 (Analyst) |
| **60단계 이력서 리라이팅** | 과잉. 5-8단계 structured pass로 90% 가치 (Architect) |
| **스타트업 생존 예측 (Gradient Boosting)** | ML 모델 학습 + 데이터셋 구축 = 별도 프로젝트 (Analyst) |

### 보류한 것 (Phase 2 백로그)

| 보류 항목 | 선결 조건 |
|----------|----------|
| ABSA 6차원 감성분석 | 리뷰 데이터 합법적 수집 경로 확정 |
| 이력서 AI 리라이팅 (5-8단계) | Hero verdict MVP 완성 후 |
| WCAG AA 전체 준수 | 사용자 규모 확보 후 |
| 편향 감사 루틴 | MVP에서 "advisory only" 라벨로 대응 |
| TheVC 투자 데이터 | 웹 수집 법적 리스크 검토 후 |
| 잡코리아/사람인 API | 개인/OSS 발급 가능 여부 확인 후 |

---

## 비전 & 포지셔닝

### 핵심 철학

> **"취업 준비자의 의사결정을 증거 기반으로 지원하는 trust-first 커리어 인텔리전스 도구"**

### Hero Workflow (문서 A에서 채택)

```
company + JD + resume → Apply / Hold / Pass verdict + evidence + next action
```

- **Apply**: 강한 매칭 + 높은 신뢰도 → 지원 전략 제시
- **Hold**: 중간 매칭 or 데이터 부족 → 추가 조사 권장
- **Pass**: 약한 매칭 + 높은 신뢰도 → 대안 기업 제시
- 모든 verdict는 **advisory only** — drill-down 가능한 증거 첨부

### 유일한 포지션 (문서 B에서 채택)

**한국 공공데이터 (DART+NPS) x 오픈소스 x Trust-first 증거 계약 x 무료 정적 사이트**

취준생이 가장 얻기 어려운 3가지 (잡코리아 n=1,252):
1. 조직문화 (26.6%) → **리뷰 감성 + NPS 퇴사율로 정량화**
2. 실제 연봉 (23.8%) → **DART 평균연봉 + 연차별 추정 범위**
3. 직원 만족도 (21.3%) → **NPS 고용 건강 지표 + 근속연수**

### Must NOT Have (가드레일, 문서 A에서 채택)

- 자동 지원/스팸 발송 자동화 없음
- 증거 없는 블랙박스 판정 없음
- 공개 경로에 개인 이력서/JD 발행 없음
- LLM이 확정적 사실/점수를 조용히 변조하는 것 없음

---

## 아키텍처 결정

### 배포 모델 (Architect 권고 채택)

| 표면 | 역할 | 제약 |
|------|------|------|
| **CLI (typer+rich)** | 전체 기능 — 분석, 매칭, verdict, 리포트 | LLM/SBERT 호출 가능, 사용자 API 키 |
| **MCP Server** | Claude Code 네이티브 통합 | CLI와 동일 엔진 |
| **GitHub Pages (docs/)** | 획득/데모 전용 — 정적 스냅샷 | 사용자 데이터 처리 불가, pre-computed JSON만 |

> **웹 데모의 범위**: 기업 스코어카드 열람, 기업 비교, 사전 계산된 결과 표시.
> JD 분석기/이력서 체커는 **클라이언트 사이드 휴리스틱** (키워드 매칭, 정규식 기반)으로 구현.
> SBERT/LLM 기반 분석은 CLI 전용.

### 데이터 흐름 (통합)

```
Sources (14 기존 + 2~4 신규)
    ↓
SourceResult (+ evidence_id, cross_validated, trust_label)  ← 3개 필드 추가
    ↓
Cross-Validation Engine (2+ 소스 일치 시 confidence 상승)
    ↓
Confidence/Contradiction Rules (staleness, authority, disagreement)
    ↓
Trust Label Assignment (verified / derived / generated / stale / unknown)
    ↓
Structured Multi-Pass LLM (재무 → 문화 → 기술, 단일 에이전트 3회 호출)
    ↓
Scoring Engine (가중 복합 스코어 + confidence 계수)
    ↓
Hero Verdict Orchestrator (Apply / Hold / Pass + evidence + next action)
    ↓
Output: CLI Report | MCP Tool | Static JSON Snapshot (docs/demo/data/)
```

### 신규 데이터 소스 (4개만, Analyst 권고)

| 소스 | 근거 | 구현 |
|------|------|------|
| **국민연금 NPS** | 유일한 월별 입퇴사 시그널 (100인+ 사업장에서 유의미) | `sources/kr/pension.py` 확장 |
| **DART 심화** | 임원보수 (CEO Pay Ratio), 지분변동 (M&A 시그널) | `sources/kr/dart.py` 확장 |
| **국세청 사업자등록** | 사업자 상태 (정상/휴폐업) — 기본 viability gate | `sources/kr/nts_biz.py` 확장 |
| **Stack-Analyser** | GitHub 공개 레포에서 700+ 기술 감지 | `sources/global_/github.py` 확장 |

> NPS "Hidden Moat" 주의사항 (Analyst): 5인 이하/10인 이하 등 **버킷 데이터**라
> 스타트업 분석에 거의 무용. **100인+ 사업장에서만 유의미한 지표**임을 명시할 것.
> 실증 필요: 먼저 10개 기업 API 호출 → 분석 가치 판단 → 파이프라인 구축 결정.

### 스코어카드 재설계

```
Company Score = Σ(wi × Di × Ci)

Di = 차원별 점수 (0-5)
wi = 가중치
Ci = 신뢰도 계수 (0.5-1.0, 소스 수·교차검증·freshness 기반)
```

| 차원 | 가중치 | 1차 소스 | Trust Label 매핑 |
|------|--------|---------|-----------------|
| Job Fit | 25% | GitHub, 기술블로그, JD 매칭 | verified (API) / derived (추론) |
| Growth | 20% | DART 재무제표 | verified (공시) |
| Compensation | 15% | DART 인사, NPS 추정 | verified (공시) / derived (NPS) |
| Culture Fit | **25%** | 커뮤니티 리뷰, NPS 퇴사율 | derived / generated |
| Career Leverage | 15% | 뉴스, 기업 규모, 브랜드 | derived |

**신뢰도 정책** (문서 A + B 통합):
- trust_label이 `unknown`/`stale`인 차원: 점수 표시 안 함, "데이터 부족" 라벨
- n < 50 리뷰: Wilson Score Interval 적용
- 소스 1개: Bayesian Shrinkage (모집단 평균 방향)
- **절대 confidence bounds 없이 점수 표시하지 않음**

### 스킬 매칭 (문서 B 채택, 단계적)

| 단계 | 방식 | 정확도 | 시점 |
|------|------|--------|------|
| **MVP** | SBERT ko-sroberta (CLI only) + ESCO 정규화 | ~82% | Phase 1 |
| **v2** | + LLM 스킬 추출 (Skill-LLM zero fine-tuning) | ~87% | Phase 2 |
| **웹 데모** | 사전 계산된 매칭 결과 JSON 표시 | N/A | Phase 1 |

### LLM 전략 (통합, Multi-Agent → Structured Multi-Pass)

```
단일 LLM + 3회 structured output 호출:
  Pass 1: 재무 분석 (DART 데이터 → 구조화 JSON)
  Pass 2: 문화/조직 분석 (리뷰+뉴스 → 구조화 JSON)
  Pass 3: 기술/성장 분석 (GitHub+블로그 → 구조화 JSON)

  → Contradiction Detection (3개 패스 간 불일치 감지)
  → Verdict Synthesis (Apply/Hold/Pass + evidence)
```

- Hero verdict 1건당 **LLM 호출 5-6회**, 비용 **$0.03-0.05** (gpt-4o-mini)
- 실패/거부 시 `generated`/`unknown` trust label 부여, 빈 분석으로 위장 금지
- refusal semantics: "이 차원에 대한 데이터가 부족해요" 명시

---

## 실행 로드맵

### Phase 1: MVP — Trust + Hero Verdict (3-4주)

> 목표: "증거 기반 지원 판단" 단일 워크플로우 완성

**Wave 0 — Foundation (3일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T1 | Trust ADR + 라벨 택소노미 (verified/derived/generated/stale/unknown) | A |
| - | `_meta` 필드 스펙을 T1 산출물에 포함 | B |
| - | LLM 비용 예산 모델 (verdict 1건당 $0.05 상한) | 신규 |

**Wave 1 — Data Contract (5일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T2 | Evidence lineage — SourceResult에 `evidence_id`, `cross_validated`, `trust_label` 추가 | A+Architect |
| T3 | Hero benchmark fixture (company + JD + resume, 정상/저데이터 각 1건) | A |
| T5 | Company identity/alias 정규화 (79개 기업 검증 포함) | A |
| - | 하드코딩 제거 → `company_db.py` (동적 로드) | B |

**Wave 2 — Engine Upgrade (7일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T4 | Cache-fidelity 수정 (scorecard/source_results 캐시 복원 보존) | A |
| T6 | Dataset governance (79개 기업 freshness + 일관성 검증) | A |
| T7 | Structured LLM output + refusal handling | A |
| - | SBERT ko-sroberta JD 매칭 (tech_taxonomy.py 대체) | B |
| - | DART 심화 (임원보수/지분변동 2-3개 엔드포인트) | B |

**Wave 3 — Verdict (5일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T8 | Contradiction/confidence engine | A |
| T9 | Hero verdict orchestrator (Apply/Hold/Pass) | A |
| T10 | Verdict-first 리포트 모델 | A |
| T11 | Career strategy transferability (신입/경력/전직 분기) | A |

**Wave 4 — Public Surface (5일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T13 | Demo snapshot schema (trust label 반영) | A |
| T14 | Demo 리디자인 (Progressive Disclosure 3계층) | A+B |
| T16 | Landing page 리포지셔닝 (hero workflow 중심) | A+B |
| - | ECharts 6 레이더 + Chart.js 연봉 바 | B |
| - | Fuse.js 검색 + 필터 | B |

**Wave 5 — Release Gate (2일)**

| # | 태스크 | 출처 |
|---|--------|------|
| T18 | Eval harness + regression gate | A |

**Phase 1 산출물**:
- [ ] 고정 fixture에서 hero verdict 안정 재현
- [ ] 공개 copy/demo/update_log 내부 일관성
- [ ] 모든 점수에 drill-down 가능한 evidence 또는 `unknown` 라벨
- [ ] SBERT 시맨틱 JD 매칭 (CLI)
- [ ] 리디자인된 demo + landing

---

### Phase 2: 확장 — 데이터 심화 + 웹 도구 (4-6주)

> 선결 조건: Phase 1 완료, NPS 실증 완료, 리뷰 데이터 수집 경로 확정

| # | 태스크 | 근거 |
|---|--------|------|
| 1 | NPS 국민연금 파이프라인 (실증 후 구축) | B — Hidden Moat |
| 2 | ESCO/KECO 스킬 택소노미 정규화 | B — 표준화 |
| 3 | LLM 스킬 추출 (Skill-LLM, zero fine-tuning) | B — +5% 정확도 |
| 4 | 스코어카드 가중치 재설계 (Culture 25%) | B — 2030세대 설문 |
| 5 | 이력서 AI 리라이팅 (5-8단계 structured pass) | B — 간소화 |
| 6 | Proof-of-work artifact generator | A — T12 |
| 7 | 웹 JD 분석기 (클라이언트 사이드 휴리스틱) | B |
| 8 | 웹 이력서 ATS 체커 (클라이언트 사이드) | B |
| 9 | 웹 기업 비교기 (ECharts 레이더 오버레이) | B |
| 10 | WCAG AA 핵심 (3중 인코딩 등급, 4.5:1 대비) | B |
| 11 | Stack-Analyser GitHub 기술 스택 연동 | B |
| 12 | 편향 감사 루틴 (인구통계 익명화 + 지역 감사) | B — T7에 통합 |

---

### Phase 3: R&D 백로그 (검증 후 선택적)

| 항목 | 선결 조건 |
|------|----------|
| ABSA 6차원 감성분석 | 리뷰 데이터 합법적 수집 경로 |
| 기업 지식 그래프 (LightRAG 아닌 pre-computed JSON) | 500+ 기업 달성 시 |
| 사용자 프로필 시스템 (profile.yaml) | PIPA 컴플라이언스 검토 |
| 경력기술서 STAR 추출 | Phase 2 이력서 기능 안정화 후 |
| 잡코리아/사람인 API 연동 | 개인/OSS 발급 확인 후 |
| TheVC 투자 데이터 | 법적 리스크 검토 후 |
| 연봉 계산기 (세후/4대보험) | 웹 도구 안정화 후 |
| 면접 질문 뱅크 확장 (200→500) | 기업별 데이터 축적 후 |
| SEO (hash routing, OG 이미지, JSON-LD) | 트래픽 기반 확보 후 |
| 한국어/영어 i18n 아키텍처 | 글로벌 확장 결정 시 |

---

## 기술 사양

### SourceResult 확장 (Architect 권고, 최소 변경)

```python
@dataclass
class SourceResult:
    source_name: str
    section: str
    data: dict
    url: str | None = None
    collected_at: datetime | None = None
    confidence: str = "medium"     # 기존
    evidence_id: str = ""          # 신규 — lineage 추적
    cross_validated: bool = False  # 신규 — 2+ 소스 일치 여부
    trust_label: str = "unknown"   # 신규 — verified/derived/generated/stale/unknown
```

### Trust Label 택소노미

| Label | 의미 | 예시 |
|-------|------|------|
| `verified` | 공식 소스에서 직접 확인 | DART 재무제표, GitHub API |
| `derived` | 확인된 데이터에서 계산/추론 | NPS 퇴사율 추정, 성장률 계산 |
| `generated` | LLM이 생성한 해석/요약 | 산업 분석, 문화 해석 |
| `stale` | 90일+ 경과된 데이터 | 캐시된 뉴스, 오래된 리뷰 |
| `unknown` | 데이터 없음 또는 검증 불가 | 비상장 스타트업 재무 |

### 성능 예산

| 작업 | 목표 |
|------|------|
| Hero verdict (캐시 히트) | < 2초 |
| Hero verdict (캐시 미스) | < 30초 |
| 79개 기업 배치 갱신 | < 60분 |
| 웹 First Paint (3G) | < 2초 |
| Verdict 1건 LLM 비용 | < $0.05 |

### 시각화 (웹 데모)

| 용도 | 라이브러리 | 근거 |
|------|-----------|------|
| 레이더 차트 (6D) | ECharts 6 CDN | 레이더 품질 10/10, 터치 최적화 |
| 연봉 바 차트 | Chart.js v4 CDN | 73% 작은 번들, ARIA 최고 |
| 기업 비교 히트맵 | ECharts 6 | 비기술 사용자 즉시 해석 |
| 기업 검색 | Fuse.js (8KB) | Lunr.js 대비 73% 경량 |

### 접근성 (핵심만)

| 항목 | 사양 |
|------|------|
| 등급 인코딩 | 3중 (색상 + 모양 + 텍스트) |
| 텍스트 대비 | 4.5:1 이상 (WCAG AA) |
| 모바일 탭 | 48dp 최소 |
| 차트 | `aria-label` 대체 텍스트 |

---

## 검증 전략

### TDD 정책 (문서 A 채택)

- 모든 태스크: 실패 테스트 먼저 → 최소 구현 → 리팩터
- 프레임워크: `pytest`
- Evidence: `.sisyphus/evidence/task-{N}-{scenario}.{ext}`

### 핵심 검증 기준

| 기준 | 측정 |
|------|------|
| Verdict 안정성 | 고정 fixture 반복 실행 시 동일 결과 |
| Trust 일관성 | 모든 점수에 trust_label 존재 |
| 캐시 무결성 | hit/miss 동일 scorecard/provenance |
| 공개 안전성 | docs/ 경로에 개인 데이터 없음 |
| 데모 일관성 | README/demo/update_log 기업 수 일치 |

### Definition of Done (Phase 1)

- [ ] 고정 fixture로 hero verdict 안정 재현
- [ ] 공개 copy, demo data, update status 내부 일관
- [ ] 공개 경로에 개인 artifact 없음
- [ ] 모든 점수/추천에 evidence drill-down 또는 `generated`/`unknown` 라벨
- [ ] Demo, tools, landing이 동일 hero workflow와 trust contract 반영

---

## 미해결 질문 (실행 전 확정 필요)

| # | 질문 | 담당 | 영향 |
|---|------|------|------|
| 1 | 잡플래닛/블라인드 리뷰 데이터 합법적 수집 경로? | 법적 검토 | ABSA, 문화 분석 전체 |
| 2 | NPS API 실증 — 10개 기업 호출 후 분석 가치 확인 | Phase 1 Wave 2 | NPS 파이프라인 구축 여부 |
| 3 | 잡코리아/사람인 API 개인/OSS 발급 가능? | API 신청 | 채용공고 데이터 소스 |
| 4 | 비상장 스타트업 (DART 없음) verdict 전략? | T9 설계 시 | "Unknown" 허용 범위 |
| 5 | 사용자에게 LLM API 키 입력 요구? vs 내장? | 비즈니스 모델 | 비용 구조 |

---

## 경쟁 포지셔닝 (문서 B에서 채택)

| 플랫폼 | 강점 | HireKit이 이기는 곳 |
|--------|------|-------------------|
| 잡플래닛 | 리뷰 깊이, 고용보험 인증 | 재무 교차검증, 투명한 스코어링, 오픈소스 |
| 원티드 | AI 매칭, 모바일 UX | 공공데이터 독점 활용, CLI 자동화, trust label |
| 블라인드 | 솔직한 내부 인사이트 | 정량 분석, 시계열 트렌드, 비개발자 접근성 |
| Levels.fyi | 연봉 시각화, 레벨 정규화 | 한국 시장 특화, 문화/면접/커리어 통합 |
| Glassdoor | 글로벌 커버리지 | 한국 공공데이터, evidence-backed verdict |

**HR Tech 시장**: 한국 1.65조원 (2025, CAGR 6.6%)

---

## 참고 문헌 (핵심만)

### 학술 논문

| 논문 | 학회 | HireKit 적용 |
|------|------|-------------|
| Resume-JD Matching with LLMs | MDPI 2025 | 하이브리드 매칭 87% 정확도 |
| Skill-LLM | ArXiv:2410.12052 | Zero fine-tuning 스킬 추출 |
| Multi-Agent Debate | ICML 2024 | → Structured multi-pass로 대체 |
| Corporate Failure Prediction | MDPI JRFM 2025 | ML > Altman Z-Score |
| EVP Mining via ABSA | ScienceDirect 2025 | 고용주 브랜드 분석 (Phase 2) |
| Big City Bias | NLP4HR 2024 | 지역 편향 감사 |

### 데이터 소스

| 소스 | 접근 | MVP 포함 |
|------|------|---------|
| DART OpenAPI (83개) | 공공 API | Yes |
| 국민연금 NPS | data.go.kr | 실증 후 |
| ESCO v1.2.0 | CC BY 4.0 | Phase 2 |

### UX 연구

| 출처 | 적용 |
|------|------|
| NNGroup Progressive Disclosure | 3계층 정보 구조 |
| Highcharts / Bold BI | 레이더 6차원 최적 |
| WCAG 2.2 AA | 3중 인코딩 등급 |

---

*이 문서는 Critic, Architect, Analyst 3개 전문 에이전트의 교차 검토를 거쳐 통합되었습니다.*
*문서 A의 실행 규율 + 문서 B의 전략적 비전 + 3개 에이전트의 현실성 검증을 반영합니다.*
