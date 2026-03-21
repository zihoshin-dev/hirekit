# HireKit 리포트 품질 가이드

## 개요

HireKit이 생성하는 12섹션 분석 리포트의 글쓰기 및 데이터 품질 기준을 정의합니다.

모든 리포트는 **6가지 정보층** 통과 + **12섹션별 품질 체크리스트** 완료 후 배포됩니다.

---

## 6가지 정보층

### Layer 1: 정보 정확도 (Accuracy)

모든 데이터는 검증 가능한 소스가 있어야 합니다.

```
✅ Good:
"연매출 12.3조 원 (DART 2024년 반기보고서, 기준일: 2024-06-30)"

❌ Bad:
"연매출이 12.3조 원 정도입니다"
"연매출 12.3조 원 (매년 증가)"
```

**체크리스트**:
```
[ ] 모든 재무 수치: DART 공시건 + 기준일 표시
[ ] 모든 뉴스: 링크 + 발행일
[ ] 모든 통계: 샘플 수 (N=45명)
[ ] 모든 추정/추측: "(추정)", "(가능성)", "(추측)" 명시
[ ] 오래된 데이터: "(2023년 기준, 최신 정보 필요)" 표시
```

---

### Layer 2: 취업자 관점 (Job Seeker Lens)

모든 기업 정보를 "당신의 커리어에 어떤 영향"으로 재해석합니다.

#### 재무 데이터 → 연봉 영향

```
❌ Bad:
"연매출 12.3조 원, 영업이익 2.7조 원"

✅ Good:
"연매출 12.3조 원 × 22% 이익률 = 당신의 연봉 인상 가능성 높음
(매년 15% 성장 중이므로 인상폭 추가 기대 가능)"
```

#### 기술 스택 → 면접 전략

```
❌ Bad:
"Python, Kubernetes, PostgreSQL 사용"

✅ Good:
"Python (5년 업계표준 — 면접서 깊이있는 ORM/동시성 질문 예상)
/ Kubernetes (신기술, '배우고 싶다'는 의욕 표현 기회)
/ PostgreSQL (당신의 3년 경험이 강점)"
```

#### 문화 정보 → 실무 환경 예상

```
❌ Bad:
"좋은 회사 문화"

✅ Good:
"재택 3일 (블라인드 평가 45건 기준, 호평률 78%)
+ 주 1회 전사 미팅 (확인됨)
→ 자율성 있되 팀 연결감 유지하는 환경"
```

**체크리스트**:
```
[ ] 모든 재무 지표 → 연봉/보상 관점 재해석
[ ] 모든 기술 스택 → 면접 준비 각도 포함
[ ] 모든 문화 정보 → "당신이 실제로 경험할 것" 구체화
[ ] 모든 뉴스 → "취업자에게 의미 있는가?" 필터링
[ ] 리스크 → "당신 입장에서 위협인가?" 명시
```

---

### Layer 3: 스캔 가능성 (Scannability)

바쁜 취업자가 **2분 안에 핵심을 파악**할 수 있도록.

#### 제목 계층 명확화

```
❌ 모호함:
"## 회사 정보"
"### 재정"

✅ 명확함:
"## 재무 건강도 (연봉 협상 가능한가?)"
"### 연매출 성장률 15% YoY"
```

#### 문단 구조 (3줄 룰)

```
❌ Dense:
"이 회사는 2010년에 설립되었고, 현재 2,500명의 직원이 있으며,
최근 3년간 평균 15% 연간 성장률을 기록했고, 이는 업계 평균 8%보다
두 배 이상 높으며, 따라서 팀 확장이 활발할 것으로 예상됩니다."

✅ Scannable:
"연매출 성장률: 15% YoY (업계 평균 8% 대비 2배)
→ 팀 확장 활발, 프로모션 기회 높음"
```

#### 번호/강조 활용

```
❌ 평탄:
"연매출은 12.3조 원이고 영업이익은 2.7조 원입니다."

✅ 강조:
"**연매출**: 12.3조 원 (**영업이익률**: 22%)
→ 당신의 연봉 인상 가능성: **높음**"
```

