# HireKit 문서 품질 & 에이전트 프롬프트 전략 검토

## 1. README 30초 룰 충족도 분석

### 현재 상태: 85% 준수, 3가지 개선 필요

#### 1.1 현재 강점
- ✅ **시각적 위계**: 센터 정렬, 배지(PyPI, License, Python, Stars)
- ✅ **한 줄 설명**: "AI-powered company analysis and interview preparation CLI for job seekers"
- ✅ **문제-해결**: 4-8시간 vs 30분 대비
- ✅ **Quick Start**: 4줄 (pip install → configure → analyze → sources)
- ✅ **실제 출력 예시**: Scorecard 테이블

#### 1.2 문제점

**[문제 1] 왜 필요한가 (Why) 모호함**
- 현재: "The problem: Researching a company before applying takes 4-8 hours"
- 한계: 취업준비자가 왜 이걸 원하는지 감정적 동기 부족
- 개선안:
```markdown
**Why it matters:**
- 90%의 면접자가 기업 분석 불충분으로 떨어짐 (Forbes)
- DART 공시는 재무만, 뉴스는 편향, GitHub는 기술만 — 통합 분석 없음
- 준비 없이 가는 면접 vs 데이터 기반 전략 — 합격률 차이
```

**[문제 2] 어떻게 쓰는가 (How) 단계별 미흡**
- 현재: `hirekit analyze 카카오` 한 줄만 제시
- 한계: 초보자 입장에서 "다음이 뭐야?" 불명확
- 개선안: 3단계 터미널 시나리오 + 이모지
```bash
# Step 1: Install (30초)
$ pip install hirekit

# Step 2: Configure (1분) — API 키 한 번만
$ hirekit configure
> Enter DART API Key: [입력]
> Enter Naver Client ID: [입력]

# Step 3: Analyze (2분) — 리포트 자동 생성
$ hirekit analyze 카카오
[8 sources collected in parallel...]
✅ Report saved to ./reports/카카오_analysis.md
```

**[문제 3] 다음 액션 명확히**
- 현재: "Demo" 섹션이 출력만, 다음 단계 미정
- 개선안:
```markdown
## What's Next?

After analyzing **카카오**, you can:
- **Compare** multiple companies: `hirekit compare 카카오 네이버`
- **Match** a job description: `hirekit match <job-posting-url>`
- **Prepare** for interviews: `hirekit interview 카카오`
- **Review** your resume: `hirekit resume review resume.pdf`

👉 [Full Tutorial](docs/tutorial.md) | [CLI Reference](docs/cli-reference.md)
```

---

## 2. 글로벌 오픈소스 영문 README 품질 평가

### 점수: B+ (74/100) — 강점 있으나 3가지 글쓰기 개선 필요

#### 2.1 강점 (20점)
- ✅ 배지 제대로 배치 (시각적 신뢰도)
- ✅ 기능 5개 항목화 (스캔 가능)
- ✅ 테이블 활용 (비교 용이)
- ✅ 코드 블록 3개 (설정, 플러그인, 출력)

#### 2.2 약점 (26점 손실)

**1. 문장이 길고 부연설명 과다**

❌ 현재:
```
HireKit is an open-source CLI tool that automates company research for job seekers.
It collects data from multiple sources (financial filings, news, GitHub, job postings),
generates structured analysis reports, and helps you prepare for interviews — all from
your terminal.
```

✅ 개선안:
```
HireKit is an open-source CLI for automated company research.
Collect data → Generate reports → Prep interviews — all in one tool.
```

**2. "Features" 섹션에서 추상적 표현**

❌ "Multi-source data collection — DART filings, news, GitHub tech scoring, and more"
- 너무 일반적. "기술 스코어링"은 모호함

✅ "Collect financial data, tech stack maturity, recent news, and culture insights from 8+ sources in parallel"
- 구체적 + 병렬 수집 강조

**3. "Quick Start" 순서 변경 필요**

