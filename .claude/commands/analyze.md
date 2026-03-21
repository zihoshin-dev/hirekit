---
description: 기업을 분석하여 5차원 스코어카드 리포트를 생성해요
argument-hint: <기업명> [--tier 1|2|3]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 기업에 대한 종합 분석을 실행합니다.

## 실행 절차

1. HireKit CLI로 기업 분석 실행:
```bash
.venv/bin/hirekit analyze $ARGUMENTS --output json
```

2. 결과 JSON을 분석하여 다음을 제공:
- 5차원 스코어카드 요약 (Job Fit, Growth, Compensation, Culture, Career Leverage)
- 핵심 강점/약점 3개씩
- 이 회사에 지원할 때 알아야 할 핵심 포인트
- 추천 여부 (Go/Hold/Pass)와 근거

3. 추가 컨텍스트가 필요하면 데모 데이터 참조:
```bash
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; [print(json.dumps(c,ensure_ascii=False,indent=2)) for c in json.load(sys.stdin) if '$ARGUMENTS' in c.get('name','')]"
```