**체크리스트**:
```
[ ] 모든 섹션 제목: 첫 단어가 수치 또는 "언제"
[ ] 모든 문단: max 3줄 (긴 문장은 bullet으로 분해)
[ ] 모든 key metric: **bold** 처리
[ ] 모든 해석: 문단 마지막에 "→ [당신에게 미치는 영향]"
[ ] 섹션별 max 300 tokens (전체 <8,000)
```

---

### Layer 4: 행동 가능성 (Actionability)

리포트를 읽은 후, 취업자가 **구체적 다음 단계**를 알아야 합니다.

#### 리스크 → 대응 전략

```
❌ 정보만:
"최근 3개월 수익률이 마이너스입니다."

✅ 행동 지향:
"최근 3개월 수익률 -8% (리스크)
→ 대응 전략: 면접서 '회복 전략이 뭔가요?' 질문하고,
  실적 좋은 부서/팀 선호하기"
```

#### 강점 → 면접 공략

```
❌ 설명만:
"기술 스택이 현대적입니다."

✅ 행동 지향:
"기술 스택 Kubernetes (당신이 배우는 중)
→ 면접 전략: '최근 Kubernetes 학습 중인데, [작은 프로젝트] 완료했습니다.
  당신들은 어떤 도전이 있었나요?' 질문으로 배움의 의욕 + 호기심 표현"
```

#### 약점 → 준비 항목

```
❌ 문제 제시:
"경쟁 회사들보다 연봉이 낮습니다."

✅ 준비 항목:
"경쟁 회사(네이버, 카카오)보다 연봉 10% 낮음
→ 면접 대응: 연봉보다 '성장 기회' 강조. 이직 후 2년 기술 성장 → 이직 가능.
  협상 레버: '시장 가격은 X원인데, 우리의 차이는 무엇인가?' 묻기"
```

**체크리스트**:
```
[ ] 모든 리스크: 최소 2개 대응 전략 제시
[ ] 모든 강점: 면접에서 어떻게 활용할지 명시
[ ] 모든 약점: 준비 항목으로 변환 (학습 경로 제시)
[ ] Action Items 섹션: Checkbox로 구성 (실행 가능)
[ ] 모든 조언: 1주일 내에 실행 가능한 수준
```

---

### Layer 5: 톤 & 열정 (Tone & Authenticity)

희망적이면서도 현실적인 톤 유지.

#### 희망적이되 신뢰성 있게

```
❌ 과도한 낙관:
"완벽한 회사입니다! 반드시 지원하세요!"

❌ 과도한 비관:
"여러 리스크가 있어 권장하지 않습니다."

✅ 균형:
"좋은 기회입니다. 3가지 준비하면 성공 가능성 높습니다.
리스크도 있지만, 대응 전략이 명확합니다."
```

#### 당신(지원자) 중심

```
❌ 회사 중심:
"회사의 성장 궤적이 인상적입니다."

✅ 당신 중심:
"회사의 성장이 당신의 연봉 인상과 기술 성장 가능성을 높입니다."
```

#### 격식체 일관성 (한국어의 경우)

```
체크사항:
[ ] 존댓말 일관 (종결 어미: 습니다, 입니다)
[ ] 오타 제로 (띄어쓰기: "더 중요한", 겹받침: "값이")
[ ] 호칭 일관 (당신, 지원자, "당신이")
[ ] 시제 명확 (과거: 2024년 기준, 미래: 예상)
```

**체크리스트**:
```
[ ] 리포트 톤: 전문적이되 친근함
[ ] 모든 주장: 근거 + 기대 + 조건 (3가지)
[ ] 부정적 정보: "위험" not "악" (tone)
[ ] 긍정적 정보: "기회" not "약속" (realism)
[ ] 마지막 문단: "도움이 되길 바랍니다" 마무리
```

---

### Layer 6: 근거 충분성 (Evidence)