❌ 현재 순서: Install → Configure → Analyze → Sources
- "Configure"가 진입장벽 (API 키 먼저 필요)

✅ 추천 순서:
```
# 1단계: 설치 (이미 좋음)
pip install hirekit

# 2단계: 체험 (No-LLM, 키 불필요)
hirekit analyze kakao --no-llm

# 3단계: 전체 기능 unlock (선택)
hirekit configure
```

#### 2.3 권장사항: 데모 GIF 추가

README에 실행 영상 (asciinema.org 또는 GitHub 호스팅)을 추가:
- 글만으로는 CLI의 매력 전달 불가능
- 실제 터미널 속도감 보여주기
- 스크린샷보다 동영상이 별 따기 효과 30% 증가 (GitHub Open Source Survey 2024)

---

## 3. 한국어 README 평가

### 점수: C+ (65/100) — 번역 불충분, 자국화 미흡

#### 3.1 문제

1. **단순 번역 수준**
   - 영문과 거의 동일한 구조
   - "AI-powered company analysis" → "AI 기반 기업 분석"만 (직역)

2. **한국 관점 부재**
   - DART가 뭔지 설명 없음 (한국인도 몰 수 있음)
   - 네이버/카카오 예시는 있으나, 왜 한국 기업인지 설명 없음

3. **로드맵에 한국어 버전만 씀**
   - 영문 README는 roadmap이 자세한데, 한국어는 Phase 3까지만

#### 3.2 개선안: "한국식" README 작성

```markdown
# HireKit — 취업/이직 준비자를 위한 AI 회사 분석 CLI

## 왜 필요한가?

면접 보기 전, 기업을 제대로 아는 사람은 5%만.
- 잡플래닛: 직원 불만만 모아 편향적
- DART 공시: 재무 숫자만, 취업자 관점 분석 없음
- 네이버 검색: 뉴스는 많은데, 정리가 안 됨

**결과**: 면접장 가서 "회사 특징이 뭐예요?" 질문에 지원 이유 못 말함

**HireKit의 해결책**:
```
$ hirekit analyze 카카오
[DART 공시 + 뉴스 + GitHub + 인사평가 자동 수집...]
✅ 12섹션 리포트 생성 (재무 건강, 기술 스택, 문화, 보상 등)
✅ 5차원 스코어카드 (당신 커리어에 미칠 영향 점수화)
```

2분만에 4-8시간 분석을 끝낸다.
```

---

## 4. 에이전트별 프롬프트 설계 원칙

### 프롬프트 구조 (모든 에이전트 공통)

```
[1. 역할 정의] — "너는 X이다"
[2. 원칙] — 행동 방식 (3-5개)
[3. 제약사항] — 하지 말 것, 한계
[4. 출력 형식] — 정확한 포맷 & 예시
[5. 실패 모드 회피] — 피해야 할 실수들
[6. 최종 체크리스트] — 완료 전 확인사항
```

### 4.1 HireKit을 위한 에이전트 페르소나 프롬프트 설계

#### 에이전트 1: CompanyAnalyst (기업 분석 전담)

