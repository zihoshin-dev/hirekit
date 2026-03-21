---
name: career-tools
description: 이력서 분석, 자기소개서 피드백, 경력기술서 작성, 커버레터 개선. "이력서", "자소서", "경력기술서", "커버레터", "자기소개서 피드백" 등의 요청에 트리거됩니다.
---

HireKit CLI를 사용하여 이력서·자소서 분석과 피드백을 제공합니다.

## 사용 가능한 명령어

- `hirekit resume <파일경로> --output json` — 이력서 정량 분석 (ATS 통과율, 키워드, 수치화)
- `hirekit coverletter <파일경로> --output json` — 자소서 피드백 (클리셰 감지, 완성도)
- `hirekit resume <파일경로> --target <직군>` — 직군별 맞춤 분석

## 실행 방법

이력서:
```bash
.venv/bin/hirekit resume <파일경로> --output json
```

자소서:
```bash
cd /Users/ziho/Desktop/ziho_dev/hirekit && .venv/bin/hirekit coverletter <파일경로> --output json
```

## 이력서 품질 기준

| 항목 | 기준 |
|------|------|
| 수치화율 | 경력 항목의 70%↑에 수치 포함 |
| ATS 키워드 | 직군 핵심 키워드 80%↑ 포함 |
| 액션 동사 | 항목마다 강한 동사로 시작 |
| 길이 | 경력 5년 미만: 1페이지, 이상: 2페이지 |

## 자소서 클리셰 감지 기준

감점 표현 예시:
- "열정적으로", "도전하겠습니다", "성장하고 싶습니다"
- "귀사의 비전에 공감하여"
- 수치 없는 역량 주장 ("뛰어난 커뮤니케이션 능력")

개선 방향: 구체적 사례 + 수치 + 임팩트 서술
