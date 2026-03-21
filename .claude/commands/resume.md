---
description: 이력서를 분석하여 정량적 피드백을 제공해요
argument-hint: <이력서파일경로> [--format pdf|md|txt] [--target <직군>]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 이력서를 분석합니다.

## 실행 절차

1. HireKit CLI로 이력서 분석 실행:
```bash
.venv/bin/hirekit resume $ARGUMENTS --output json
```

2. 결과를 바탕으로 다음을 제공:
- ATS 통과율 예측 (키워드 매칭 기반)
- 경력 기술 정량화 점수 (수치 포함 비율)
- 액션 동사 다양성 분석
- 포맷/가독성 평가 (섹션 구조, 길이, 일관성)
- 직군별 핵심 키워드 누락 항목
- 개선 우선순위 Top 5 (즉시 적용 가능한 순서)

3. 이력서 체크리스트:
- 각 경력 항목: [동사] + [행동] + [결과 수치] 구조 확인
- 연락처, 링크(GitHub/LinkedIn) 포함 여부
- 최근 3년 경력 상세도 (5년 이상은 압축)
