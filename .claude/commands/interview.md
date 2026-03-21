---
description: 면접 준비를 위한 질문 생성과 답변 가이드를 제공해요
argument-hint: <기업명> [--type behavioral|technical|culture] [--rounds 1|2|3]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 면접 준비를 실행합니다.

## 실행 절차

1. HireKit CLI로 면접 질문 생성:
```bash
.venv/bin/hirekit interview $ARGUMENTS --output json
```

2. 결과를 바탕으로 다음을 제공:
- 예상 면접 질문 10개 (Behavioral 4 / Technical 4 / Culture Fit 2)
- 각 질문별 STAR 프레임워크 기반 답변 가이드
- 이 회사 면접 특이사항 (알려진 프로세스, 분위기, 주의사항)
- 역질문 추천 3개 (면접관에게 할 질문)

3. 기업 데이터 보강:
```bash
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; [print(json.dumps(c,ensure_ascii=False,indent=2)) for c in json.load(sys.stdin) if '$ARGUMENTS' in c.get('name','')]"
```
