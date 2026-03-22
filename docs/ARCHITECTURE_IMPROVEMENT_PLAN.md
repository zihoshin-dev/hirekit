# HireKit 구조 진단 및 고도화 계획

## 문서 목적

이 문서는 `hirekit`의 현재 구조를 빠르게 파악하고, 실제 운영/확장 관점에서 어떤 순서로 고도화해야 하는지 정리한 실행 문서예요.

목표는 세 가지예요.

1. 현재 구조를 레이어별로 명확히 설명하기
2. 동작은 하지만 구조적으로 위험한 지점을 구분하기
3. 작은 PR 단위로 나눌 수 있는 개선 로드맵을 제시하기

---

## 한눈에 보는 결론

HireKit은 이미 좋은 출발점을 갖고 있어요.

- `src` 기반 패키지 구조가 명확해요
- `cli -> engine -> sources/core/output/templates` 레이어가 읽혀요
- 테스트 기반선이 존재해요
- 한국 취업 준비 도메인에 맞는 기능 방향이 일관돼요

하지만 지금 단계의 핵심 과제는 "기능 추가"보다 "구조 일관성 회복"이에요.

특히 아래 네 가지가 우선이에요.

1. 캐시 hit 시 결과가 불완전하게 복원되는 문제 수정
2. 패키징 메타데이터와 실제 구현의 불일치 해소
3. 선언만 있고 실제 런타임에 반영되지 않는 설정/옵션 정리
4. 커진 CLI/Engine 파일을 역할별로 분리

---

## 현재 구조

### 1. 최상위 구조

현재 핵심 디렉터리는 아래처럼 이해하면 돼요.

```text
hirekit/
├── src/hirekit/
│   ├── cli/         # Typer CLI 엔트리
│   ├── core/        # 설정, 캐시, 병렬 수집, 보안, taxonomy
│   ├── engine/      # 실제 도메인 로직과 오케스트레이션
│   ├── llm/         # LLM adapter
│   ├── output/      # 렌더러
│   ├── sources/     # 데이터 수집 플러그인
│   └── templates/   # Markdown 템플릿
├── tests/           # 계층별 테스트
├── docs/            # 공개/내부 문서
├── tools/           # 데이터/데모 보조 스크립트
└── pyproject.toml   # 패키지 및 엔트리포인트 정의
```

### 2. 실행 흐름

대표 흐름인 `hirekit analyze`는 아래 구조예요.

```text
CLI(app.py)
  -> Config 로드
  -> CompanyAnalyzer
      -> SourceRegistry / source discovery
      -> collect_parallel
      -> section assembly
      -> scorecard 계산
      -> optional LLM enhancement
  -> Markdown/JSON/terminal 출력
```

### 3. 모듈 책임

#### CLI

- 사용자 입력 파싱
- 상태 메시지 출력
- 엔진 호출
- 파일 저장 또는 terminal/json 출력

현재는 `app.py` 한 파일에 명령이 집중돼 있어요.

#### Engine

- 기업 분석
- JD 매칭
- 면접 준비
- 이력서 리뷰
- 자기소개서 코칭

도메인 가치는 여기 가장 많이 들어 있어요.

#### Sources

- DART, GitHub, 뉴스, 검색, 커뮤니티 등 외부 데이터 수집
- `SourceRegistry` 기반 플러그인 구조
- 지역별 소스 분리(`kr`, `global_`, `us`)

#### Output / Templates

- Markdown 렌더링
- 템플릿 기반 보고서 생성

---

## 확인된 강점

### 테스트 기반선이 있음

현재 테스트는 상당히 넓게 깔려 있어요.

- CLI 테스트
- core 테스트
- engine 테스트
- source 테스트
- output 테스트

점검 시점 기준:

- `pytest -q`: 344 passed
- `mypy src`: clean

이건 구조 개선을 시작하기 좋은 상태예요.

### 레이어가 최소한 분리돼 있음

완벽하진 않지만 "입력", "분석", "수집", "출력"이 섞여 있지는 않아요.
즉, 리라이트보다 정리형 리팩터링이 더 적합해요.

### 패키지로서의 방향성이 분명함

`pyproject.toml`, entry point, optional dependency, docs, GitHub Actions가 모두 있어요.
즉 "개인 스크립트 묶음"이 아니라 "배포 가능한 제품" 지향이 이미 반영돼 있어요.

---

## 핵심 문제 진단

## 1. 캐시 복원 품질이 깨져 있어요

가장 먼저 고쳐야 할 문제예요.

