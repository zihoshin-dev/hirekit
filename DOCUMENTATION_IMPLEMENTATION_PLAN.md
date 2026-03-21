# HireKit 문서 개선 & 에이전트 프롬프트 구현 계획

## 📋 검토 결과 요약

### 종합 점수

| 영역 | 현재 | 목표 | 개선폭 |
|------|------|------|--------|
| **README 품질** | 74.7/100 | 90.7/100 | +16점 |
| **에이전트 프롬프트** | 설계 완료 | 실행 준비 | Ready |
| **리포트 글쓰기** | 무지침 | 6층 체계 | New |
| **한국어 자국화** | 65/100 | 85/100 | +20점 |

---

## 🚀 즉시 실행 계획 (다음 2주)

### Week 1: 문서 개선 (5시간)

#### Task 1.1: README 개선 (1.5시간)
**파일**: `/Users/ziho/Desktop/ziho_dev/hirekit/README.md`

적용할 변경:
1. "Why/How/Next" 섹션 추가 (현재 README_IMPROVED.md 참고)
   - Why: 감정적 공감 + 실제 문제점 (90% rejection rate 등)
   - How: 단계별 사용법 (Install → Configure → Analyze)
   - Next: 다음 명령어들 (compare, match, interview, resume)

2. Features 섹션 재작성
   - 추상 용어 제거 (multi-source → 8-source parallel)
   - 구체적 숫자 추가 (2 minutes, 5 dimensions, 100 points)
   - 당신 관점 강조 (salary negotiation, career growth)

3. Demo 섹션 개선
   - 현재: 텍스트 표 스크린샷만
   - 개선: asciinema 또는 GIF 영상 추가 (선택사항이지만 권장)

**검증**: README 읽고 2분 내에 이해 가능한가? (30초 룰)

#### Task 1.2: 한국어 README 자국화 (1.5시간)
**파일**: `/Users/ziho/Desktop/ziho_dev/hirekit/README.ko.md`

적용할 변경:
1. 전체 구조 재설계 (현재 README_IMPROVED.md의 한국어 섹션 참고)
   - "왜 필요한가" 섹션 확대 (실제 면접 상황, 블라인드/잡플래닛 언급)
   - "해결책" 섹션 명확화 (3분만에 뭘 얻는가 테이블)
   - "사용 시나리오" 추가 (Before/After 비교)

2. DART 설명 추가
   - "한국 기업 재무 공시" 한 줄 설명
   - DART API 키 어디서 얻는지 링크

3. 한국식 톤 일관화
   - 존댓말 확인
   - "당신", "지원자" 중심으로 재작성
   - 한국 취업 시장 언어 사용 (잡플래닛, 블라인드, 공고 링크)

**검증**: 한국 취업자가 "오, 이거 나한테 맞다" 느끼는가?

#### Task 1.3: 리포트 품질 가이드 문서 확인 (1시간)
**파일**: `/Users/ziho/Desktop/ziho_dev/hirekit/docs/REPORT_QUALITY_GUIDE.md` (이미 생성됨)

확인 사항:
- [ ] 6가지 정보층 설명 완전한가?
- [ ] 12섹션별 체크리스트 명확한가?
- [ ] Before/After 예시가 설득력 있는가?

추가 작업:
- 리포트 생성 코드에 자동 검증 로직 추가 (선택)
- 팀원 리뷰 1회

#### Task 1.4: 에이전트 프롬프트 가이드 문서 확인 (1시간)
**파일**: `/Users/ziho/Desktop/ziho_dev/hirekit/docs/AGENT_PROMPTS.md` (이미 생성됨)

확인 사항:
- [ ] 3개 에이전트 (CompanyAnalyst, JobMatcher, InterviewCoach) 프롬프트 명확한가?
- [ ] 각 프롬프트의 6계층 구조가 일관적인가?
- [ ] Python 구현 예시가 충분한가?

### Week 2: 에이전트 프롬프트 구현 (10시간)

#### Task 2.1: CompanyAnalyst 프롬프트 구현 (4시간)
**대상**: LLM 기반 기업 분석 로직

