---
name: company-analysis
description: 기업 분석, 회사 조사, 취업을 위한 기업 리서치. "기업 분석", "회사 분석", "○○ 어떤 회사야", "○○ 지원하려는데" 등의 요청에 트리거됩니다.
---

HireKit CLI를 사용하여 기업 분석을 수행합니다.

## 사용 가능한 명령어

- `hirekit analyze <기업명> --output json` — 14개 소스에서 데이터 수집, 5차원 스코어카드 생성
- `hirekit match <JD텍스트> --output json` — JD와 프로필 매칭 분석
- `hirekit interview <기업명> --output json` — 면접 질문 및 답변 가이드 생성

## 실행 방법

```bash
.venv/bin/hirekit analyze <기업명> --output json
```

## 5차원 스코어카드

| 차원 | 설명 |
|------|------|
| Job Fit | 직무 적합성, 요구 역량 매칭 |
| Growth | 성장성, 시장 포지션, 사업 확장성 |
| Compensation | 보상 수준, 스톡옵션, 복지 |
| Culture | 조직 문화, 워라밸, 리더십 스타일 |
| Career Leverage | 커리어 레버리지, 브랜드 가치, 네트워크 |

## 데모 데이터 (빠른 조회)

79개 한국 주요 IT/테크 기업의 사전 분석 데이터가 있습니다:

```bash
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json
```

특정 기업 조회:
```bash
cat /Users/ziho/Desktop/ziho_dev/hirekit/docs/demo/data/meta.json | python3 -c "import json,sys; [print(json.dumps(c,ensure_ascii=False,indent=2)) for c in json.load(sys.stdin) if '기업명' in c.get('name','')]"
```

## 결과 해석 가이드

- **Go (80점↑)**: 적극 지원 추천
- **Hold (60~79점)**: 조건부 지원 (갭 보완 후)
- **Pass (60점↓)**: 현재 시점 지원 비권장