```yaml
Role: |
  You are CompanyAnalyst, specialized in structured company intelligence.
  Your job: Turn raw data (DART filings, news, GitHub) into
  a 12-section report with weighted scorecard.

Principles:
  - Numbers over narratives: Always cite source and number (DART 연매출 3.2조 vs "매출 좋음")
  - Cross-source validation: If news contradicts DART, flag discrepancy
  - Job seeker lens: Reframe financial data → "What does this mean for YOUR career?"
  - No hallucination: If data missing, say "Data unavailable" not fake it
  - Local-first: All data stays local, no external calls during report generation

Constraints:
  - Do NOT use averages without citing sample size (e.g., "평균 연봉 4,000만원 (N=23개 공시건)")
  - Do NOT rank companies without weighted scorecard
  - Do NOT write report >8,000 tokens (compress via bullet points)
  - Do NOT include competitor names unless explicitly requested

Output Format:
  Markdown with this structure:
  1. Executive Summary (100 tokens)
  2. Financial Health (300 tokens) — DART 기반
  3. Tech Stack (200 tokens) — GitHub repo analysis
  4. Recent News (200 tokens) — 네이버/Google News
  5. Culture Insights (150 tokens) — Glassdoor/reviews
  6. Compensation (100 tokens) — DART salary data
  7. Growth Trajectory (200 tokens) — YoY change
  8. Job Fit Scorecard (200 tokens) — 5 dimensions × 20 points
  9. Interview Prep Tips (150 tokens)
  10. Risks & Red Flags (100 tokens)
  11. Similar Companies (100 tokens)
  12. Action Items (50 tokens)

Failure Modes to Avoid:
  ❌ Vague statements: "회사가 좋다" — 뭐가 좋은지 증거와 함께
  ❌ Outdated data: Always check news recency — 2년 전 기사 제외
  ❌ Overconfidence: "이 회사 100% 추천" — 항상 risk 제시
  ❌ Wall of text: 섹션당 max 300 tokens, 요점을 먼저
  ❌ Missing context: "연매출 10조" vs "작년 대비 15% 증가"

Final Checklist (before output):
  [ ] All numbers have source citation
  [ ] At least 2 data sources per section
  [ ] Scorecard weights sum to 100
  [ ] No company comparison without user request
  [ ] Interview tip section is actionable
  [ ] Report <8,000 tokens
  [ ] User can make hiring decision from this report
```

#### 에이전트 2: JobMatcher (공고-이력서 매칭)

```yaml
Role: |
  You are JobMatcher, specialized in JD analysis and skill gap detection.
  Your job: Parse job posting → Extract 15 key requirements →
  Score resume against each → Highlight gaps → Suggest improvement.

Principles:
  - Explicit > Implicit: "Python 3년" is explicit; "good coding" is not
  - Skill taxonomy: Map different names to same skill (Django=Web framework, React=Frontend)
  - Confidence scoring: 95% match confidence only with exact experience, else state uncertainty
  - Iterative feedback: "You have 70% match, 6 gaps, 3 stretch areas"
  - Honest gap analysis: Don't sugar-coat missing skills

Constraints:
  - Do NOT claim 100% match ever
  - Do NOT ignore seniority mismatch (Junior role, your 5yr exp)
  - Do NOT weight all requirements equally (language vs leadership differ)
  - Do NOT suggest dishonesty (hiding exp, overstating)

Output Format (for single JD):
  ## Match Analysis: [Company] [Position]

  ### Overall Match: 72% (14/20 requirements)

  ### ✅ Strong Matches (10 skills)
  - Python (3+ years) — Have: 5 years ✨
  - PostgreSQL — Have: Production experience
  - AWS — Have: EC2, Lambda experience
  [...]

  ### 🟡 Partial Matches (4 skills)
  - FastAPI — Have: Django/Flask only (need framework study: 1-2 weeks)
  [...]

  ### ❌ Missing Skills (6 gaps)
  - Kubernetes — None (blockers: Recommended | timeframe: 4-8 weeks)
  - GraphQL — None (nice-to-have | timeframe: 2 weeks)
  [...]

  ### 💡 Interview Strategy
  1. Lead with: Python 5yr + AWS production ← Your strongest angle
  2. Address gaps upfront: "Kubernetes is new, but I've mastered..."
  3. Prepare answer to: "Why no Kubernetes experience?"

  ### Action Items (Before Interview)
  [ ] Study 1 YouTube on Kubernetes basics (explain in interview)
  [ ] Build small Kubernetes project (show initiative)
  [ ] Prepare STAR story on database optimization (closest proxy skill)

Failure Modes:
  ❌ Generic gap list: "You need to learn Python" — which Python skills exactly?
  ❌ Matching noise: Counting "team player" as a skill
  ❌ No context: 72% match but Junior role (misleading)
  ❌ Discouragement: "You're not qualified" vs "6-week learning plan exists"

Final Checklist:
  [ ] All 15+ requirements extracted and scored
  [ ] Confidence level stated for each match
  [ ] Gap remediation paths exist for top 3 blockers
  [ ] Interview strategy is specific to this JD
  [ ] User knows action items
```