현재 `CompanyAnalyzer.analyze()`는 캐시 miss 때는 정상적으로 `scorecard`, `source_results`를 채워요.
하지만 캐시 hit 때는 직렬화된 결과 중 일부만 복원하고 있어요.

결과적으로 같은 명령을 두 번 실행했을 때 두 번째 결과가 약해질 수 있어요.

예상 영향:

- `scorecard`가 없는 리포트 반환 가능
- `source_results`가 빈 리스트가 될 수 있음
- CLI 요약 표가 비거나 품질이 달라질 수 있음
- 캐시가 "성능 최적화"가 아니라 "출력 일관성 저하"로 바뀜

이건 버그이자 신뢰성 문제예요.

---

## 2. 패키징 선언과 실제 구현이 어긋나요

`pyproject.toml`에는 output entry point가 세 개 선언돼 있어요.

- `markdown`
- `json`
- `terminal`

하지만 실제 구현은 사실상 Markdown renderer만 존재해요.
즉, 설치 후 entry-point 로딩 시 일부가 깨질 수 있어요.

이 문제는 두 가지 측면에서 위험해요.

1. 패키지 신뢰도 저하
2. 향후 플러그인 구조 확장 시 메타데이터 오염

README와 패키지 선언이 강하게 약속한 기능은 실제 파일 구조와 맞아야 해요.

---

## 3. 설정과 런타임이 분리돼 있어요

현재 설정 모델에는 아래처럼 미래 확장을 위한 필드가 존재해요.

- `sources.enabled`
- `sources.disabled`
- `output.template`
- `analysis.default_region`

그런데 실제 런타임에서는 일부만 부분적으로 반영되고, 일부는 거의 사용되지 않아요.

또 `tier`도 CLI에는 중요 옵션처럼 보이지만, 실제로는 섹션 필터링에 충분히 연결되지 않았어요.

이런 상태가 되면 사용자는 "설정 가능"하다고 믿지만, 내부적으로는 no-op인 옵션이 늘어나요.

이 문제는 기능 부족보다 더 안 좋아요.
왜냐하면 API/CLI 계약 자체가 흐려지기 때문이에요.

---

## 4. 핵심 파일 몇 개에 복잡도가 몰려 있어요

현재 구조에서 특히 집중도가 높은 파일은 아래예요.

- `engine/interview_questions.py`
- `engine/interview_prep.py`
- `cli/app.py`
- `engine/cover_letter.py`
- `engine/company_analyzer.py`
- `engine/jd_matcher.py`
- `engine/resume_advisor.py`

이 상태가 계속되면 다음 문제가 생겨요.

- 변경 영향 범위를 예측하기 어려움
- 테스트가 있어도 리팩터링 비용이 커짐
- 신규 기여자가 진입하기 어려움
- 명령별 UX와 엔진별 정책이 서로 섞이기 시작함

지금은 "아직 버틸 수 있는 모놀리식 파일" 단계예요.
조금만 더 커지면 유지보수 속도가 급격히 떨어질 가능성이 커요.

---

## 5. 플러그인 구조가 반쯤만 정리돼 있어요

소스 수집은 `SourceRegistry` 기반이라 방향은 좋아요.
하지만 실제 등록 경로는 두 갈래예요.

- import side effect 기반 `@SourceRegistry.register`
- entry_points 기반 discovery

즉, 구조상 "플러그인 시스템"처럼 보이지만 실제론 "내장 소스 import + 패키지 메타데이터"의 혼합 모델이에요.

이 혼합 구조는 초기엔 빠르지만, 이후 아래 문제가 생겨요.

- 어떤 소스가 실제로 등록되는지 추적 어려움
- editable install / wheel install / 테스트 환경별 차이 발생 가능
- source catalog 관리가 어려움

중장기적으로는 등록 방식을 하나로 정리해야 해요.

---

## 6. 품질 게이트 범위가 좁아요

현재 CI는 `src/`, `tests/` 기준으로는 잘 동작해요.
하지만 `tools/`까지 포함한 저장소 전체 품질은 보장하지 않아요.

실제 점검에서도 `ruff check .`는 `tools/`에서 실패했어요.

즉, 지금의 CI는 "패키지 코어"는 지키지만 "리포지토리 전체"는 지키지 못해요.

이건 반드시 나쁜 건 아니지만, 경계를 문서로 명확히 해야 해요.

- 이 저장소가 package-only 품질을 보장하는지
- tools까지 release surface인지

이 구분이 없으면 유지보수 기준이 계속 흔들려요.

---

