# HireKit CLI 가이드

취업 준비를 위한 기업 분석·JD 매칭·면접 준비·자소서·이력서 분석 통합 CLI.

## venv 경로

```bash
/Users/ziho/Desktop/ziho_dev/hirekit/.venv/bin/hirekit
```

항상 프로젝트 루트에서 실행:
```bash
.venv/bin/hirekit <command>
```

---

## 전체 명령어 레퍼런스

### analyze — 기업 분석
```bash
.venv/bin/hirekit analyze <기업명> [--tier 1|2|3] [--output json|md|html]
```
- 14개 소스에서 데이터 수집 후 5차원 스코어카드 생성
- `--tier`: 1=대기업, 2=중견기업, 3=스타트업 (기본값: 자동 감지)
- `--output json`: 구조화 JSON 출력 (파이프라인 연동용)

### match — JD 매칭 분석
```bash
.venv/bin/hirekit match "<JD텍스트>" [--profile <경로>] [--output json|md]
.venv/bin/hirekit match --url <JD URL> [--output json]
```
- JD 텍스트 또는 URL로 사용자 프로필과 매칭 분석
- `--profile`: 사용자 프로필 JSON 경로 (기본값: ~/.hirekit/profile.json)

### interview — 면접 준비
```bash
.venv/bin/hirekit interview <기업명> [--type behavioral|technical|culture|all] [--rounds 1|2|3] [--output json|md]
```
- 맞춤형 면접 질문 10~20개 + STAR 답변 가이드 생성
- `--type`: 질문 유형 필터 (기본값: all)
- `--rounds`: 면접 라운드 수 (기본값: 1)

### coverletter — 자소서 피드백
```bash
.venv/bin/hirekit coverletter <파일경로> [--company <기업명>] [--output json|md]
```
- 클리셰 감지, 구체성 점수, 완성도 평가 (A~F)
- `--company`: 지원 기업명 제공 시 맞춤 피드백

### resume — 이력서 분석
```bash
.venv/bin/hirekit resume <파일경로> [--format pdf|md|txt] [--target <직군>] [--output json|md]
```
- ATS 통과율, 키워드 분석, 수치화율, 액션 동사 다양성 평가
- `--target`: 직군 지정 (예: backend, product, design)

### pipeline — 5단계 통합 파이프라인
```bash
.venv/bin/hirekit pipeline <기업명> [--jd <URL>] [--resume <경로>] [--coverletter <경로>] [--output json|md]
```
- 위 5개 명령어를 순서대로 실행 후 통합 리포트 생성

---

## 데이터 소스 14개

| # | 소스 | 유형 | 수집 내용 |
|---|------|------|-----------|
| 1 | LinkedIn | SNS | 채용 공고, 직원 리뷰 |
| 2 | Glassdoor | 리뷰 | 연봉, 문화, 면접 후기 |
| 3 | Blind | 커뮤니티 | 내부자 의견, 복지 실태 |
| 4 | Wanted | 채용 | JD, 기업 소개 |
| 5 | Jumpit | 채용 | 기술 스택, 복지 |
| 6 | Rocketpunch | 스타트업 | 투자 현황, 팀 규모 |
| 7 | DART | 공시 | 재무제표, 공시 정보 |
| 8 | Crunchbase | 투자 | 펀딩 라운드, 투자사 |
| 9 | GitHub | 기술 | 오픈소스 기여, 기술 스택 |
| 10 | StackShare | 기술 | 사용 기술 스택 |
| 11 | Naver News | 뉴스 | 최신 뉴스, 이슈 |
| 12 | Google News | 뉴스 | 영문 글로벌 뉴스 |
| 13 | Company Website | 공식 | 비전, 미션, 제품 |
| 14 | Toss Community | 커뮤니티 | 토스 유저 반응, 평판 |

---

## JSON 출력 스키마

```json
{
  "company": "기업명",
  "tier": 1,
  "scores": {
    "job_fit": 85,
    "growth": 78,
    "compensation": 72,
    "culture": 80,
    "career_leverage": 90,
    "total": 81
  },
  "recommendation": "Go",
  "strengths": ["강점1", "강점2", "강점3"],
  "weaknesses": ["약점1", "약점2", "약점3"],
  "key_points": ["핵심포인트1", "핵심포인트2"],
  "sources": ["source1", "source2"],
  "updated_at": "2026-03-22T00:00:00Z"
}
```

---

## 데모 데이터

79개 한국 주요 IT/테크 기업 사전 분석 데이터:

```bash
# 전체 목록
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; [print(c.get('name')) for c in json.load(sys.stdin)]"

# 특정 기업 조회
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; [print(json.dumps(c,ensure_ascii=False,indent=2)) for c in json.load(sys.stdin) if '카카오' in c.get('name','')]"

# 기업별 상세 데이터
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/companies/<기업명>.json
```

---

## 사용 팁

1. **빠른 조회**: 분석 시간이 부족하면 데모 데이터 먼저 확인
2. **JSON 출력**: 파이프라인 연동 시 항상 `--output json` 사용
3. **tier 지정**: 대기업/스타트업은 평가 기준이 다르므로 명시 권장
4. **순서 추천**: analyze → match → interview → coverletter → resume (pipeline 명령어로 일괄 실행 가능)