구현 단계:
1. `src/hirekit/agents/company_analyst.py` 생성
   ```python
   class CompanyAnalyst:
       def __init__(self, llm_config):
           self.system_prompt = self._build_prompt()

       def _build_prompt(self) -> str:
           # AGENT_PROMPTS.md의 CompanyAnalyst 프롬프트 적용
           pass

       def analyze(self, company_data: Dict) -> str:
           # LLM 호출 + 출력 검증
           pass
   ```

2. 출력 검증 레이어
   ```python
   class ReportValidator:
       def validate_accuracy(self, report: str) -> List[str]:
           # 6가지 정보층 검증
           pass

       def validate_sections(self, report: str) -> List[str]:
           # 12섹션 체크리스트 검증
           pass
   ```

3. 테스트 작성
   - 30개 회사 × 2언어 (한국어/영어) 샘플 리포트 생성
   - 품질 메트릭 측정 (정확도, 스캔 가능성, 행동 가능성)

#### Task 2.2: JobMatcher 프롬프트 구현 (3시간)
**대상**: 공고-이력서 매칭 분석

구현 단계:
1. `src/hirekit/agents/job_matcher.py` 생성
2. JD 파싱 + 요구사항 추출 (15+ 요구사항)
3. 사용자 경험과의 매칭 점수 (confidence level 기반)
4. 간격 채우기 전략 생성 (학습 시간, 면접 대응)

#### Task 2.3: InterviewCoach 프롬프트 구현 (3시간)
**대상**: 회사별 맞춤 면접 준비

구현 단계:
1. `src/hirekit/agents/interview_coach.py` 생성
2. 예상 질문 생성 (회사 특화)
3. STAR 프레임워크 기반 답변 생성
4. 레드플래그 감지 + 대응책 생성

---

## 📊 구현 로드맵

```
Week 1 (Documentation Polish)
├── Day 1-2: README 개선 + 검증
├── Day 3: 한국어 README 자국화
└── Day 4-5: 가이드 문서 팀 리뷰

Week 2 (Agent Implementation)
├── Day 1-2: CompanyAnalyst 구현 + 30개 회사 테스트
├── Day 3: JobMatcher 구현
└── Day 4-5: InterviewCoach 구현 + 품질 테스트

Week 3+ (Polish & Launch)
├── 사용자 피드백 수집 (5-10명)
├── 반복 개선
└── PyPI 배포
```

---

## 🔍 검증 기준

### README 30초 룰 검증
```
30초 지나서 사용자가 이해해야 할 것:
[ ] 뭔지 (What) — CLI 도구, 기업 분석
[ ] 왜 필요한지 (Why) — 4-8시간 걸리는 작업을 2분으로
[ ] 어떻게 쓰는지 (How) — pip install → configure → analyze
[ ] 다음이 뭔가 (Next) — compare, match, interview 명령어들
```

### 에이전트 프롬프트 품질 검증
```
CompanyAnalyst:
[ ] 모든 수치에 소스 표시 (DART, 기사 링크)
[ ] 당신에게 미치는 영향 해석 (연봉, 기술, 문화)
[ ] 리스크 → 대응책 제시
[ ] 리포트 <8,000 토큰
[ ] 한국어/영어 일관성

JobMatcher:
[ ] 15+ 요구사항 추출
[ ] 각 요구사항 점수 + 신뢰도
[ ] 학습 시간 예상 (gap 별)
[ ] 면접 대응책 구체적
[ ] "당신은 부족합니다" 아닌 "여기 준비 가이드"

InterviewCoach:
[ ] 10-12 예상 질문 (회사 특화)
[ ] 각 질문의 STAR 답변틀
[ ] 회사 최근 뉴스 통합
[ ] 3가지 스마트 질문 제시
[ ] Post-interview 팔로업 전략
```