## 7. 테스트는 많지만 중요한 회귀 시나리오가 비어 있어요

현재 테스트는 많지만, 구조적 회귀를 막는 테스트가 일부 부족해요.

대표적으로 부족한 것:

- cache hit 후 scorecard/source_results 보존 테스트
- output entry point load 테스트
- 실제 source registry catalog 일관성 테스트
- tier 옵션이 섹션 수/출력에 미치는 영향 테스트
- CLI 명령별 golden output 테스트

즉 "함수가 돌아가는가"는 잘 보는데,
"제품 계약이 유지되는가"는 아직 덜 보고 있어요.

---

## 권장 고도화 원칙

개선은 아래 원칙으로 가져가는 게 좋아요.

### 1. 리라이트보다 분해

지금은 전면 재작성보다, 기존 코드의 역할 경계를 명확히 쪼개는 편이 훨씬 안전해요.

### 2. 선언과 동작을 일치

설정, README, CLI help, entry point, 실제 구현이 같은 계약을 말해야 해요.

### 3. 기능보다 신뢰성 우선

새 source 추가보다 먼저,
"같은 입력이면 같은 품질의 결과가 나온다"를 보장해야 해요.

### 4. 작은 PR 단위 유지

한 번에 대수술하면 이득보다 회귀 위험이 커요.
각 단계는 독립적으로 merge 가능한 크기로 나눠야 해요.

---

## 단계별 개선 계획

## Phase 1. 신뢰성 복구

목표: 현재 기능의 계약을 깨뜨리는 문제를 먼저 제거해요.

### 작업 항목

1. 캐시 복원 로직 수정
2. `AnalysisReport` 직렬화/역직렬화 경로 정식화
3. output entry point 정리
4. 실제 없는 renderer는 구현하거나 선언에서 제거
5. cache hit 회귀 테스트 추가
6. entry-point load 테스트 추가

### 완료 기준

- 캐시 전후 결과 구조가 동일해요
- package metadata load가 모두 성공해요
- `analyze` 결과가 cold/hot cache에서 일관돼요

### 기대 효과

- 사용자 신뢰도 상승
- CLI 결과 일관성 확보
- 패키징 안정성 회복

---

## Phase 2. 계약 정리

목표: 설정과 런타임의 어긋남을 줄여요.

### 작업 항목

1. `sources.enabled` 정책 결정
   - 실제로 지원할지
   - 아니면 제거할지
2. `output.template` 실제 연결
3. `analysis.default_region` 기본값 흐름 반영
4. `tier`를 실제 섹션 선택/수집 깊이 정책과 연결
5. README와 CLI help를 실제 동작 기준으로 수정

### 완료 기준

- 설정 파일의 각 필드가 실제 동작에 영향을 줘요
- 동작하지 않는 옵션은 제거돼요
- 문서와 코드가 같은 계약을 설명해요

### 기대 효과

- 설정 신뢰성 향상
- 유지보수자 혼란 감소
- 사용자 학습 비용 감소

---

## Phase 3. CLI 분해

목표: `app.py`를 명령별로 분리해요.

### 권장 구조

```text
src/hirekit/cli/
├── app.py
├── commands/
│   ├── analyze.py
│   ├── match.py
│   ├── interview.py
│   ├── resume.py
│   ├── coverletter.py
│   ├── pipeline.py
│   └── sources.py
└── shared.py
```

### 작업 항목

1. 명령별 핸들러 분리
2. 공통 출력 로직 공유화
3. `_get_llm`, `_load_profile`, 공통 path 처리 정리
4. CLI 테스트를 명령 단위로 재배치

### 완료 기준

- `app.py`는 command registration 중심만 남아요
- 명령별 변경이 서로 덜 얽혀요
- CLI 테스트가 명령별 책임과 대응돼요

### 기대 효과

- 명령 추가/수정이 쉬워짐
- UX 개선 작업 병렬화 가능
- 리뷰 범위가 작아짐

---

## Phase 4. Analyzer 분해

목표: `CompanyAnalyzer`를 orchestration 중심 클래스로 되돌려요.

### 권장 분리 방향

```text
engine/company_analysis/
├── orchestrator.py
├── source_selection.py
├── section_mapper.py
├── cache_codec.py
├── scoring.py
└── llm_enrichment.py
```

### 작업 항목

1. source 선택 로직 분리
2. section mapping 분리
3. score 계산 로직 별도 모듈화
4. cache serialization codec 도입
5. LLM enhancement 모듈 분리

### 완료 기준

