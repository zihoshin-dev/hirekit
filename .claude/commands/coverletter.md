---
description: 자기소개서 피드백과 클리셰 감지를 제공해요
argument-hint: <자소서파일경로 또는 텍스트> [--company <기업명>]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 자기소개서를 분석합니다.

## 실행 절차

1. HireKit CLI로 자소서 피드백 실행:
```bash
.venv/bin/hirekit coverletter $ARGUMENTS --output json
```

2. 결과를 바탕으로 다음을 제공:
- 클리셰 감지 목록 (감점 요인 표현과 개선 제안)
- 강점 표현 분석 (잘 쓴 구간 3개)
- 구체성 점수 (수치/사례 포함 여부)
- 지원 동기의 진정성 평가
- 항목별 개선 제안 (구체적인 문장 예시 포함)
- 전체 완성도 점수 (A~F)

3. 클리셰 표현 예시 (감지 기준):
- "열정", "도전정신", "성장하고 싶습니다" 등 추상적 표현
- 구체적 수치·사례 없는 역량 주장
- 회사 비전 단순 반복