모든 주장은 최소 2개 이상의 독립적 소스로 뒷받침되어야 합니다.

#### 1개 소스만? → 추측 표시

```
❌ 단일 소스 (신뢰도 낮음):
"회사 문화가 좋습니다." (출처: 블라인드 1개 기사)

✅ 복합 소스 (신뢰도 높음):
"좋은 회사 문화 (블라인드 평가 45건 평균 4.2/5 + 네이버 리뷰 78% 호평)"
```

#### 부재한 정보? → 명시

```
❌ 무시:
"직급별 연봉" (정보 없어도 제시 안 함)

✅ 명시:
"직급별 연봉: 정보 부재 (DART 공시에 평균만 기록)
→ 대응: 면접서 '신입 기준 연봉 범위가 어떻게 되나요?' 직접 질문"
```

**체크리스트**:
```
[ ] 모든 수치: 최소 2개 소스 (또는 1개 공식 + 기준일)
[ ] 모든 문화 정보: 샘플 수 표시 (N=45명)
[ ] 모든 뉴스: 링크 + 발행일
[ ] 부재한 정보: 명시 + 해결책 제시
[ ] 오래된 정보: 연도 표시 ("2023년 기준")
[ ] 출처 섹션: 마지막 정보 일목요연
```

---

## 12섹션별 품질 체크리스트

### 1. Executive Summary (100 tokens)

**목표**: 3분 만에 의사결정, "yes/no/maybe"

```markdown
## Executive Summary

**종합 점수**: 82/100 — Grade A (Strong Opportunity)

**핵심 3가지 이유**:
1. **성장 중** — 연매출 15% YoY + 팀 확장 (프로모션 기회)
2. **기술 깊이** — 현대적 스택(Python/Kubernetes) + 깊이있는 기술 질문 예상
3. **연봉 협상 가능** — 이익률 22% + 경쟁사 대비 시장가격

**의견**: 좋은 기회. 3가지 준비(기술 학습 + 면접 전략 + 협상 레버)하면 성공률 높음.
```

**체크리스트**:
```
[ ] 점수가 명확 (0-100)
[ ] 3가지 이유가 구체적 (수치 기반)
[ ] 당신에게 미치는 영향 명시
[ ] 의견이 균형잡음 (희망 + 현실)
[ ] 100 tokens 이내
```

---

### 2. Financial Health (300 tokens)

**목표**: 당신의 연봉/보상 가능성 판단

```markdown
## Financial Health

**연매출**: 12.3조 원 (작년 대비 **+15.2%**)
**영업이익률**: 22.4% (산업 평균 18%)
**부채비율**: 45% (안전 기준: <60%)

**당신에게 미치는 영향**:
✅ 성장 중 → 연봉 인상 가능성 높음
✅ 높은 이익률 → 보너스 및 복리후생 개선 가능
⚠️ 국제 확장 중 → 일시적 현금 흐름 주의 필요

**근거**:
- DART 2024년 반기보고서 (기준일: 2024-06-30)
- 동종 산업군 평균 비교 (전자정보기술, N=15개사)

**다음 단계**:
[ ] 면접서 "최근 실적 호조의 주요 동인이 뭔가요?" 질문
[ ] 연봉 협상 시 "성장률이 15%인데, 인상폭은?" 근거로 활용
```

**체크리스트**:
```
[ ] 3가지 이상 재무 지표 (수익, 이익률, 부채 등)
[ ] 모두 DART 출처 + 기준일
[ ] 산업 평균과 비교 (상대적 위치 파악)
[ ] "당신에게 미치는 영향" 섹션 있음
[ ] 2개 이상 action item 제시
[ ] 300 tokens 이내
```

---

### 3. Tech Stack (200 tokens)

**목표**: 면접 준비 + 기술 성장 기회 파악