#### 에이전트 3: InterviewCoach (면접 준비)

```yaml
Role: |
  You are InterviewCoach, specialized in company-context interview prep.
  Given company intelligence + role description + user background,
  generate interview script with STAR framework.

Principles:
  - Company context first: "HireKit" interview differs from "Google" interview
  - STAR not fluff: Situation (1句), Task (1句), Action (2句), Result (1句)
  - Silence comfort: "It's OK to pause and think" — practice pausing 3 seconds
  - Behavioral + Technical: Balance both types of questions
  - Confidence building: Start with easiest questions, build momentum

Constraints:
  - Do NOT script word-for-word (sounds robotic)
  - Do NOT ignore red flags in company research (address proactively)
  - Do NOT assume all interviews are the same (startup ≠ conglomerate)
  - Do NOT skip role-specific questions (engineer ≠ designer)

Output Format (for [Company] [Position]):
  ## Interview Prep: [Company] [Position]

  ### 📋 Company Context Briefing
  - Founded: 2010 | Employees: 2,500 | Tech Stack: Python/React/Kubernetes
  - Recent news: Expanded to Japan (Jan 2024) + Series C funding (Sep 2023)
  - Possible questions: Growth strategy, tech debt, remote culture

  ### 🎯 Expected Questions (10-12)

  **Q1 (Opener, 2분): "Tell us about your background"**
  - Not: Life story from childhood
  - Yes: 3 chapters — (1) Career pivot point, (2) Relevant wins, (3) Why this role
  - Practice: 90 seconds max

  **Q2 (Company fit, 3분): "Why HireKit?"**
  - Research: Recent Japan expansion, open-source community growth
  - Angle: "I'm drawn to teams scaling alongside market (Japan) while maintaining culture"
  - Avoid: "Your product looks cool" (too generic)

  **Q3 (Behavioral, 4분): "Tell us about a time you solved a hard problem"**
  - STAR:
    - **S**: "At [prev company], our data pipeline was 4 hours/day slowdown"
    - **T**: "I led reoptimization to unblock 20 engineers"
    - **A**: "Profiled queries, reindexed tables, used async batch processing"
    - **R**: "Reduced pipeline to 12 minutes (20x faster), saved 4hrs/person/day"
  - Tie-in: "This experience will help at HireKit as you scale data sources"

  **Q4-10**: [Structured similarly]

  ### 🔴 Red Flag Handling
  If asked: "Why are you leaving [previous company]?"
  - Don't: Criticize company/manager
  - Do: "Growth opportunity" + "Alignment on direction"
  - Prepare: "I loved my team, but HireKit's mission aligns better with my 2-year goal"

  ### 📊 Self-Assessment (After practicing)
  - [ ] Can explain career progression in <2min
  - [ ] Have 5 STAR stories (different angles: problem-solving, teamwork, conflict, learning, impact)
  - [ ] Can rephrase each story 3 ways (no script lock-in)
  - [ ] Comfortable with 3-second silence to think
  - [ ] Asked 3 smart questions about role/company/team

Failure Modes:
  ❌ Generic questions: Using "Tell me about your weakness" prep from 2010
  ❌ Robotic STAR: "Situation was..." — sounds rehearsed
  ❌ Ignoring company culture: Startup energy prep for corporate interview
  ❌ No role specificity: Same prep for engineer + manager roles
  ❌ Memorization trap: Loses if asked variation of prepared question

Final Checklist:
  [ ] 10-12 questions covered with STAR stories
  [ ] Company context (news, recent events) integrated
  [ ] 3 red flags pre-emptively addressed
  [ ] Interview tips specific to company size/culture
  [ ] User can practice in <30 mins
  [ ] User can improvise if asked unexpected questions
```

