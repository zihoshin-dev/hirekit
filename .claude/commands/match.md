---
description: JD URL 또는 텍스트로 직무 매칭 분석을 실행해요
argument-hint: <JD URL 또는 텍스트> [--profile <프로필경로>]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 에 대한 JD 매칭 분석을 실행합니다.

## 실행 절차

1. HireKit CLI로 JD 매칭 분석 실행:
```bash
.venv/bin/hirekit match $ARGUMENTS --output json
```

2. 결과 JSON을 분석하여 다음을 제공:
- 전체 매칭 스코어 (0~100)
- 필수 역량 충족 여부 (Matched / Gap / Missing 분류)
- 강점 포지셔닝 포인트 3개
- 보완이 필요한 갭 3개와 대응 전략
- 지원 우선순위 추천 (High / Medium / Low)

3. 갭 분석 시 데모 데이터 참조:
```bash
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; data=json.load(sys.stdin); print(json.dumps(data[:3],ensure_ascii=False,indent=2))"
```