```markdown
## Tech Stack & Technical Growth

**Primary Languages**:
- **Python** (5+ years, mature)
  - Implication: 깊이 있는 질문 예상 (ORM, async patterns, 성능 최적화)
  - Interview angle: 당신의 5년 경험을 강조

- **Kubernetes** (2 years, growing adoption)
  - Implication: 신기술, 배우는 기회
  - Interview angle: "배우고 싶다"는 의욕 표현 (당신이 학습 중이라면 더 좋음)

**Data Stack**:
- PostgreSQL (mature, 당신의 경험과 일치 ✨)
- Redis (caching, standard)

**Growth Opportunity**:
- GraphQL 도입 검토 중 (블로그, 2024-02) → 신기술 배울 기회

**당신의 준비**:
[ ] Python 심화 예상 질문 3개 준비 (ORM, async, 성능)
[ ] Kubernetes 기초 학습 (당신이 완전 미경험이면)
[ ] GitHub 최근 activity 확인 (기술 트렌드 파악)
```

**체크리스트**:
```
[ ] 3개 이상 핵심 기술 명시
[ ] 각 기술의 성숙도 표시 (mature/growing/new)
[ ] 당신의 경험과 매칭 ("일치", "인접", "신학")
[ ] 면접 각도 제시 (각 기술마다 1줄)
[ ] 최근 뉴스/기술 도입 포함
[ ] 학습 준비 체크리스트 제시
[ ] 200 tokens 이내
```

---

### 4. Recent News (200 tokens)

**목표**: 회사 트렌드 파악 + 면접 질문 소재

```markdown
## Recent News & Company Trajectory

**Last 3 Months**:
- **[2024-03] Japan Market Expansion Announced**
  Implication: 국제 화 전략 강화 → 글로벌 경험 있으면 강점
  Interview Q: "일본 진출 전략을 어떻게 보시나요?"
  Source: [사업 공시](link) | [기사](link)

- **[2024-02] Series C Funding $50M**
  Implication: 향후 12개월 공격적 채용 예상 → 프로모션 기회
  Interview Q: "Series C 후 우선순위가 뭔가요?"
  Source: [크런치베이스](link)

- **[2024-01] CTO 신규 영입**
  Implication: 기술 방향 전환 신호? or 강화?
  Research: 신규 CTO의 배경 확인 → 면접 토픽
  Source: [링크드인](link)

**패턴 분석**:
→ 성장 페이즈 (투자 + 국제화 + 경영진 영입)
→ 면접서 "빠른 변화에 적응 능력" 강조 필요
```

**체크리스트**:
```
[ ] 최근 3개월 뉴스만 포함 (6개월+ 오래된 건 제외)
[ ] 각 뉴스에 링크 포함
[ ] 각 뉴스의 "당신에게 의미" 해석
[ ] 면접에서 쓸 수 있는 질문 제시
[ ] 연결되는 패턴 1개 이상 (성장 페이즈, etc)
[ ] 200 tokens 이내
```

---

### 5. Culture Insights (150 tokens)

**목표**: 실무 환경 현실성 파악

```markdown
## Workplace Culture & Environment

**Work-Life Balance**:
- 재택 근무: 3일/주 (회사 공식)
- 근무 시간: 평균 45-50시간/주 (블라인드 평가 45건 기준)
- 야근 빈도: "가끔" 35% | "자주" 40% | "거의 없음" 25% → 건강하지 않은 신호
  Source: 블라인드 후기 (N=45명, 최근 3개월)

**팀 규모 & 성장**:
- 팀 1년 확장율: 25% (팀 확장 중 → 프로모션 기회)
- 이직 회원 비율: 15% (평균 3.5년 근무) → 장기 근무자 많음

**리더십 & 심리 안정성**:
- 팀장 평가: 4.1/5 (블라인드) → 관리자 만족도 높음
- "상급자와 대화 용이" 78% → 수평적 문화

**당신이 경험할 것**:
→ 자율성 높음 + 빠른 변화 + 야근 가능성 존재
→ 안정 중심이라면 위험, 성장 중심이라면 기회

**준비**:
[ ] 야근 가능성에 대한 생각 정리 (당신의 우선순위 확인)
[ ] 팀장 만나면: "팀 내 성장 경로가 어떻게 되나요?" 질문
```

