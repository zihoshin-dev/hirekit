---
description: 기업 DB를 최신 데이터로 갱신해요
argument-hint: [--source dart|market|ai|all] [--company 기업명] [--dry-run]
allowed-tools: [Bash, Read]
---

기업 DB를 갱신합니다.

## 실행

```bash
cd /Users/ziho/Desktop/ziho_dev/hirekit
.venv/bin/python tools/update_company_db.py $ARGUMENTS
```

## 소스 옵션

| 소스 | 설명 |
|------|------|
| `dart` | DART API 기본 정보 (CEO, 주소, 설립일 등) |
| `market` | KRX/Yahoo Finance 시장 데이터 |
| `ai` | GitHub AI 레포 메트릭 |
| `all` | 전체 소스 순차 갱신 (기본값) |

## 갱신 후

- 신선도 확인: `.venv/bin/python tools/check_freshness.py`
- 변경사항 확인: `git diff docs/demo/data/`
- 테스트: `.venv/bin/pytest tests/ -x -q`
- 커밋: `git add docs/demo/data/ && git commit -m "chore(data): DB update $(date +%Y-%m-%d)"`
