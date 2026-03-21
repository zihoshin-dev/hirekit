---
description: 기업분석→JD매칭→면접준비→자소서→이력서 5단계 통합 파이프라인을 실행해요
argument-hint: <기업명> [--jd <JD URL>] [--resume <이력서경로>] [--coverletter <자소서경로>]
allowed-tools: [Bash, Read, Glob, Grep]
---

$ARGUMENTS 에 대한 5단계 통합 취업 준비 파이프라인을 실행합니다.

## 실행 절차

### Step 1: 기업 분석
```bash
.venv/bin/hirekit analyze $ARGUMENTS --output json
```

### Step 2: JD 매칭 (JD URL 제공 시)
```bash
.venv/bin/hirekit match $ARGUMENTS --output json
```

### Step 3: 면접 준비
```bash
.venv/bin/hirekit interview $ARGUMENTS --output json
```

### Step 4: 자소서 피드백 (파일 제공 시)
```bash
.venv/bin/hirekit coverletter $ARGUMENTS --output json
```

### Step 5: 이력서 분석 (파일 제공 시)
```bash
.venv/bin/hirekit resume $ARGUMENTS --output json
```

## 최종 통합 리포트 구성
각 단계 결과를 종합하여 제공:
- 지원 전략 종합 판단 (Go/Hold/Pass + 근거)
- 단계별 핵심 액션 아이템 (즉시 실행 가능한 순서)
- 타임라인 제안 (지원 마감 기준 역산 준비 일정)
- 경쟁력 강화 포인트 (이 회사에서 차별화할 수 있는 요소)