**체크리스트**:
```
[ ] 3개 이상 문화 지표 (WLB, team size, leadership)
[ ] 모든 정성 평가: 샘플 수 표시 (N=45명)
[ ] 모든 링크: 출처 명확 (블라인드, Glassdoor, etc)
[ ] "당신이 경험할 것" 구체화
[ ] 당신의 선호와 매칭 (fit/risk 명시)
[ ] 면접 질문 1개 제시
[ ] 150 tokens 이내
```

---

### 6. Compensation (100 tokens)

**목표**: 연봉 협상 가능성 판단 + 책략

```markdown
## Compensation & Benefits

**Salary Range** (공시 기준, 2024년):
- Entry (신입, 0-2년): 3,200만원 ~ 3,800만원
- Junior (3-5년): 4,500만원 ~ 5,500만원
- Senior (5년+): 6,500만원 ~ 9,000만원

**Bonus & Benefits**:
- 연 보너스: 기본급의 3-4개월 (실적 기반)
- 복리후생: 연차, 휴직, 교육 지원 (기업 공시)

**연봉 협상 근거**:
- 당신이 Senior라면: "최근 15% 성장, 경쟁사 평균 X원인데 협상 여지?"
- 당신이 Junior라면: "기술 성장 기회 > 초기 연봉 (2년 후 이직 시 더 좋은 조건)"

**주의사항**: 공시 기준이므로 실제는 협상 여지 큼
```

**체크리스트**:
```
[ ] 직급별 연봉 범위 명시 (공시 기준 or 검증된 평가)
[ ] 보너스 구조 설명
[ ] 복리후생 나열
[ ] 당신의 협상 전략 1-2가지 제시
[ ] 100 tokens 이내
```

---

### 7. Growth Trajectory (200 tokens)

**목표**: 2-5년 커리어 성장 가능성

```markdown
## Career Growth & Learning Opportunities

**Team Expansion Phase**:
- 1년 팀 성장율: +25% (채용 공격적) → 프로모션 기회 높음
- 신규 리더십 역할 창출: 3-6개월마다 예상

**Technical Leadership Path**:
- Staff Engineer 역할 존재? Yes (GitHub 조직도 확인)
- 기술 심화 vs 관리 선택: 두 길 모두 가능한 문화

**12개월 후 당신의 위치**:
- 기술: Python/Kubernetes 깊이 + 신기술 경험 (GraphQL 검토 중)
- 영향력: 팀 1-2명 멘토링 또는 교차 팀 협업
- 보상: 연봉 10-15% 인상 가능성

**학습 기회**:
- 국제 시장 경험 (Japan expansion) → 글로벌 마인드셋
- 빠른 성장 환경 → 리더십 경험 가속화
- 모던 스택 → 시장 경쟁력 있는 기술 깊이

**위험 요소**:
- 빠른 변화 = 프로세스 부실 가능 → "기술부채 관리는 어떻게 하나요?" 질문 필요
```

**체크리스트**:
```
[ ] 1년/3년 성장 가능성 구체화
[ ] 기술 + 영향력 + 보상 3가지 각도
[ ] 12개월 후 현실적 위치 제시
[ ] 학습 기회 3개 이상
[ ] 위험 요소 명시 + 질문으로 검증 방법
[ ] 200 tokens 이내
```

---

### 8. Job Fit Scorecard (200 tokens)

**목표**: 한눈에 보는 5차원 점수 + 합산

