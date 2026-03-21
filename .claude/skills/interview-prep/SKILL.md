---
name: interview-prep
description: 면접 준비, 면접 질문 생성, 인터뷰 준비, 답변 연습. "면접 준비", "면접 질문", "인터뷰 준비", "○○ 면접 어떻게 해" 등의 요청에 트리거됩니다.
---

HireKit CLI를 사용하여 면접 준비를 수행합니다.

## 사용 가능한 명령어

- `hirekit interview <기업명> --output json` — 맞춤형 면접 질문 + STAR 답변 가이드
- `hirekit interview <기업명> --type behavioral` — 행동 기반 질문 집중
- `hirekit interview <기업명> --type technical` — 기술 질문 집중
- `hirekit interview <기업명> --rounds 2` — 2차 면접 기준 질문

## 실행 방법

```bash
.venv/bin/hirekit interview <기업명> --output json
```

## 면접 질문 구성

| 유형 | 비중 | 예시 |
|------|------|------|
| Behavioral | 40% | "가장 어려웠던 프로젝트 경험은?" |
| Technical | 40% | "시스템 설계 / 코딩 / 도메인 지식" |
| Culture Fit | 20% | "우리 회사를 선택한 이유는?" |

## STAR 프레임워크

- **S**ituation: 상황 설명 (1~2문장)
- **T**ask: 맡은 역할과 목표
- **A**ction: 구체적으로 취한 행동
- **R**esult: 수치로 측정 가능한 결과

## 역질문 팁

면접 말미 역질문 3개 추천:
1. 팀 문화와 협업 방식
2. 이 포지션의 성공 지표
3. 입사 후 90일 기대치