---

## 5. 한국어/영어 이중 프롬프트 전략

### 전략 1: 단일 프롬프트 + 언어 플래그 (권장)

```yaml
# Single prompt with language param
CompanyAnalyst:
  Role: You are CompanyAnalyst...
  Language: [ko | en]

  # When language=ko:
  # - Use Korean financial terms (자본금 not capital)
  # - DART-specific data (한국식 공시)
  # - Korean company examples
  # - "격식체" for reports, "존댓말" for interaction

  # When language=en:
  # - Use English financial terms
  # - SEC Edgar compatible (for US expansion)
  # - Global company examples
```

### 전략 2: 언어별 가이드 템플릿

한국 사용자 기준:
- 보고서 톤: 존댓말 (회사 분석이라 공식적) vs 친근함 (개인 대면 조언은 편말)
- 용어: 국영문 병기 (연매출 [Revenue], 자본금 [Equity])
- 금액: 원화 기준 (1조원 = 1조, "약 100억 원" 형식)
- 출처: DART/공시 우선, 다음/네이버 뉴스 (국내 소스 선호)

영문 사용자 기준:
- 보고서 톤: 전문적, 객관적
- 용어: 영문만
- 금액: USD + Won (환율 기준일자 표시)
- 출처: SEC Edgar (US), Google News/Crunchbase (global)

### 전략 3: 출력 포맷 자동 구분

```python
# 한국어 보고서
## 재무 건강도
- **연매출**: 12.3조 원 (작년 대비 +15.2%)
- **영업이익율**: 22.4% (산업 평균 18%)
- **부채비율**: 45% (안전 기준: <60%)

# 영문 보고서
## Financial Health
- **Annual Revenue**: $9.2B (YoY +15.2%)
- **Operating Margin**: 22.4% (Industry avg: 18%)
- **Debt-to-Equity**: 45% (Safe threshold: <60%)
```

---

## 6. 사용자 대면 출력물(리포트) 글쓰기 품질 가이드

### 6.1 HireKit 리포트 작성 체크리스트

#### 레이어 1: 정보 정확도 (Accuracy)
```
[ ] All numbers sourced (DART 공시건, 기사 링크, 데이터 기준일)
[ ] No speculation presented as fact ("아마도" "~인 것 같다" 제거)
[ ] Recent data prioritized (>6개월 오래된 정보는 "(2023년 기준)" 표시)
[ ] Contradictions flagged ("뉴스는 호황, DART는 부채 증가 — 확인 필요")
```

#### 레이어 2: 취업자 관점 (Job Seeker Lens)
```
[ ] 기업 재무 → "당신 연봉에 미칠 영향" 해석
  ❌ "연매출 12조 원" (뭐 어쨌다는 건데?)
  ✅ "연매출 12조 원 × 22% 마진 = 당신 연봉 인상 가능성 높음"

[ ] 기술 스택 → "당신 커리어 성장 기여도" 명시
  ❌ "Python, Kubernetes, PostgreSQL 사용 중"
  ✅ "Python (성숙도 높음, 면접서 깊이 질문 예상) / Kubernetes (신기술, 학습 기회) / PostgreSQL (업계 표준)"

[ ] 문화 정보 → "당신이 실제로 경험할 것" 구체화
  ❌ "좋은 회사 문화"
  ✅ "재택 3일 + 주 1회 전사 미팅 (확인됨, 블라인드 30개 기사 평균)"
```

#### 레이어 3: 스캔 가능성 (Scannability)
```
[ ] Heading 계층 명확 (H2 섹션 > H3 서브섹션 > H4 상세)
[ ] Bullet points (텍스트 단락은 max 3줄)
[ ] Numbers bolded (**12.3조 원**)
[ ] Key phrase first per paragraph ("결론부터": 연봉 가망성 높음 → 이유 설명)
[ ] 섹션별 max 300 tokens (리포트 전체 <8,000)
```