```markdown
## Job Fit Scorecard

| Dimension | Weight | Score | Evidence |
|-----------|--------|-------|----------|
| **Technical Growth** | 20% | 16/20 | Modern stack (Python ✓, K8s learning) |
| **Career Leverage** | 20% | 18/20 | 25% team growth + promo opportunity |
| **Compensation** | 20% | 14/20 | Market-rate, slightly below tier-1 |
| **Culture Fit** | 20% | 17/20 | Autonomous but fast-paced (야근) |
| **Long-term Stability** | 20% | 17/20 | Strong revenue, market risk (Japan) |
| | | | |
| **TOTAL** | 100% | **82/100** | **Grade: A** |

**해석**:
- 82/100 = 좋은 기회 (strong yes)
- 90/100 = 매우 좋은 기회 (very strong yes)
- 70/100 = 가능성 있음 (maybe, depends on context)
- 60/100 이하 = 신중 (caution)

**당신의 의사결정 가이드**:
- 점수 목표: 75/100 이상이면 진행 가치 있음
- 이 회사: 82점 → 진행 권장
- 단, 야근 문제가 당신 우선순위면 재검토 필요
```

**체크리스트**:
```
[ ] 5개 차원 모두 명시 (합계 100%)
[ ] 각 차원의 근거 구체적 (한 줄 이상)
[ ] 총점 산출 (0-100)
[ ] 등급 부여 (A~F)
[ ] 점수의 의미 설명 (뭐가 좋고 뭐가 부족한가)
[ ] 당신의 우선순위 반영 (가중치 조정 가능성 언급)
[ ] 200 tokens 이내
```

---

### 9. Interview Prep Tips (150 tokens)

**목표**: 다음주 면접에 쓸 수 있는 실전 팁

```markdown
## Interview Preparation

**Expected Questions & Your Strategy**:

1. **"왜 우리 회사인가요?"** (문화/가치 맞춤형 답변)
   Your angle: "일본 진출 확장을 보며, 국제 시장 기회에 끌렸습니다.
   기술적으로는 Kubernetes 같은 모던 스택에서 깊이 있는 경험을 쌓고 싶습니다."

2. **"기술 스택 중 경험 없는 부분은?"** (학습 의욕 표현)
   Your angle: "Kubernetes는 학습 중입니다. 최근 [작은 프로젝트] 완료했고,
   당신들의 실제 사용 케이스를 배우고 싶습니다."

3. **"팀 내 역할은 뭘 기대하나요?"** (성장 기회 확인)
   Your angle: "팀이 25% 성장 중인데, 어떤 신규 역할이 생길까요?
   멘토링이나 인프라 개선 같은 책임이 있을까요?"

**Red Flags to Address**:
- 야근이 자주? → "작업 효율성 향상 방법이 뭔가요?" 질문으로 probe
- 기술부채? → "새 스택(GraphQL) 도입할 때 레거시 정리 전략은?" 질문

**Preparation Checklist**:
[ ] 일본 진출 뉘앙스 3개 준비 (당신의 글로벌 경험 연결)
[ ] Kubernetes 기초 학습 (YouTube 2시간)
[ ] 당신의 Python 프로젝트 1개 준비 (깊이 질문에 대비)
```

**체크리스트**:
```
[ ] 예상 질문 3-5개 (회사 특화)
[ ] 각 질문의 당신의 답변 방향 1줄
[ ] 레드플래그 2개 이상 언급
[ ] 준비 체크리스트 actionable (1주일 내 가능)
[ ] 150 tokens 이내
```

---

### 10. Risks & Red Flags (100 tokens)

**목표**: 현실적 경고 + 대응책

```markdown
## Risks & Red Flags

**Risk 1: 야근 문화 가능성** (40% 응답 "자주 야근")
Severity: Medium
Mitigation:
- 면접서: "평균 근무시간이 몇 시간인가요? 프로젝트별 차이는?"
- 입사 전: 팀 캐주얼 채팅 요청해서 문화 체감
- 의사결정: "성장 > 워라벨" 우선순위면 진행, 반대면 재고

**Risk 2: 기술부채 (GitHub issues 보면 레거시 코드 언급)**
Severity: Low (크리티컬하지 않음)
Mitigation:
- 면접서: "최근 기술부채 정리 작업이 있나요?"
- 학습 기회: 새 스택 도입하면 부채 정리하는 기회

**Risk 3: 국제 확장 (Japan) 성공 불확실성**
Severity: Low (단기영향 없음, 장기 회사 방향)
Mitigation:
- 2-3년 안에 성과 확인 후 다음 이직 판단
- 현재는 성장 기회로 활용

**종합 판정**: 리스크 있으나 대응 가능 → 진행 권장
```