### 리포트 품질 검증
```
6가지 정보층:
[ ] Accuracy: 모든 수치에 소스+기준일
[ ] Job Seeker Lens: 당신에게 미치는 영향
[ ] Scannability: 각 섹션 <300 tokens
[ ] Actionability: 리스크마다 대응책
[ ] Tone: 희망적이되 신뢰성 있음
[ ] Evidence: 모든 주장에 2개 이상 소스

12섹션:
[ ] Executive Summary (100t)
[ ] Financial Health (300t)
[ ] Tech Stack (200t)
[ ] Recent News (200t)
[ ] Culture (150t)
[ ] Compensation (100t)
[ ] Growth (200t)
[ ] Scorecard (200t)
[ ] Interview Prep (150t)
[ ] Risks (100t)
[ ] Similar Companies (100t)
[ ] Action Items (50t)
```

---

## 📁 생성된 문서 정리

### 검토 문서
- **`DOCUMENTATION_REVIEW.md`** — 종합 검토 리포트 (623줄)
  - README 30초 룰 분석
  - 영문/한국어 품질 평가
  - 에이전트 프롬프트 설계 원칙

### 구현 가이드
- **`docs/AGENT_PROMPTS.md`** — 3개 에이전트 프롬프트 상세 (863줄)
  - CompanyAnalyst: 기업 분석 전담
  - JobMatcher: 공고-이력서 매칭
  - InterviewCoach: 회사별 면접 준비
  - 각 에이전트별 역할/원칙/제약/형식/체크리스트

- **`docs/REPORT_QUALITY_GUIDE.md`** — 리포트 글쓰기 가이드 (879줄)
  - 6가지 정보층 (정확도/직업자관점/스캔가능성/행동가능성/톤/근거)
  - 12섹션별 상세 체크리스트 + 예시
  - Before/After 비교
  - 자동 검증 코드 예시

- **`README_IMPROVED.md`** — README 개선안 (462줄)
  - 30초 룰 충족 버전
  - 영문 재작성
  - 한국어 자국화 전체 버전

### 이 파일
- **`DOCUMENTATION_IMPLEMENTATION_PLAN.md`** — 구현 계획 (현재 파일)

---

## 🎯 핵심 인사이트

### 1. 한국 오픈소스의 비상
HireKit은 다음 이유로 GitHub star 폭발 가능성 높음:
- ✅ 한국 시장 특화 (DART 공시, 네이버 뉴스)
- ✅ 취업자 痛점 해결 (실제 4-8시간 절감)
- ✅ 데이터 신뢰성 (추측 아닌 공시 기반)
- ✅ 엔드투엔드 경험 (분석→매칭→면접→이력서)

### 2. 에이전트 프롬프트 설계 원칙
모든 에이전트는 **6계층 구조** 따라야 함:
```
역할 → 원칙 → 제약 → 형식 → 실패모드 → 체크리스트
```
이는 일관성과 품질을 보장함.

### 3. 리포트 글쓰기의 6가지 정보층
좋은 리포트 = 사용자가 의사결정을 내릴 수 있는 리포트
```
Accuracy → Job Seeker Lens → Scannability →
Actionability → Tone → Evidence
```

### 4. 한국어 자국화 vs 영문 번역
- ❌ 단순 번역: 영문을 한국어로만 바꿈
- ✅ 자국화: 한국 취업 시장 언어 + 맥락 + 톤 통합

---

## 💡 추가 개선 아이디어 (Phase 2+)

### UI/UX 개선
- [ ] Rich 터미널 UI (현재: 마크다운만)
- [ ] 웹 대시보드 (보고서 열람 + 비교)
- [ ] Slack/Discord 통합

### 데이터 소스 확대
- [ ] 비상장 회사 (Crunchbase, Pitchbook)
- [ ] 해외 회사 (SEC Edgar, Companies House)
- [ ] Glassdoor/LinkedIn 통합 (법적 이슈 확인 후)

### AI 강화
- [ ] 실시간 시장 분석 (뉴스 → 영향도)
- [ ] 급여 추천 (시장 + 경력 + 회사 고려)
- [ ] 커리어 경로 제안 ("5년 후 이 회사에서 어디로?")

### 커뮤니티
- [ ] "Made with HireKit" 갤러리
- [ ] 사용자 리포트 공유 (익명화)
- [ ] 플러그인 마켓플레이스

---

## 📞 Q&A