- `CompanyAnalyzer`는 흐름 제어만 담당해요
- 점수 계산과 수집 정책이 독립 테스트 가능해요
- 캐시/LLM/section mapping을 개별 교체할 수 있어요

### 기대 효과

- 기능 확장 속도 상승
- 디버깅 난이도 감소
- 분석 정책 실험이 쉬워짐

---

## Phase 5. Source 플랫폼 정식화

목표: 소스 등록과 검증 방식을 일관되게 만들어요.

### 작업 항목

1. 내장 source catalog를 명시적 리스트로 관리
2. `@register`와 entry_points 중 하나를 주 방식으로 선택
3. source contract test 추가
4. source metadata 표준화
   - 지역
   - 섹션
   - timeout
   - freshness
   - required env var
5. source 수집 실패 이유를 구조화

### 완료 기준

- 어떤 source가 등록되는지 예측 가능해요
- 설치 방식에 따라 등록 결과가 흔들리지 않아요
- 새 source 추가 절차가 단순해져요

### 기대 효과

- 수집 파이프라인 안정화
- source 추가 비용 감소
- 디버깅 효율 향상

---

## Phase 6. 품질 게이트 강화

목표: 제품 계약 중심의 테스트와 CI를 만듭니다.

### 작업 항목

1. package metadata smoke test
2. cache regression test
3. CLI golden output test
4. source registry consistency test
5. markdown snapshot/golden test 강화
6. coverage 기준 상향
   - 50 -> 70 -> 80 단계 권장
7. `tools/`를 release surface에 포함할지 정책 결정

### 완료 기준

- 깨지면 안 되는 계약이 테스트로 표현돼요
- CI 실패 메시지가 더 직접적이에요
- release 전 체크리스트가 명확해져요

### 기대 효과

- 회귀 비용 감소
- 리뷰 품질 향상
- 배포 안정성 상승

---

## 우선순위 제안

실행 순서는 아래가 좋아요.

### P0

1. 캐시 복원 버그 수정
2. output entry point 정리
3. cache/entry-point 회귀 테스트 추가

### P1

1. dead config 제거 또는 실제 반영
2. `tier` 동작 명확화
3. README/CLI 계약 정리

### P2

1. CLI 분해
2. CompanyAnalyzer 분해

### P3

1. source platform 정식화
2. 품질 게이트 고도화
3. coverage 상향

---

## 추천 PR 분할

작은 PR로 나누면 아래 정도가 적당해요.

### PR 1. Cache correctness fix

- cache codec 추가
- cache hit 결과 보존
- 회귀 테스트 추가

### PR 2. Packaging cleanup

- output entry points 정리
- metadata smoke test 추가
- README 계약 수정

### PR 3. Config contract cleanup

- dead config 제거 또는 구현
- tier 정책 정리
- CLI help 정돈

### PR 4. CLI modularization

- command 모듈 분리
- 공통 유틸 추출

### PR 5. Analyzer modularization

- scoring/section mapping/source selection 분리

### PR 6. Source platform hardening

- registry/catalog 정리
- source contract test 추가

---

## 성공 지표

개선이 끝났는지 보려면 아래 지표를 보면 돼요.

### 구조 지표

- `app.py` LOC 감소
- `company_analyzer.py` LOC 감소
- 명령/분석 책임 분리 완료

### 품질 지표

- cache 관련 회귀 0건
- entry-point load 실패 0건
- CI coverage 목표 상향 달성

### 제품 지표

- 동일 입력 반복 시 결과 일관성 확보
- 설정 옵션이 실제 동작과 일치
- 새 source 추가 리드타임 감소

---

## 바로 실행 가능한 첫 작업

지금 당장 시작한다면 아래 순서가 가장 좋아요.

1. `AnalysisReport` cache codec 설계
2. cache hit 회귀 테스트 작성
3. output entry point 깨진 선언 정리
4. `tier`와 `sources.enabled` 계약 결정

이 네 개만 해도 구조 신뢰도가 체감될 만큼 올라가요.

---

## 최종 판단

HireKit은 "다 뜯어고쳐야 하는 프로젝트"는 아니에요.
오히려 핵심 도메인 가치와 테스트 기반선은 이미 충분히 괜찮아요.

지금 필요한 건 리라이트가 아니라 아래예요.

- 버그성 구조 문제 제거
- 선언과 동작의 일치
- 큰 파일의 책임 분리
- source/platform 계약 정식화

즉, 방향은 맞고 구조 정리가 필요한 단계예요.

이 시점에 정리해두면 이후 기능 추가 속도와 품질이 같이 올라갈 가능성이 커요.