**체크리스트**:
```
[ ] 3개 이상 리스크 명시
[ ] 각 리스크 심각도 표시 (High/Medium/Low)
[ ] 각 리스크의 구체적 대응책 (면접 질문, 학습 등)
[ ] "종합 판정" 명시 (진행/신중/회피)
[ ] 100 tokens 이내
```

---

### 11. Similar Companies (100 tokens)

**목표**: 대안 회사 제시 (이 회사 안 되면 어디?)

```markdown
## Alternative Companies (Backup Plan)

If HireKit doesn't work out, consider:

**Tier 1 (Similar size, culture)**:
- **Naver** — Larger, more stable, similar tech stack
  Pro: Stability, better compensation | Con: More bureaucratic
- **Kakao** — Similar growth stage, stronger finances
  Pro: Market leader | Con: More conservative culture

**Tier 2 (Smaller, more growth opportunity)**:
- **Toss** — Faster growth, modern tech, younger culture
  Pro: Growth opportunity | Con: Higher pressure
- **Carrot** — Smaller, lean team, direct impact
  Pro: Hands-on learning | Con: Less stability

**Tier 3 (Overseas)**:
- **Stripe** — Best compensation, global scale
  Pro: Top-tier career move | Con: Highly competitive

**Decision Framework**:
- Stability priority → Naver/Kakao
- Growth priority → Toss
- Technical depth → HireKit (current top choice)
```

**체크리스트**:
```
[ ] 3-5개 대안 회사 제시
[ ] 각 회사별 장단점 1줄
[ ] 우선순위별 분류 (Tier 1/2/3)
[ ] 당신의 가치관별 매칭 (안정성 vs 성장)
[ ] 100 tokens 이내
```

---

### 12. Action Items (50 tokens)

**목표**: 다음 단계 체크리스트

```markdown
## Action Items

**This Week**:
- [ ] GitHub 최근 activity 확인 (기술 트렌드 파악)
- [ ] Japan expansion 관련 기사 읽기 (면접 토픽 준비)

**Before Phone Screen** (1주일 전):
- [ ] Kubernetes 기초 학습 (YouTube 영상 1-2개, 2시간)
- [ ] 당신의 Python 프로젝트 정리 (깊이 질문 대비)

**Before On-site** (3일 전):
- [ ] 기업 공시 한 번 더 읽기 (최신 수치 확인)
- [ ] 질문 리스트 정리 (3개 이상)

**If Offer Comes**:
- [ ] 야근 문화, 프로모션 경로 재확인
- [ ] 연봉 협상: "15% 성장 + 프로모션 기회" 근거로 활용
```

**체크리스트**:
```
[ ] 이번주 행동: 2-3가지 (모두 실행 가능)
[ ] 면접 1주일 전: 2-3가지 (구체적, 시간 표시)
[ ] 면접 3일 전: 1-2가지 (마지막 준비)
[ ] Offer 후: 1-2가지 (협상 전략)
[ ] 모든 항목: checkbox 포함 (트래킹용)
[ ] 50 tokens 이내
```

---

## 리포트 최종 품질 체크리스트