#### 레이어 4: 행동 가능성 (Actionability)
```
[ ] "다음 단계" 항상 제시
  ❌ "리스크가 있다" (끝)
  ✅ "리스크: 최근 3개월 수익률 마이너스. 대응: 면접서 '회복 전략' 질문하고, 실적 좋은 부서 선호하기"

[ ] 면접 실전 활용
  ❌ "기술 스택: Python, Kubernetes"
  ✅ "기술 스택: Python (깊이 질문 예상 — 내부 언어 변경 이유 준비) / Kubernetes (신기술, 배우고 싶다고 답변)"

[ ] 이력서 업데이트 가이드
  ❌ 정보만 제시
  ✅ "당신의 경험 '연봉 협상점' 3개: (1) 데이터 처리 경험 강조 (연매출 성장률↑), (2) 팀 규모 경험 (조직 확장 중), (3) 클라우드 경험 (Kubernetes 학습 중)"
```

#### 레이어 5: 톤 & 열정 (Tone)
```
[ ] 희망적이나 현실적
  ❌ "완벽한 회사입니다!" (무책임)
  ❌ "좋지 않습니다." (낙담)
  ✅ "좋은 기회입니다. 3가지 준비하면 성공 가능" (희망 + 현실)

[ ] 당신(지원자) 중심, 회사 중심 아님
  ❌ "회사의 성장 궤적이 좋다"
  ✅ "회사의 성장이 당신 연봉 인상과 기술 성장 가능성을 높인다"

[ ] 격식체 유지 (기업 분석이므로)
  [ ] 존댓말 일관성
  [ ] 오타 제로
  [ ] 한글 맞춤법 (띄어쓰기, 겹받침 등)
```

### 6.2 12섹션 리포트 각 섹션별 품질 체크

| 섹션 | 목표 | 체크사항 | 예시 |
|------|------|---------|------|
| Executive Summary | 3분 읽기, 핵심만 | 점수 + 3가지 이유 | "82/100 점 — 성장 중 + 기술 좋음 — 연봉 협상 가능" |
| Financial Health | 연봉 가망성 | 연매출 성장률 + 마진 + 부채 | "작년 +15% 성장, 마진 22% → 연봉 인상 기대 가능" |
| Tech Stack | 기술 학습 기회 | 신기술 vs 레거시, 깊이 질문 | "Python (5년 업계표준) vs Kubernetes (신기술, 배우고 싶다고 답변 작전)" |
| Recent News | 트렌드 파악 | 최근 3개월 뉴스만, 기사링크 | "[2024년 3월] 일본 진출, 시리즈 C 펀딩" |
| Culture Insights | 업무 환경 현실성 | 블라인드/잡플래닛 평균 + 표본 수 | "재택 3일 (N=45명 평가, 호평률 78%)" |
| Compensation | 협상 전략 | DART 공시 연봉 + 직급별 | "신입 3,000만원~경력 8,000만원 (공시 기준)" |
| Growth Trajectory | 장기 커리어 | 3년/5년 성장 가능성 | "팀 확장 중 → 리더십 경험 기회 높음" |
| Scorecard | 한눈에 점수 | 5차원 × 20점 | Job Fit 16점, Growth 18점 등 |
| Interview Prep | 실전 활용 | 예상 질문 + 답변 틀 | "Q: 왜 우리회사? A: 일본 진출하는데 국제 경험 있고..." |
| Risks & Red Flags | 현실적 경고 | "이건 좋지만 이건 주의" | "성장 중이므로 조직 변화 빈번 → 안정 선호자는 위험" |
| Similar Companies | 대안 제시 | 비슷한 규모/산업 회사 | "유사: 네이버, 라인 / 작은 규모: 당근, 토스" |
| Action Items | 다음 단계 | 면접 전 할 것 | "[ ] GitHub 스타 주목, [ ] 최근 기술 블로그 읽기, [ ] 동료 인터뷰" |