**Q: 모든 가이드 문서를 다 적용해야 하나?**
A: 아니오. Week 1 (문서 개선)부터 시작하고, Week 2 (에이전트 구현)는 선택사항.
   최소 필수: README 개선 + 한국어 자국화.

**Q: 에이전트 프롬프트를 다른 LLM (Claude vs GPT vs Gemini)으로 테스트?**
A: 권장함. 각 LLM은 프롬프트에 다르게 반응함.
   최소 2개 LLM 테스트: OpenAI (GPT-4) + Anthropic (Claude-3).

**Q: 리포트 품질 검증을 어떻게 자동화?**
A: `ReportValidator` 클래스 (Python) 구현:
   - 정확도: 정규식으로 소스 참조 확인
   - 토큰: tiktoken으로 계산
   - 체크리스트: LLM 평가 (메타 평가)

**Q: 한국어 리포트와 영문 리포트 구분?**
A: 런타임 플래그: `hirekit analyze 카카오 --language ko`
   또는 설정: `hirekit configure --language ko`

---

## 🎬 최종 체크리스트

### 배포 전 필수 확인
```
Documentation:
[ ] README 개선 완료 + 30초 룰 검증
[ ] 한국어 README 자국화 완료
[ ] AGENT_PROMPTS.md 팀 리뷰 완료
[ ] REPORT_QUALITY_GUIDE.md 적용 확인

Testing:
[ ] 30개 회사 리포트 샘플 생성 (한국어 10 + 영문 10 + 기타 10)
[ ] 3개 에이전트 각각 5개 시나리오 테스트
[ ] 사용자 피드백 5명 이상 수집

Code:
[ ] 자동 검증 로직 구현 (Report QA)
[ ] 언어 지원 (한국어/영어) 확인
[ ] 에러 처리 + 로깅
[ ] 타입 힌트 완성

Release:
[ ] CHANGELOG 업데이트
[ ] PyPI 배포 준비
[ ] GitHub Release Notes 작성
[ ] 커뮤니티 공지 (GeekNews, OKKY)
```

---

## 📚 참고 자료

### 생성된 문서
1. **DOCUMENTATION_REVIEW.md** — 현재 상태 분석
2. **docs/AGENT_PROMPTS.md** — 프롬프트 설계 상세
3. **docs/REPORT_QUALITY_GUIDE.md** — 글쓰기 가이드
4. **README_IMPROVED.md** — 개선안 샘플

### 외부 자료
- [30-Seconds README Rule](https://github.com/30-seconds/30-seconds-of-code#readme) — 오픈소스 문서 모범 사례
- [Chain of Density Summarization](https://arxiv.org/abs/2309.04269) — 압축 글쓰기 원칙
- [STAR Interview Framework](https://www.themuse.com/advice/tell-me-about-a-time-you-failed) — 행동 면접 표준
- [Prompt Engineering Best Practices](https://platform.openai.com/docs/guides/prompt-engineering) — LLM 프롬프트 설계

---

## 🚀 다음 세션 액션

```bash
# 1. 문서 검토
cd /Users/ziho/Desktop/ziho_dev/hirekit
cat DOCUMENTATION_REVIEW.md

# 2. README 개선 적용
# README_IMPROVED.md의 "Why/How/Next" 섹션을 README.md에 통합

# 3. 한국어 자국화
# README_IMPROVED.md의 한국어 버전을 README.ko.md에 통합

# 4. 에이전트 프롬프트 구현 시작
# docs/AGENT_PROMPTS.md를 참고하여 CompanyAnalyst 구현

# 5. 리포트 검증 자동화
# docs/REPORT_QUALITY_GUIDE.md의 체크리스트를 코드로 변환
```

---

## 최종 요약

이 계획은 HireKit을 **글로벌 오픈소스 스탠다드**로 끌어올리기 위한 3가지 축:

1. **문서** (5시간): README 개선 + 가이드 완성
2. **에이전트** (10시간): LLM 기반 분석 엔진 구현
3. **품질** (지속): 6층 정보층 + 12섹션 체크리스트로 일관성 보장

**예상 결과**: GitHub ⭐ +20-30%, PyPI 월 다운로드 +100-150%