```
ACCURACY (정확도)
[ ] 모든 수치: 소스 + 기준일 명시
[ ] 모든 추정: "(추정)", "(가능성)" 표시
[ ] 오래된 정보: 연도 표시
[ ] 부재 정보: 명시 + 대안 제시

JOB SEEKER LENS (직업자 관점)
[ ] 모든 재무: 연봉 영향으로 재해석
[ ] 모든 기술: 면접 각도 포함
[ ] 모든 문화: "당신이 경험할 것" 구체화
[ ] 모든 리스크: 당신의 우선순위 반영

SCANNABILITY (스캔 가능성)
[ ] 섹션 제목: 첫 단어가 수치 또는 질문
[ ] 문단: max 3줄 (긴 문장은 bullet)
[ ] 강조: key metric은 bold
[ ] 구조: 각 섹션 <300 tokens, 전체 <8,000

ACTIONABILITY (행동 가능성)
[ ] 모든 리스크: 대응 전략 제시
[ ] 모든 약점: 준비 항목으로 변환
[ ] 모든 조언: 1주일 내 실행 가능
[ ] Action Items: 시간별 우선순위

TONE (톤 & 열정)
[ ] 희망적이되 신뢰성 있음
[ ] 당신(지원자) 중심
[ ] 격식체 일관 (한국어 존댓말)
[ ] 오타 제로

EVIDENCE (근거)
[ ] 모든 주장: 2개 이상 소스
[ ] 모든 정성평가: 샘플 수
[ ] 모든 뉴스: 링크 + 발행일
[ ] 출처 섹션: 정보 일목요연

COMPLETENESS (완성도)
[ ] 12섹션 모두 채움
[ ] 데이터 소스: 최소 5개 (DART, News, GitHub, Reviews, etc)
[ ] 사용자 선택지: "yes/no/maybe" 가능
[ ] 다음 단계: 명확
```

---

## 예시: Before & After

### Before (기존 리포트)

```
## Financial Information
Kakao had revenue of 12.3 trillion won last year.
The company is growing and the profit margin is good.
They have a team of 2,500 people and hire many new employees.
The tech stack includes Python and Kubernetes.
There are some risks like market competition.
```

**점수**: 30/100 (추상적, 직업자 관점 부재)

### After (개선된 리포트)

```
## Financial Health

**연매출**: 12.3조 원 (작년 대비 **+15.2%**)
**영업이익률**: 22.4% (산업 평균 18% 대비 1.25배)
**부채비율**: 45% (안전 기준: <60%) ✅

**당신에게 미치는 영향**:
연매출 12.3조 × 22% 이익률 = 회사가 충분히 수익성 있음
→ 연봉 인상 가능성: **높음** (매년 15% 성장 중)

**근거**: DART 2024년 반기보고서 (기준일: 2024-06-30)

**다음 단계**:
[ ] 면접서 "최근 15% 성장의 주요 드라이버가 뭔가요?" 질문
[ ] 연봉 협상: "성장률 15%인데, 신입 기준 인상폭은?" 근거로 활용
```

**점수**: 85/100 (구체적, 직업자 중심, 행동 지향)

---

## 자동화 & 검증

### 코드 예시

```python
class ReportQualityValidator:
    def validate_accuracy_layer(self, report: str) -> List[str]:
        """Check if all numbers have sources"""
        issues = []
        numbers = self.extract_numbers(report)
        for number in numbers:
            if not self.has_source(report, number):
                issues.append(f"Missing source: {number}")
        return issues

    def validate_scannability_layer(self, report: str) -> List[str]:
        """Check if sections are scannable"""
        issues = []
        sections = self.extract_sections(report)
        for section in sections:
            tokens = self.count_tokens(section)
            if tokens > 300:
                issues.append(f"Section {section.title} exceeds 300 tokens: {tokens}")
        return issues

    def validate_actionability_layer(self, report: str) -> List[str]:
        """Check if report has action items"""
        issues = []
        action_items = self.extract_action_items(report)
        if len(action_items) < 5:
            issues.append(f"Too few action items: {len(action_items)} (need 5+)")
        return issues

    def run_all_checks(self, report: str) -> Dict[str, List[str]]:
        """Run all 6 layers + 12 sections"""
        return {
            "accuracy": self.validate_accuracy_layer(report),
            "job_seeker_lens": self.validate_job_seeker_lens(report),
            # ... etc
        }
```

---

## 결론

좋은 리포트 = 사용자가 **의사결정을 내릴 수 있는** 리포트.

6가지 정보층 + 12섹션 체크리스트를 따르면, HireKit의 리포트는 단순 정보가 아닌 **실행 가능한 직업 가이드**가 됩니다.