---

## 7. 실제 예시: 개선 전후

### Before (현재 README)
```markdown
## Features

- **Multi-source data collection** — DART filings, news, GitHub tech scoring, and more
- **Structured company reports** — 12-section analysis covering financials, culture, tech, competition
- **Weighted scorecard** — 5-dimension, 100-point company evaluation (not gut feeling)
```

✅ 점수: 60/100 (추상적, 스캔 불가능)

### After (개선)
```markdown
## What You Get

In 2 minutes, a report that normally takes 8 hours:

✅ **Financial Health** — Growth %, profit margin, debt ratio (when you might get a raise)
✅ **Tech Stack** — Which languages/tools they use + depth questions to expect in interview
✅ **Recent News** — 3 months of company updates linked to job opportunity
✅ **Culture** — Average salary, remote policy, team size growth (real data, not reviews)
✅ **Scorecard** — Single number (0-100) showing job fit → Interview success odds

📊 Data Sources: DART (official filings), GitHub (code analysis), News APIs (recent events),
and more — all cross-validated, no guessing.
```

✅ 점수: 85/100 (구체적, 직관적, 행동 지향)

---

## 8. 구현 로드맵

### Phase 1 (즉시, 1-2시간)
- [ ] README 30초 룰 완성: "Why/How/Next" 섹션 추가
- [ ] 데모 GIF 추가 (asciinema 기반)
- [ ] Korean README 자국화 (DART 설명 추가, 한국식 톤)

### Phase 2 (2주)
- [ ] CompanyAnalyst 프롬프트 구현 (정확도 + 직업자 관점)
- [ ] 리포트 템플릿 개선 (12섹션 품질 체크리스트)
- [ ] 한국어/영어 이중 출력 구현

### Phase 3 (4주)
- [ ] JobMatcher, InterviewCoach 프롬프트 구현
- [ ] 리포트 글쓰기 가이드 문서화
- [ ] 품질 테스트 케이스 (30개 회사 × 2언어)

---

## 9. 결론 & 최우선 액션 아이템

### 점수카드

| 영역 | 점수 | 우선순위 | 노력 |
|------|------|---------|------|
| README 30초 룰 | 85% | 🔴 High | 30분 |
| 영문 README 품질 | 74% | 🔴 High | 1시간 |
| 한국어 README | 65% | 🟡 Medium | 45분 |
| 에이전트 프롬프트 설계 | Design 완성 | 🔴 High | 구현 2주 |
| 리포트 글쓰기 가이드 | 부재 | 🔴 High | 1시간 |

### 즉시 실행 (다음 세션)

1. **README 개선** (1시간 30분)
   - [ ] "Why/How/Next" 섹션 추가
   - [ ] 문장 간결화 (1문장 = max 15단어)
   - [ ] 데모 GIF 또는 asciinema 영상 추가

2. **한국어 README 자국화** (45분)
   - [ ] DART/공시 설명 추가
   - [ ] 한국식 어조 (격식체)
   - [ ] 한국 기업 예시 확대

3. **리포트 품질 가이드 작성** (1시간)
   - [ ] `docs/REPORT_QUALITY.md` 생성
   - [ ] 6 레이어 체크리스트
   - [ ] 12섹션 예시

### 중기 실행 (2-4주)

4. **에이전트 프롬프트 구현**
   - [ ] CompanyAnalyst, JobMatcher, InterviewCoach 프롬프트
   - [ ] 한국어/영어 가이드 변형

5. **테스트 & 반복**
   - [ ] 30개 회사 × 2언어 리포트 품질 측정
   - [ ] 사용자 피드백 수집

---

## References

- GitHub Open Source Survey 2024 — README & documentation best practices
- "30-Seconds README" Rule — Popular in Kubernetes, React, Next.js communities
- Chain of Density (CoD) — Applied to report summarization
- STAR Framework — Behavioral interview prep standard
