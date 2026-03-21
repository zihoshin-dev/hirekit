"""Interview question bank — 200+ categorized questions (Korean)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class QuestionCategory(StrEnum):
    PERSONALITY = "인성/적성"
    TECH_COMMON = "기술 공통"
    FRONTEND = "프론트엔드"
    BACKEND = "백엔드"
    DEVOPS = "DevOps"
    DATA = "데이터"
    MOBILE = "모바일"
    LEADERSHIP = "리더십"
    STARTUP = "스타트업"
    LARGE_CORP = "대기업"


@dataclass
class InterviewQuestion:
    """A single interview question with metadata."""

    question: str
    category: QuestionCategory
    difficulty: int  # 1=쉬움, 2=보통, 3=어려움
    frequency: int   # 1-5 (5=매우 빈출)
    answer_points: list[str] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)
    star_applicable: bool = False


@dataclass
class AnswerGuide:
    """Rule-based answer guide for a question."""

    question: str
    key_points: list[str] = field(default_factory=list)
    star_structure: dict[str, str] = field(default_factory=dict)
    anti_patterns: list[str] = field(default_factory=list)
    time_allocation_sec: int = 120  # 권장 답변 시간

    def to_markdown(self) -> str:
        lines = [f"**Q: {self.question}**\n"]
        if self.key_points:
            lines.append("**핵심 포인트:**")
            for p in self.key_points:
                lines.append(f"- {p}")
        if self.star_structure:
            lines.append("\n**STAR 구조:**")
            for k, v in self.star_structure.items():
                lines.append(f"- **{k}**: {v}")
        if self.anti_patterns:
            lines.append("\n**이런 답변은 피하세요:**")
            for a in self.anti_patterns:
                lines.append(f"- {a}")
        lines.append(f"\n*권장 답변 시간: {self.time_allocation_sec // 60}분 {self.time_allocation_sec % 60}초*")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Question Bank — 200+ questions across 10 categories
# ---------------------------------------------------------------------------

QUESTION_BANK: list[InterviewQuestion] = [

    # -----------------------------------------------------------------------
    # 인성/적성 (20개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="자신의 가장 큰 강점과 약점을 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=5,
        answer_points=["구체적 사례로 강점 입증", "약점은 개선 노력과 함께 언급", "직무 연관성 고려"],
        anti_patterns=["'강점이 너무 많아요' 식의 겸손 포장", "약점을 장점으로 포장 (성실함이 약점 등)", "추상적 단어만 나열"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="팀에서 갈등이 생겼을 때 어떻게 해결하셨나요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=5,
        answer_points=["갈등 원인 명확히 파악", "상대방 입장 경청 강조", "해결 과정과 결과 구체화"],
        anti_patterns=["'갈등이 없었습니다'", "상대방 잘못만 부각", "결과 없이 과정만 설명"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="가장 어려웠던 프로젝트와 어떻게 극복했는지 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=5,
        answer_points=["어려움의 구체적 원인 설명", "본인의 역할과 기여 명확히", "정량적 결과 포함"],
        anti_patterns=["어려움을 외부 요인으로만 귀인", "본인 기여 불명확", "결과 없이 고생담만"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="5년 후 어떤 모습이 되고 싶으신가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=5,
        answer_points=["직무 성장 방향과 연계", "회사의 성장 궤도와 연결", "구체적 역량 목표 포함"],
        anti_patterns=["'모르겠습니다'", "다른 회사/직무 언급", "지나치게 높은 직책 목표만"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="실패한 경험과 그로부터 배운 점을 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=5,
        answer_points=["실패를 솔직하게 인정", "본인 책임 부분 명확히", "배운 점을 이후 적용한 사례"],
        anti_patterns=["실패를 남 탓으로", "사소한 실패만 언급", "배운 점만 있고 실제 적용 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="지원 동기를 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=5,
        answer_points=["회사 미션/제품에 대한 진정성", "본인 커리어 방향과 연계", "구체적 조사 내용 언급"],
        anti_patterns=["'연봉이 높아서'", "홈페이지 복사 수준의 회사 설명", "모든 회사에 쓸 수 있는 답변"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="협업에서 가장 중요하게 생각하는 것은 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=4,
        answer_points=["명확한 커뮤니케이션 강조", "사례로 구체화", "팀 목표 우선 언급"],
        anti_patterns=["추상적 단어만 (소통, 배려)", "본인 중심적 사고", "사례 없음"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="본인만의 스트레스 관리 방법은 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=3,
        answer_points=["건강한 방법 제시", "업무 효율과 연결", "실제 활용 사례"],
        anti_patterns=["'스트레스를 안 받아요'", "지나치게 개인적 취미만", "업무 연관성 없음"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="리더십을 발휘한 경험을 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=4,
        answer_points=["팀원 동기부여 방식 구체화", "의사결정 과정 설명", "성과 정량화"],
        anti_patterns=["공식 직책 없으면 경험 없다고 함", "독단적 리더십", "팀 성과를 본인 공으로만"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="빠르게 새로운 기술/환경에 적응한 경험을 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=4,
        answer_points=["학습 방법론 구체화", "적응 기간과 성과", "주도적 학습 강조"],
        anti_patterns=["추상적 '열심히 했어요'", "적응 결과 없음", "강요에 의한 적응으로 표현"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="우선순위가 충돌할 때 어떻게 결정하나요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=4,
        answer_points=["기준 명확히 (임팩트, 긴급성, 중요도)", "이해관계자와 소통", "사례로 구체화"],
        anti_patterns=["'상사가 시키는 대로'", "기준 없이 감으로", "결과 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="본인이 틀렸다는 것을 깨달았을 때 어떻게 행동하셨나요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=3,
        answer_points=["빠른 인정과 수정", "팀에 미친 영향 최소화 방법", "재발 방지 조치"],
        anti_patterns=["틀린 경험이 없다고 함", "인정하지 않고 이유 설명만", "남 탓"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="피드백을 받았을 때 어떻게 반응하고 적용하셨나요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=4,
        answer_points=["수용적 자세 강조", "구체적 개선 행동", "이후 변화 결과"],
        anti_patterns=["방어적 반응", "피드백을 무시했던 경험 없다고", "추상적 수용만"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="혼자 일하는 것과 팀으로 일하는 것 중 어느 것을 더 선호하나요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=3,
        answer_points=["상황에 따른 유연성 강조", "각각의 장점 균형 있게 언급", "팀 협업 가치 존중"],
        anti_patterns=["한쪽만 극단적으로 선호", "지원하는 직무 성격과 맞지 않는 답변"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="본인이 가장 자랑스럽게 생각하는 성과는 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=4,
        answer_points=["정량적 성과 포함", "본인 기여도 명확히", "팀/회사에 미친 임팩트"],
        anti_patterns=["학창시절 수상 등 너무 오래된 사례", "본인 기여 불명확", "수치 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="직장 생활에서 가장 중요하게 생각하는 가치는 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=3,
        answer_points=["회사 문화와 연계", "구체적 사례로 뒷받침", "직무 관련성"],
        anti_patterns=["'돈'이나 '워라밸'만 언급", "모든 가치를 다 나열", "사례 없음"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="현 직장/이전 직장을 떠나는/떠난 이유는 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=2, frequency=5,
        answer_points=["성장 기회 중심으로 긍정적 프레이밍", "이전 회사 비방 절대 금지", "지원 회사와의 연결"],
        anti_patterns=["상사/동료 비방", "연봉만 언급", "부정적 경험만 나열"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="본인을 한 단어(또는 한 문장)로 표현한다면?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=3,
        answer_points=["직무 관련 키워드 활용", "사례로 뒷받침 가능한 단어", "기억에 남는 표현"],
        anti_patterns=["너무 평범한 단어 (성실, 열정)", "검증 불가능한 추상어", "회사가 원하는 것과 무관"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="최근에 읽은 책이나 학습한 내용을 말씀해 주세요.",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=3,
        answer_points=["직무 연관성", "실제 적용 방법", "지속적 학습 자세 어필"],
        anti_patterns=["'최근에 책을 안 읽었어요'", "내용 설명만 하고 적용 없음", "너무 오래된 책"],
        star_applicable=False,
    ),
    InterviewQuestion(
        question="이 직무에 지원하게 된 구체적인 계기는 무엇인가요?",
        category=QuestionCategory.PERSONALITY,
        difficulty=1, frequency=4,
        answer_points=["진정성 있는 스토리", "커리어 방향과 일관성", "회사/직무 조사 결과 반영"],
        anti_patterns=["'우연히 공고를 봤어요'", "모든 회사에 쓸 수 있는 답변", "직무 이해 부족"],
        star_applicable=False,
    ),

    # -----------------------------------------------------------------------
    # 기술 공통 (30개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="시간복잡도 O(n log n)과 O(n²)의 차이를 실제 데이터 크기로 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["n=1000일 때 연산 수 비교", "정렬 알고리즘 예시", "실무 선택 기준"],
        anti_patterns=["공식만 암기하고 의미 모름", "실무 적용 설명 없음"],
    ),
    InterviewQuestion(
        question="해시 테이블의 충돌(collision) 해결 방법을 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["체이닝(Chaining) vs 오픈 어드레싱", "실제 언어별 구현 방식", "성능 트레이드오프"],
        anti_patterns=["한 가지 방법만 알고 있음", "구현 불가"],
    ),
    InterviewQuestion(
        question="트리와 그래프의 차이점과 각각의 적용 사례를 말씀해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["순환(cycle) 유무 차이", "파일시스템 vs SNS 팔로우 관계 예시", "탐색 알고리즘(BFS/DFS)"],
        anti_patterns=["정의만 암기", "실무 사례 없음"],
    ),
    InterviewQuestion(
        question="동적 프로그래밍(DP)은 언제 사용하고, 메모이제이션과의 차이는 무엇인가요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=3,
        answer_points=["최적 부분 구조 + 중복 부분 문제", "top-down vs bottom-up", "실제 문제 예시 (피보나치, 배낭)"],
        anti_patterns=["개념만 설명하고 코드/예시 없음"],
    ),
    InterviewQuestion(
        question="프로세스와 스레드의 차이를 메모리 관점에서 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["메모리 공간(코드/데이터/힙/스택) 구분", "컨텍스트 스위칭 비용", "멀티프로세스 vs 멀티스레드 선택 기준"],
        anti_patterns=["단순 정의만", "컨텍스트 스위칭 설명 못함"],
    ),
    InterviewQuestion(
        question="교착상태(Deadlock)의 발생 조건과 해결 방법을 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=3,
        answer_points=["4가지 필요 조건 (상호배제, 점유대기, 비선점, 환형대기)", "예방/회피/탐지/복구 전략", "실무 예시"],
        anti_patterns=["조건 1-2개만 알고 있음", "해결책 없음"],
    ),
    InterviewQuestion(
        question="REST API 설계 원칙을 설명하고 좋은 API와 나쁜 API의 차이를 예시로 보여주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=5,
        answer_points=["자원 중심 URL 설계", "HTTP 메서드 올바른 사용", "상태 코드 의미", "버전 관리"],
        anti_patterns=["GET /getUser 같은 동사형 URL", "모든 것을 POST로", "상태 코드 무시"],
    ),
    InterviewQuestion(
        question="TCP와 UDP의 차이점과 각각 어떤 상황에서 사용하나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["신뢰성 vs 속도 트레이드오프", "3-way handshake 설명", "스트리밍/게임 vs 파일전송 예시"],
        anti_patterns=["정의만 암기", "실무 사례 없음"],
    ),
    InterviewQuestion(
        question="HTTP와 HTTPS의 차이, TLS 핸드셰이크 과정을 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["대칭키 vs 비대칭키", "인증서 검증 과정", "성능 영향과 최적화"],
        anti_patterns=["'암호화한다'만 설명", "핸드셰이크 모름"],
    ),
    InterviewQuestion(
        question="인덱스(Index)가 무엇이고, 언제 사용하면 안 되나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=5,
        answer_points=["B-Tree 구조 기본 설명", "읽기 성능 vs 쓰기 성능 트레이드오프", "카디널리티가 낮을 때 비효율"],
        anti_patterns=["'빠르게 검색한다'만", "단점 모름", "복합 인덱스 설명 못함"],
    ),
    InterviewQuestion(
        question="N+1 문제가 무엇이고 어떻게 해결하나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=5,
        answer_points=["ORM에서 발생하는 쿼리 문제 설명", "Eager Loading, JOIN, 배치 로딩", "실제 경험 사례"],
        anti_patterns=["개념만 설명하고 해결책 없음", "경험 없음"],
    ),
    InterviewQuestion(
        question="트랜잭션의 ACID 속성을 설명하고, 각 속성이 위반될 때 어떤 문제가 생기나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["Atomicity/Consistency/Isolation/Durability 각각 설명", "격리 수준별 문제 (dirty read 등)", "실무 격리 수준 선택"],
        anti_patterns=["약자만 암기하고 의미 모름"],
    ),
    InterviewQuestion(
        question="캐시(Cache)를 설계할 때 고려할 사항을 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["TTL 설정", "Cache Invalidation 전략", "Cache-aside vs Write-through vs Write-behind", "캐시 스탬피드 문제"],
        anti_patterns=["'Redis 쓰면 됩니다'만", "무효화 전략 없음"],
    ),
    InterviewQuestion(
        question="메시지 큐(Message Queue)를 왜 사용하고, 어떤 문제를 해결하나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["비동기 처리와 디커플링", "트래픽 버퍼링", "신뢰성 보장", "Kafka vs RabbitMQ 차이"],
        anti_patterns=["사용 경험만 나열하고 이유 설명 못함"],
    ),
    InterviewQuestion(
        question="OAuth 2.0 인증 흐름을 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["Authorization Code Flow 상세", "Access Token vs Refresh Token", "보안 고려사항 (PKCE 등)"],
        anti_patterns=["'소셜 로그인'만 언급", "토큰 종류 구분 못함"],
    ),
    InterviewQuestion(
        question="마이크로서비스와 모놀리식 아키텍처의 장단점을 비교해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=4,
        answer_points=["팀 규모와 복잡도 기반 선택 기준", "데이터 일관성 도전", "운영 오버헤드 vs 독립 배포"],
        anti_patterns=["마이크로서비스가 무조건 좋다", "팀 규모 고려 없음"],
    ),
    InterviewQuestion(
        question="코드 리뷰에서 중요하게 보는 것이 무엇인가요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=1, frequency=4,
        answer_points=["가독성/유지보수성", "버그 가능성", "성능 영향", "테스트 커버리지"],
        anti_patterns=["스타일만 지적", "긍정적 피드백 없음", "코드 전체 재작성 요구"],
    ),
    InterviewQuestion(
        question="테스트를 어떻게 작성하시나요? 단위/통합/E2E 테스트의 비율은?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["테스트 피라미드 개념", "각 테스트 목적과 비용", "실제 경험 비율과 이유"],
        anti_patterns=["테스트를 안 쓴다", "E2E만 작성", "모킹 남용"],
    ),
    InterviewQuestion(
        question="Git 브랜치 전략(Git Flow, GitHub Flow 등)을 설명하고 어떤 것을 선호하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=1, frequency=3,
        answer_points=["각 전략의 특징 설명", "팀 규모/배포 주기에 따른 선택", "실제 사용 경험"],
        anti_patterns=["이름만 알고 내용 모름", "무조건 Git Flow"],
    ),
    InterviewQuestion(
        question="객체지향 설계 원칙(SOLID)을 실제 코드 예시와 함께 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=3,
        answer_points=["5원칙 각각 실제 위반 예시", "리팩토링 방향", "DIP와 의존성 주입 연결"],
        anti_patterns=["약자만 암기", "예시 없이 설명만"],
    ),
    InterviewQuestion(
        question="디자인 패턴 중 실무에서 가장 많이 사용한 패턴과 이유를 설명해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["패턴 선택 이유 (문제 → 솔루션)", "구체적 코드/사례", "남용 사례도 언급"],
        anti_patterns=["Singleton만 안다", "예시 없음", "패턴 목록만 나열"],
    ),
    InterviewQuestion(
        question="대용량 트래픽을 처리하기 위해 어떤 전략을 사용하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=4,
        answer_points=["수평 확장 vs 수직 확장", "로드 밸런싱", "캐싱 계층", "DB 샤딩/레플리케이션"],
        anti_patterns=["'서버 늘리면 됩니다'만", "병목 지점 분석 없음"],
    ),
    InterviewQuestion(
        question="동시성 문제(Race Condition)를 경험한 적 있나요? 어떻게 해결했나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=3, frequency=3,
        answer_points=["문제 발생 상황 설명", "락(Lock), 원자적 연산, 낙관적/비관적 잠금", "해결 결과"],
        anti_patterns=["경험 없다고만", "해결책 없이 문제만 설명"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="성능 프로파일링을 어떻게 하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["병목 지점 측정 방법", "사용 도구 (pprof, perf, Chrome DevTools 등)", "개선 전후 지표"],
        anti_patterns=["'느리면 코드 보면 됩니다'", "도구 모름"],
    ),
    InterviewQuestion(
        question="보안에서 SQL Injection과 XSS를 설명하고 방어 방법을 말씀해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=4,
        answer_points=["공격 원리 설명", "Prepared Statement, CSP 헤더", "OWASP Top 10 언급"],
        anti_patterns=["원리 모르고 방어법만", "방어법 1개만 알고 있음"],
    ),
    InterviewQuestion(
        question="코드를 작성할 때 가독성을 높이기 위해 어떤 노력을 하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=1, frequency=3,
        answer_points=["네이밍 컨벤션", "함수 길이/책임 분리", "주석 vs 자기 문서화 코드"],
        anti_patterns=["'변수명 잘 짓는다'만", "구체적 기준 없음"],
    ),
    InterviewQuestion(
        question="기술 부채(Technical Debt)를 어떻게 관리하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["부채 식별 방법", "비즈니스 우선순위와 균형", "리팩토링 전략 (보이스카우트 원칙 등)"],
        anti_patterns=["'리팩토링 할 시간이 없어요'만", "무조건 완벽한 코드 주장"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="API 버전 관리는 어떻게 하시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["URL vs 헤더 버전 방식", "하위 호환성 유지 전략", "Deprecation 정책"],
        anti_patterns=["버전 관리를 안 함", "하위 호환성 고려 없음"],
    ),
    InterviewQuestion(
        question="모니터링과 로깅에서 어떤 지표를 중요하게 보시나요?",
        category=QuestionCategory.TECH_COMMON,
        difficulty=2, frequency=3,
        answer_points=["RED(Rate/Error/Duration) 또는 USE 메트릭", "구조화 로그", "알람 임계값 설정"],
        anti_patterns=["'로그 찍으면 됩니다'만", "지표 없음"],
    ),
    InterviewQuestion(
        question="최근 관심 있는 기술 트렌드와 그 이유를 말씀해 주세요.",
        category=QuestionCategory.TECH_COMMON,
        difficulty=1, frequency=4,
        answer_points=["업무 관련성 연결", "실제 학습/적용 경험", "비판적 시각도 포함"],
        anti_patterns=["유행어만 나열", "학습 없이 관심만", "회사 기술 스택 무관"],
    ),

    # -----------------------------------------------------------------------
    # 프론트엔드 (20개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="브라우저의 렌더링 과정을 Critical Rendering Path 관점에서 설명해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=5,
        answer_points=["DOM/CSSOM → Render Tree → Layout → Paint → Composite", "렌더 블로킹 리소스", "FCP/LCP 최적화"],
        anti_patterns=["'HTML 파싱한다'만", "성능 최적화 연결 못함"],
    ),
    InterviewQuestion(
        question="React의 가상 DOM(Virtual DOM)이 실제 성능을 어떻게 향상시키나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=5,
        answer_points=["Diffing 알고리즘", "배치 업데이트", "실제 DOM 조작 최소화", "React Fiber 언급"],
        anti_patterns=["'빠르다'만", "실제 조작 비용 설명 못함", "React 18 변경사항 모름"],
    ),
    InterviewQuestion(
        question="React의 useCallback과 useMemo의 차이와 올바른 사용 시점은?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["함수 메모이제이션 vs 값 메모이제이션", "의존성 배열의 의미", "남용 시 오히려 성능 저하"],
        anti_patterns=["무조건 사용", "차이 설명 못함", "의존성 배열 빈 배열로 고정"],
    ),
    InterviewQuestion(
        question="CSS Flexbox와 Grid의 차이를 언제 어떤 것을 선택해야 하는지 설명해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=1, frequency=4,
        answer_points=["1차원 vs 2차원 레이아웃", "실제 사용 사례 비교", "브라우저 지원 현황"],
        anti_patterns=["하나만 사용", "차이 설명 못함"],
    ),
    InterviewQuestion(
        question="웹 접근성(Web Accessibility, a11y)을 위해 어떤 노력을 하시나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["ARIA 속성 활용", "키보드 네비게이션", "색상 대비 기준", "스크린리더 테스트"],
        anti_patterns=["'잘 모릅니다'", "ARIA만 언급"],
    ),
    InterviewQuestion(
        question="상태 관리 라이브러리(Redux, Zustand, Recoil 등)의 선택 기준은 무엇인가요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["프로젝트 규모와 복잡도", "팀 학습 곡선", "각 도구의 장단점 비교"],
        anti_patterns=["무조건 Redux", "선택 기준 없이 사용해봤다만"],
    ),
    InterviewQuestion(
        question="React의 렌더링 최적화 방법을 말씀해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["React.memo, useMemo, useCallback", "코드 스플리팅 (lazy/Suspense)", "리스트 가상화 (react-virtual 등)"],
        anti_patterns=["이론만 알고 실제 적용 경험 없음", "한 가지 방법만"],
    ),
    InterviewQuestion(
        question="CSR, SSR, SSG, ISR의 차이와 각각의 적합한 사용 사례는?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["SEO/초기 로딩/서버 비용 트레이드오프", "Next.js 구현 방식", "사용 사례 매핑"],
        anti_patterns=["이름만 알고 차이 설명 못함", "모든 상황에 SSR 추천"],
    ),
    InterviewQuestion(
        question="웹 성능 지표(Core Web Vitals)를 설명하고 개선 경험을 말씀해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["LCP/FID/CLS 정의와 임계값", "측정 도구 (Lighthouse, WebPageTest)", "실제 개선 사례와 수치"],
        anti_patterns=["지표 이름만 알고 의미 모름", "개선 경험 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="JavaScript의 이벤트 루프(Event Loop)를 설명해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=5,
        answer_points=["Call Stack, Web APIs, Callback Queue, Microtask Queue", "Promise vs setTimeout 실행 순서", "블로킹 코드의 영향"],
        anti_patterns=["단순 '비동기 처리'만", "Microtask/Macrotask 구분 못함"],
    ),
    InterviewQuestion(
        question="TypeScript를 사용하는 이유와 실무에서 어떻게 활용하시나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=1, frequency=4,
        answer_points=["타입 안정성과 개발 경험", "any 타입 남용 주의", "고급 타입 활용 (Generic, Utility Types)"],
        anti_patterns=["'type 쓰면 됩니다'만", "any 남용", "장점만 나열"],
    ),
    InterviewQuestion(
        question="번들 사이즈를 줄이기 위해 어떤 최적화를 하셨나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["Tree Shaking", "Code Splitting", "이미지 최적화 (WebP, lazy loading)", "번들 분석 도구 사용"],
        anti_patterns=["'webpack 설정했어요'만", "수치 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="크로스 브라우저 호환성 문제를 어떻게 처리하시나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=1, frequency=3,
        answer_points=["Can I Use 확인 습관", "Polyfill vs Transpiling", "BrowserStack 등 테스트 도구"],
        anti_patterns=["'Chrome만 지원합니다'", "해결 방법 없음"],
    ),
    InterviewQuestion(
        question="CSS-in-JS와 CSS Modules, Tailwind CSS의 장단점을 비교해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["런타임 비용 vs 개발 경험", "팀 컨벤션과 학습 곡선", "빌드 타임 추출 옵션"],
        anti_patterns=["무조건 Tailwind", "성능 차이 모름"],
    ),
    InterviewQuestion(
        question="React Context API와 전역 상태 관리 라이브러리의 차이는 무엇인가요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["리렌더링 범위 차이", "Context 남용 시 성능 문제", "적절한 사용 범위"],
        anti_patterns=["Context가 Redux 대체라고만", "리렌더링 문제 모름"],
    ),
    InterviewQuestion(
        question="SPA에서 SEO를 개선하는 방법을 설명해 주세요.",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["SSR/SSG 전환", "Dynamic Rendering", "메타 태그/OpenGraph 관리"],
        anti_patterns=["'SPA는 SEO 안 됩니다'만", "해결책 제시 없음"],
    ),
    InterviewQuestion(
        question="Debounce와 Throttle의 차이와 각각 어떤 상황에서 사용하나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=4,
        answer_points=["실행 타이밍 차이 명확히", "검색 자동완성 vs 스크롤 이벤트 예시", "직접 구현 가능 여부"],
        anti_patterns=["차이 설명 못함", "라이브러리만 사용"],
    ),
    InterviewQuestion(
        question="웹 보안에서 CSRF와 XSS를 프론트엔드 관점에서 방어하는 방법은?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["SameSite Cookie, CSRF Token", "CSP 헤더", "innerHTML 사용 금지"],
        anti_patterns=["백엔드 책임이라고만", "한 가지 방어법만"],
    ),
    InterviewQuestion(
        question="React에서 커스텀 훅(Custom Hook)을 언제 만들어야 하나요?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["로직 재사용 기준", "관심사 분리", "테스트 용이성 향상"],
        anti_patterns=["모든 로직을 훅으로", "컴포넌트 내 로직과 차이 모름"],
    ),
    InterviewQuestion(
        question="웹 소켓(WebSocket)과 Server-Sent Events(SSE)의 차이와 적용 사례는?",
        category=QuestionCategory.FRONTEND,
        difficulty=2, frequency=3,
        answer_points=["양방향 vs 단방향", "채팅 vs 실시간 대시보드", "HTTP/2와의 관계"],
        anti_patterns=["WebSocket만 알고 있음", "사용 사례 구분 못함"],
    ),

    # -----------------------------------------------------------------------
    # 백엔드 (20개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="동기와 비동기 처리의 차이를 실제 서버 구현 관점에서 설명해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=4,
        answer_points=["I/O 블로킹 vs 논블로킹", "이벤트 루프 vs 스레드 풀", "실무 선택 기준"],
        anti_patterns=["'비동기가 빠르다'만", "실제 구현 설명 못함"],
    ),
    InterviewQuestion(
        question="RESTful API vs GraphQL vs gRPC의 차이와 각각의 사용 사례를 설명해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=3, frequency=4,
        answer_points=["Over-fetching/Under-fetching 문제", "타입 안정성", "스트리밍과 성능"],
        anti_patterns=["GraphQL이 무조건 좋다", "차이 설명 못함"],
    ),
    InterviewQuestion(
        question="데이터베이스 샤딩(Sharding)을 어떤 기준으로 하고, 어떤 문제가 발생할 수 있나요?",
        category=QuestionCategory.BACKEND,
        difficulty=3, frequency=3,
        answer_points=["샤딩 키 선택 기준", "핫스팟 문제", "크로스 샤드 쿼리/트랜잭션 한계"],
        anti_patterns=["'분산하면 됩니다'만", "문제점 모름"],
    ),
    InterviewQuestion(
        question="읽기/쓰기 분리(Read Replica)를 구현할 때 고려할 사항은 무엇인가요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["복제 지연(Replication Lag)", "읽기 일관성 수준 결정", "장애 시 페일오버"],
        anti_patterns=["'성능 좋아진다'만", "복제 지연 고려 없음"],
    ),
    InterviewQuestion(
        question="분산 트랜잭션을 어떻게 구현하시나요? (2PC, Saga 패턴 등)",
        category=QuestionCategory.BACKEND,
        difficulty=3, frequency=3,
        answer_points=["2PC의 블로킹 문제", "Saga의 보상 트랜잭션", "이벤트 소싱과 연계"],
        anti_patterns=["분산 트랜잭션을 모름", "단일 트랜잭션으로 해결 주장"],
    ),
    InterviewQuestion(
        question="Rate Limiting을 어떻게 구현하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=4,
        answer_points=["토큰 버킷, 슬라이딩 윈도우 알고리즘", "분산 환경에서 Redis 활용", "사용자/IP/API별 분리"],
        anti_patterns=["'Nginx 설정하면 됩니다'만", "분산 환경 고려 없음"],
    ),
    InterviewQuestion(
        question="서버리스(Serverless) 아키텍처의 장단점과 적합한 사용 사례는?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["콜드 스타트 문제", "비용 모델", "상태 관리 한계", "이벤트 드리븐 적합 케이스"],
        anti_patterns=["'무조건 싸다'", "콜드 스타트 모름"],
    ),
    InterviewQuestion(
        question="API Gateway의 역할과 직접 구현한 경험을 말씀해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["인증/인가, 라우팅, 로드밸런싱", "Rate Limiting, 캐싱", "Circuit Breaker 연계"],
        anti_patterns=["'AWS API Gateway 씁니다'만", "역할 설명 못함"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="이벤트 소싱(Event Sourcing)과 CQRS 패턴을 설명해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=3, frequency=2,
        answer_points=["상태 대신 이벤트 저장", "읽기/쓰기 모델 분리", "최종 일관성 수용"],
        anti_patterns=["이름만 알고 구현 못함", "모든 상황에 적용 주장"],
    ),
    InterviewQuestion(
        question="백그라운드 작업(Background Job)을 어떻게 처리하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["큐 기반 작업 처리 (Celery, Bull 등)", "재시도와 멱등성", "데드레터 큐(DLQ)"],
        anti_patterns=["Thread로만 처리", "실패 처리 없음"],
    ),
    InterviewQuestion(
        question="HTTP 캐시(ETag, Last-Modified, Cache-Control)를 어떻게 활용하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["각 헤더의 역할과 우선순위", "Conditional Request 흐름", "CDN과 연계"],
        anti_patterns=["서버 캐시만 알고 있음", "헤더 구분 못함"],
    ),
    InterviewQuestion(
        question="서킷 브레이커(Circuit Breaker) 패턴이 무엇이고 어떻게 구현하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["Closed/Open/Half-Open 상태", "장애 전파 방지", "Hystrix, Resilience4j 등 도구"],
        anti_patterns=["개념만 알고 구현 경험 없음"],
    ),
    InterviewQuestion(
        question="멱등성(Idempotency)이 중요한 이유와 API 설계 시 어떻게 보장하나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["재시도 안전성", "Idempotency-Key 헤더", "PUT vs PATCH 차이"],
        anti_patterns=["멱등성 개념 모름", "POST 요청 멱등성 처리 방법 모름"],
    ),
    InterviewQuestion(
        question="데이터베이스 정규화와 비정규화의 트레이드오프를 설명해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["1NF/2NF/3NF 기본 설명", "읽기 성능 vs 데이터 무결성", "실무에서 비정규화 적용 사례"],
        anti_patterns=["항상 정규화가 맞다", "비정규화 장점 모름"],
    ),
    InterviewQuestion(
        question="API 설계 시 페이지네이션 방법을 비교해 주세요. (Offset vs Cursor)",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=4,
        answer_points=["Offset의 성능 저하와 데이터 일관성 문제", "Cursor 기반의 장점과 단점", "실시간 데이터에서의 선택"],
        anti_patterns=["Offset만 알고 있음", "대용량 데이터 문제 모름"],
    ),
    InterviewQuestion(
        question="웹훅(Webhook)과 폴링(Polling)의 차이와 각각의 적합한 상황은?",
        category=QuestionCategory.BACKEND,
        difficulty=1, frequency=3,
        answer_points=["서버 푸시 vs 클라이언트 풀", "웹훅 신뢰성 보장 방법", "Long Polling 언급"],
        anti_patterns=["차이 설명 못함", "웹훅 재시도 처리 없음"],
    ),
    InterviewQuestion(
        question="로그 집중화(Centralized Logging)를 어떻게 구현하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["ELK Stack, Loki+Grafana 등 도구", "구조화 로그 (JSON)", "Correlation ID로 트레이싱"],
        anti_patterns=["'로그 파일 보면 됩니다'만", "분산 환경 고려 없음"],
    ),
    InterviewQuestion(
        question="JWT의 장단점과 세션 기반 인증과의 차이를 설명해 주세요.",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=4,
        answer_points=["Stateless vs Stateful", "JWT 무효화 문제", "토큰 크기와 전송 비용"],
        anti_patterns=["JWT가 무조건 좋다", "무효화 문제 모름"],
    ),
    InterviewQuestion(
        question="데이터베이스 커넥션 풀(Connection Pool)의 적절한 크기를 어떻게 결정하나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["CPU 코어 수 기반 공식", "I/O 대기 시간 고려", "모니터링 지표로 튜닝"],
        anti_patterns=["무조건 크게 설정", "기준 없이 감으로"],
    ),
    InterviewQuestion(
        question="분산 환경에서 유일한 ID(Unique ID)를 어떻게 생성하시나요?",
        category=QuestionCategory.BACKEND,
        difficulty=2, frequency=3,
        answer_points=["UUID v4 vs Snowflake ID vs ULID", "정렬 가능성", "충돌 가능성과 성능"],
        anti_patterns=["DB Auto-Increment만", "분산 환경 고려 없음"],
    ),

    # -----------------------------------------------------------------------
    # DevOps (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="CI/CD 파이프라인을 어떻게 설계하시나요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=5,
        answer_points=["빌드 → 테스트 → 보안스캔 → 배포 단계", "환경별 배포 전략", "롤백 방법"],
        anti_patterns=["도구 이름만 나열", "롤백 계획 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="블루/그린 배포와 카나리 배포의 차이와 적합한 사용 사례는?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=4,
        answer_points=["다운타임 없는 배포 vs 점진적 트래픽 이동", "리스크와 비용 트레이드오프", "실제 사용 도구"],
        anti_patterns=["차이 설명 못함", "무조건 카나리가 좋다"],
    ),
    InterviewQuestion(
        question="쿠버네티스(Kubernetes)에서 Pod, Deployment, Service의 역할을 설명해 주세요.",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=4,
        answer_points=["컨테이너 추상화 계층", "레플리카셋과 자동 복구", "서비스 디스커버리"],
        anti_patterns=["이름만 알고 역할 구분 못함"],
    ),
    InterviewQuestion(
        question="도커(Docker) 이미지 크기를 줄이는 방법을 설명해 주세요.",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["멀티 스테이지 빌드", "Alpine 베이스 이미지", "불필요한 레이어 최소화"],
        anti_patterns=["'작은 이미지 쓰면 됩니다'만", "멀티 스테이지 모름"],
    ),
    InterviewQuestion(
        question="인프라를 코드로 관리(IaC)하는 이유와 사용 도구를 설명해 주세요.",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["재현 가능성과 버전 관리", "Terraform vs Pulumi vs CloudFormation", "드리프트 감지"],
        anti_patterns=["'콘솔에서 설정합니다'만", "IaC 이유 설명 못함"],
    ),
    InterviewQuestion(
        question="장애(Incident) 발생 시 어떻게 대응하고 사후 처리를 하시나요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=4,
        answer_points=["탐지 → 격리 → 복구 순서", "커뮤니케이션 체계", "포스트모템과 재발 방지"],
        anti_patterns=["복구만 하고 사후 분석 없음", "비난 문화"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="SLO/SLA/SLI의 차이를 설명하고 실제 설정 경험을 말씀해 주세요.",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["SLI가 측정 지표, SLO가 목표, SLA가 계약", "에러 버짓 개념", "실제 가용성 계산"],
        anti_patterns=["약자만 알고 내용 모름", "경험 없음"],
    ),
    InterviewQuestion(
        question="컨테이너 보안을 위해 어떤 조치를 취하시나요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["루트리스 컨테이너", "이미지 취약점 스캔 (Trivy 등)", "네트워크 정책"],
        anti_patterns=["'방화벽 쓰면 됩니다'만", "이미지 스캔 없음"],
    ),
    InterviewQuestion(
        question="Helm Chart를 사용하는 이유와 장단점은 무엇인가요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["쿠버네티스 패키지 관리", "템플릿 재사용", "버전 관리와 롤백"],
        anti_patterns=["'YAML이 복잡해서'만", "장단점 균형 없음"],
    ),
    InterviewQuestion(
        question="GitOps가 무엇이고 기존 CI/CD와의 차이는?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["Git이 단일 진실 소스", "Pull 방식 배포 (ArgoCD, Flux)", "드리프트 자동 감지"],
        anti_patterns=["GitOps를 모름", "Git에 코드만 관리한다고 이해"],
    ),
    InterviewQuestion(
        question="오토스케일링(Auto Scaling)을 설정할 때 고려할 사항은?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["스케일 인/아웃 트리거 지표", "Warm-up 시간", "스테이트풀 서비스의 한계"],
        anti_patterns=["'CPU 80% 이상이면 스케일'만", "스테이트풀 서비스 고려 없음"],
    ),
    InterviewQuestion(
        question="로드 밸런서의 알고리즘 종류와 각각의 적합한 상황은?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["Round Robin, Least Connections, IP Hash", "세션 지속성 요구사항", "헬스 체크"],
        anti_patterns=["Round Robin만 알고 있음", "세션 문제 모름"],
    ),
    InterviewQuestion(
        question="프로메테우스(Prometheus)와 그라파나(Grafana)를 어떻게 활용하시나요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["Pull 방식 메트릭 수집", "PromQL 기본 쿼리", "알람 규칙 설정"],
        anti_patterns=["'설치해봤어요'만", "쿼리 작성 경험 없음"],
    ),
    InterviewQuestion(
        question="비용 최적화를 위해 클라우드 리소스를 어떻게 관리하시나요?",
        category=QuestionCategory.DEVOPS,
        difficulty=2, frequency=3,
        answer_points=["리소스 태깅과 비용 추적", "예약 인스턴스/Spot 인스턴스 활용", "사용하지 않는 리소스 정리"],
        anti_patterns=["비용 최적화 고려 없음", "개발 환경 상시 가동"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="서비스 메시(Service Mesh, Istio 등)를 사용하는 이유와 오버헤드는?",
        category=QuestionCategory.DEVOPS,
        difficulty=3, frequency=2,
        answer_points=["사이드카 프록시 패턴", "mTLS, 트래픽 관리", "운영 복잡도 증가"],
        anti_patterns=["이름만 알고 내용 모름", "무조건 좋다"],
    ),

    # -----------------------------------------------------------------------
    # 데이터 (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="GROUP BY와 HAVING, WHERE의 차이를 설명해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=1, frequency=5,
        answer_points=["WHERE는 집계 전, HAVING은 집계 후 필터", "실행 순서 설명", "인덱스 활용 차이"],
        anti_patterns=["WHERE와 HAVING 혼동", "실행 순서 모름"],
    ),
    InterviewQuestion(
        question="윈도우 함수(Window Function)를 사용한 경험을 말씀해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=4,
        answer_points=["ROW_NUMBER, RANK, LAG/LEAD 활용", "PARTITION BY 설명", "집계 함수와의 차이"],
        anti_patterns=["서브쿼리로만 해결", "경험 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="ETL과 ELT의 차이와 각각 적합한 상황을 설명해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["변환 위치(소스 vs 타겟)", "클라우드 데이터 웨어하우스 시대의 ELT 선호", "도구 비교 (dbt 등)"],
        anti_patterns=["차이 설명 못함", "무조건 ETL"],
    ),
    InterviewQuestion(
        question="데이터 파이프라인의 신뢰성을 어떻게 보장하시나요?",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=4,
        answer_points=["데이터 품질 검증", "멱등성 설계", "모니터링과 알람"],
        anti_patterns=["'그냥 실행합니다'", "실패 처리 없음"],
    ),
    InterviewQuestion(
        question="배치 처리와 스트림 처리의 차이와 Lambda/Kappa 아키텍처를 설명해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=3, frequency=3,
        answer_points=["지연시간 vs 처리량 트레이드오프", "Lambda의 복잡도 문제", "Kafka Streams/Flink 언급"],
        anti_patterns=["배치만 알고 있음", "아키텍처 패턴 모름"],
    ),
    InterviewQuestion(
        question="컬럼형(Columnar) 데이터 포맷(Parquet, ORC)이 왜 분석에 유리한가요?",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["컬럼 단위 압축 효율", "분석 쿼리 I/O 최소화", "Predicate Pushdown"],
        anti_patterns=["'빠르다'만", "행(Row) 방식과 비교 못함"],
    ),
    InterviewQuestion(
        question="데이터 카탈로그와 데이터 계보(Lineage)를 왜 관리해야 하나요?",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["데이터 신뢰성과 거버넌스", "장애 추적 효율", "규제 준수 (GDPR 등)"],
        anti_patterns=["'데이터만 있으면 됩니다'", "거버넌스 필요성 모름"],
    ),
    InterviewQuestion(
        question="A/B 테스트를 설계하고 결과를 분석한 경험을 말씀해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=4,
        answer_points=["가설 설정", "샘플 사이즈 계산", "통계적 유의성 (p-value)", "신뢰 구간"],
        anti_patterns=["결과만 보고 유의성 검증 없음", "경험 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="데이터 웨어하우스와 데이터 레이크, 레이크하우스의 차이는?",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["구조화 vs 비구조화 데이터", "스키마 온 라이트 vs 리드", "Delta Lake, Iceberg 언급"],
        anti_patterns=["두 가지만 알고 레이크하우스 모름", "차이 설명 못함"],
    ),
    InterviewQuestion(
        question="머신러닝 모델을 프로덕션에 배포할 때 고려할 사항은 무엇인가요?",
        category=QuestionCategory.DATA,
        difficulty=3, frequency=3,
        answer_points=["모델 버전 관리 (MLflow 등)", "드리프트 모니터링", "A/B 테스트와 Shadow Mode", "서빙 지연시간"],
        anti_patterns=["학습만 알고 배포 고려 없음", "모니터링 없음"],
    ),
    InterviewQuestion(
        question="데이터 파티셔닝 전략을 설명해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["시간 기반 파티셔닝 (일/월)", "쿼리 패턴 기반 선택", "파티션 프루닝 효과"],
        anti_patterns=["파티셔닝 없이 전체 스캔", "파티션 과다 생성"],
    ),
    InterviewQuestion(
        question="SQL 쿼리 성능을 최적화한 경험을 말씀해 주세요.",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=5,
        answer_points=["실행 계획(EXPLAIN) 분석", "인덱스 추가/재설계", "쿼리 리팩토링 결과 수치"],
        anti_patterns=["경험 없음", "결과 수치 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="데이터 품질 문제를 어떻게 탐지하고 처리하시나요?",
        category=QuestionCategory.DATA,
        difficulty=2, frequency=3,
        answer_points=["Great Expectations, dbt test 등 도구", "NULL/중복/범위 검증", "알람과 대응 프로세스"],
        anti_patterns=["'데이터 보면 됩니다'만", "자동화 없음"],
    ),
    InterviewQuestion(
        question="피처 스토어(Feature Store)가 무엇이고 왜 필요한가요?",
        category=QuestionCategory.DATA,
        difficulty=3, frequency=2,
        answer_points=["훈련/서빙 간 피처 일관성", "피처 재사용성", "Feast, Tecton 등 도구"],
        anti_patterns=["'몰라요'", "필요성 설명 못함"],
    ),
    InterviewQuestion(
        question="실시간 데이터 집계를 어떻게 구현하시나요?",
        category=QuestionCategory.DATA,
        difficulty=3, frequency=3,
        answer_points=["Kafka Streams, Flink 등 스트리밍 처리", "집계 창(Window) 전략", "정확성 vs 지연시간"],
        anti_patterns=["배치로만 처리", "정확성 보장 방법 모름"],
    ),

    # -----------------------------------------------------------------------
    # 모바일 (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="iOS와 Android의 앱 생명주기(Lifecycle) 차이를 설명해 주세요.",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=4,
        answer_points=["각 플랫폼 상태 전환 설명", "백그라운드 제한 차이", "리소스 해제 시점"],
        anti_patterns=["한 플랫폼만 알고 있음", "생명주기 콜백 모름"],
    ),
    InterviewQuestion(
        question="앱 성능 최적화를 위해 어떤 방법을 사용하셨나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=4,
        answer_points=["메인 스레드 블로킹 방지", "이미지 캐싱과 지연 로딩", "메모리 누수 탐지 도구"],
        anti_patterns=["'빠른 폰 쓰면 됩니다'", "측정 없이 최적화"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="React Native와 Flutter의 차이와 각각의 장단점은?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["브릿지 vs 네이티브 렌더링", "성능 차이", "생태계와 학습 곡선"],
        anti_patterns=["하나만 알고 있음", "무조건 Flutter가 좋다"],
    ),
    InterviewQuestion(
        question="모바일 앱에서 오프라인 지원을 어떻게 구현하시나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["로컬 데이터베이스 (Room, Core Data)", "동기화 충돌 해결", "낙관적 업데이트"],
        anti_patterns=["오프라인 지원 없음", "충돌 처리 없음"],
    ),
    InterviewQuestion(
        question="앱 보안을 위해 어떤 조치를 취하시나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["루팅/탈옥 탐지", "SSL Pinning", "중요 데이터 암호화 저장"],
        anti_patterns=["'HTTPS 쓰면 됩니다'만", "리버스 엔지니어링 대응 없음"],
    ),
    InterviewQuestion(
        question="푸시 알림(Push Notification) 시스템을 어떻게 구현하셨나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["FCM/APNs 기본 흐름", "토큰 관리", "알림 권한 요청 타이밍"],
        anti_patterns=["라이브러리만 사용하고 원리 모름", "토큰 갱신 처리 없음"],
    ),
    InterviewQuestion(
        question="딥 링크(Deep Link)와 유니버설 링크의 차이를 설명해 주세요.",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["URL Scheme vs Universal Link/App Link", "인증 파일(apple-app-site-association 등)", "폴백 처리"],
        anti_patterns=["URL Scheme만 알고 있음", "보안 차이 모름"],
    ),
    InterviewQuestion(
        question="앱 스토어 최적화(ASO)와 배포 프로세스를 설명해 주세요.",
        category=QuestionCategory.MOBILE,
        difficulty=1, frequency=3,
        answer_points=["키워드 최적화", "심사 기간과 대응", "단계적 출시"],
        anti_patterns=["'올리면 됩니다'만", "심사 거절 대응 방법 모름"],
    ),
    InterviewQuestion(
        question="앱의 크래시율을 어떻게 모니터링하고 개선하셨나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["Firebase Crashlytics, Sentry 등 도구", "크래시 우선순위 결정 기준", "개선 전후 수치"],
        anti_patterns=["크래시 모니터링 없음", "수치 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="메모리 누수(Memory Leak)를 어떻게 탐지하고 해결하시나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["Instruments/Android Profiler 활용", "순환 참조 패턴 (weak 참조)", "해결 사례"],
        anti_patterns=["메모리 누수 경험 없음", "탐지 도구 모름"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="Swift와 Objective-C의 차이, 또는 Kotlin과 Java의 차이를 설명해 주세요.",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=3,
        answer_points=["언어 안정성 (Null safety)", "문법 간결성", "성능 차이", "상호 운용성"],
        anti_patterns=["한쪽만 알고 있음", "차이 설명 못함"],
    ),
    InterviewQuestion(
        question="앱 내 결제(In-App Purchase)를 구현할 때 주의할 점은?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=2,
        answer_points=["영수증 서버사이드 검증", "구독 갱신 처리", "결제 실패 복구"],
        anti_patterns=["클라이언트만 검증", "구독 갱신 처리 없음"],
    ),
    InterviewQuestion(
        question="Flutter의 위젯 트리와 렌더링 파이프라인을 설명해 주세요.",
        category=QuestionCategory.MOBILE,
        difficulty=3, frequency=3,
        answer_points=["Widget/Element/RenderObject 3계층", "Key의 역할", "setState와 리빌드 범위"],
        anti_patterns=["Widget만 알고 나머지 모름", "Key 필요성 모름"],
    ),
    InterviewQuestion(
        question="SwiftUI와 UIKit을 함께 사용할 때 어떻게 통합하시나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=2,
        answer_points=["UIHostingController, UIViewRepresentable", "Coordinator 패턴", "점진적 마이그레이션 전략"],
        anti_patterns=["한 가지만 사용", "통합 방법 모름"],
    ),
    InterviewQuestion(
        question="앱 성능 테스트(Monkey Test, 스트레스 테스트)를 어떻게 수행하시나요?",
        category=QuestionCategory.MOBILE,
        difficulty=2, frequency=2,
        answer_points=["Android Monkey Tool", "다양한 디바이스/OS 버전", "네트워크 조건 시뮬레이션"],
        anti_patterns=["QA에 맡기면 됩니다만", "테스트 계획 없음"],
    ),

    # -----------------------------------------------------------------------
    # 리더십 (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="팀원의 성과가 기대에 미치지 못할 때 어떻게 대화하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=4,
        answer_points=["사실 기반 피드백", "원인 파악 먼저", "개선 계획 함께 수립"],
        anti_patterns=["비공개 불만", "즉각적 징계 언급", "방치"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="기술적 의사결정을 팀원들과 어떻게 하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=4,
        answer_points=["RFC/ADR 프로세스", "반대 의견 수렴 방법", "최종 결정 후 팀 정렬"],
        anti_patterns=["독단적 결정", "결정 없이 계속 토론", "문서화 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="팀의 생산성을 측정하고 개선한 경험을 말씀해 주세요.",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["DORA 메트릭 (배포 빈도, 리드 타임 등)", "병목 지점 파악", "개선 전후 수치"],
        anti_patterns=["'열심히 일했다'만", "수치 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="기술적 로드맵을 어떻게 수립하고 비즈니스 목표와 연계하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=3, frequency=3,
        answer_points=["비즈니스 임팩트 기반 우선순위", "분기별 목표 설정", "이해관계자 커뮤니케이션"],
        anti_patterns=["기술만을 위한 로드맵", "비즈니스 연결 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="주니어 개발자를 어떻게 멘토링하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=1, frequency=4,
        answer_points=["개인별 성장 목표 파악", "코드 리뷰 활용", "점진적 책임 확대"],
        anti_patterns=["'스스로 공부해야 한다'만", "방치", "과도한 간섭"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="이해관계자(비개발자)에게 기술적 내용을 어떻게 설명하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=1, frequency=4,
        answer_points=["비유와 시각화 활용", "비즈니스 임팩트 중심", "기술 용어 최소화"],
        anti_patterns=["기술 용어 그대로 사용", "설명 포기", "지나치게 단순화"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="팀 내 의견 불일치를 해결한 경험을 말씀해 주세요.",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=4,
        answer_points=["각 입장 객관적 정리", "데이터/사례 기반 결정", "결정 후 팀 정렬"],
        anti_patterns=["다수결만으로 해결", "한쪽 편만 들음", "미해결"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="팀 채용에서 어떤 기준으로 평가하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["기술 역량과 문화 적합도 균형", "성장 가능성", "구조화된 평가 기준"],
        anti_patterns=["느낌으로만 판단", "기술만 평가", "다양성 고려 없음"],
    ),
    InterviewQuestion(
        question="스프린트/이터레이션 계획을 어떻게 수립하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["팀 속도(Velocity) 기반", "백로그 우선순위와 연계", "리스크 버퍼 포함"],
        anti_patterns=["위에서 주어진 대로만", "팀 참여 없음"],
    ),
    InterviewQuestion(
        question="기술적 결정의 트레이드오프를 어떻게 문서화하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["ADR(Architecture Decision Record) 형식", "맥락/결정/결과 기록", "미래 팀원을 위한 활용"],
        anti_patterns=["문서화 안 함", "결과만 기록하고 이유 없음"],
    ),
    InterviewQuestion(
        question="원격 팀이나 분산 팀을 어떻게 효과적으로 관리하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["비동기 커뮤니케이션 도구", "타임존 고려 회의 설계", "신뢰 기반 관리"],
        anti_patterns=["실시간 감시", "자율성 없음", "소외 팀원 발생"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="팀이 번아웃 상태일 때 어떻게 대응하셨나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["조기 신호 탐지", "업무량 조정과 이해관계자 소통", "재충전 시간 확보"],
        anti_patterns=["'버텨야 한다'만", "신호 무시", "개인 문제로 방치"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="팀의 기술 역량을 어떻게 향상시키시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["스터디/해커톤 운영", "외부 컨퍼런스 지원", "내부 지식 공유 문화"],
        anti_patterns=["'알아서 공부해야 한다'만", "환경 조성 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="OKR이나 KPI를 어떻게 팀에 적용하시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["팀 목표와 개인 목표 연계", "달성 가능한 목표 설정 기준", "주기적 리뷰"],
        anti_patterns=["위에서 내려온 것만 전달", "측정 불가능한 목표"],
    ),
    InterviewQuestion(
        question="기술 조직의 문화를 어떻게 만들어 가시나요?",
        category=QuestionCategory.LEADERSHIP,
        difficulty=2, frequency=3,
        answer_points=["심리적 안전감 조성", "실험과 학습 장려", "투명한 커뮤니케이션"],
        anti_patterns=["문화는 저절로 형성된다", "실패 처벌 문화", "구체적 사례 없음"],
        star_applicable=True,
    ),

    # -----------------------------------------------------------------------
    # 스타트업 (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="빠른 가설 검증을 위해 MVP를 어떻게 정의하고 만드시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=5,
        answer_points=["핵심 가설 한 가지 집중", "코드 없이 검증 방법", "성공 지표 사전 정의"],
        anti_patterns=["모든 기능 포함", "측정 지표 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="성장(Growth) 지표 중 가장 중요하게 보는 것은 무엇이고 이유는?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=4,
        answer_points=["North Star Metric 개념", "선행/후행 지표 구분", "비즈니스 단계별 다른 지표"],
        anti_patterns=["MAU만 언급", "지표 선택 이유 없음"],
    ),
    InterviewQuestion(
        question="리소스가 제한된 상황에서 기술 결정을 어떻게 하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=4,
        answer_points=["부채 수용과 경계 설정", "'Good Enough' 기준", "리팩토링 타이밍"],
        anti_patterns=["완벽한 설계만 고집", "기술 부채 무한 누적"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="제품-시장 적합성(PMF)을 찾는 과정에서 기술팀의 역할은?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["빠른 실험 환경 구축", "데이터 수집 인프라", "피벗 지원 아키텍처"],
        anti_patterns=["기술팀은 구현만 한다", "PMF 개념 모름"],
    ),
    InterviewQuestion(
        question="스타트업에서 기술 스택을 선택할 때 어떤 기준으로 하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=4,
        answer_points=["팀 역량과 채용 가능성", "생태계와 커뮤니티", "확장성 vs 개발 속도"],
        anti_patterns=["최신 기술 무조건 선택", "팀 역량 고려 없음"],
    ),
    InterviewQuestion(
        question="초기 스타트업에서 엔지니어링 프로세스를 어떻게 구축하셨나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["최소한의 필수 프로세스 우선", "팀 규모에 맞는 도구", "점진적 개선"],
        anti_patterns=["대기업 프로세스 복사", "프로세스 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="고객 피드백을 제품 개발에 어떻게 반영하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=1, frequency=4,
        answer_points=["피드백 수집 채널 다양화", "우선순위 결정 기준", "반영 결과 고객 소통"],
        anti_patterns=["모든 요청 수용", "피드백 무시", "우선순위 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="스타트업에서 온콜(On-call)과 운영 부담을 어떻게 관리하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["알람 노이즈 줄이기", "런북(Runbook) 작성", "로테이션과 보상"],
        anti_patterns=["특정인에게 집중", "런북 없음", "번아웃 방치"],
    ),
    InterviewQuestion(
        question="데이터 기반 의사결정과 직관/경험 기반 의사결정을 어떻게 균형 잡으시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["데이터 없을 때의 가설 설정", "측정 계획 수립", "직관 검증 방법"],
        anti_patterns=["데이터만 맹신", "직관만 따름"],
    ),
    InterviewQuestion(
        question="스타트업에서 경쟁사보다 빠르게 실행하면서 품질을 유지하는 방법은?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=4,
        answer_points=["핵심 품질 기준 설정", "자동화 테스트 최우선", "빠른 롤백 체계"],
        anti_patterns=["품질 완전 포기", "속도만 강조"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="투자자나 이사회에 기술 현황을 어떻게 보고하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=2,
        answer_points=["비즈니스 언어로 번역", "리스크와 마일스톤", "기술 부채 투명 공개"],
        anti_patterns=["기술 용어 그대로", "좋은 것만 보고"],
    ),
    InterviewQuestion(
        question="초기 팀 빌딩 시 기술 채용에서 가장 중요하게 보는 것은?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["불확실성 수용 능력", "제너럴리스트 vs 스페셜리스트", "문화 적합도"],
        anti_patterns=["대기업 출신만 선호", "기술만 평가"],
    ),
    InterviewQuestion(
        question="제품의 방향이 갑자기 바뀔 때 기술 조직을 어떻게 이끄시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["피벗 이유 투명하게 공유", "기존 작업 가치 인정", "새 방향으로 빠른 정렬"],
        anti_patterns=["이유 설명 없이 지시", "팀 사기 저하 방치"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="스타트업에서 기술 부채를 언제 상환하기로 결정하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=2, frequency=3,
        answer_points=["PMF 확인 후 시스템화", "개발 속도 저하 임계점", "비즈니스 리스크 수준"],
        anti_patterns=["항상 나중으로 미룸", "PMF 전에 완벽주의"],
    ),
    InterviewQuestion(
        question="스타트업 초기에 모니터링/알람을 어떻게 설정하시나요?",
        category=QuestionCategory.STARTUP,
        difficulty=1, frequency=3,
        answer_points=["비즈니스 핵심 지표 우선", "에러율과 응답시간 기본", "무료/저비용 도구 활용"],
        anti_patterns=["모니터링 없음", "너무 많은 알람으로 노이즈"],
    ),

    # -----------------------------------------------------------------------
    # 대기업 (15개)
    # -----------------------------------------------------------------------
    InterviewQuestion(
        question="대규모 조직에서 기술 표준화를 어떻게 추진하셨나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=3, frequency=4,
        answer_points=["상향식 vs 하향식 접근", "얼리어답터 팀 활용", "가이드라인 문서화"],
        anti_patterns=["강제로만 추진", "표준 없이 각자"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="여러 팀이 같은 인프라/플랫폼을 사용할 때 충돌을 어떻게 해결하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["플랫폼 팀과 제품 팀 역할 분리", "SLA와 사용 규칙 정의", "갈등 해결 프로세스"],
        anti_patterns=["강자가 독점", "해결 없이 방치"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="레거시 시스템을 어떻게 현대화(Modernization)하셨나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=3, frequency=4,
        answer_points=["Strangler Fig 패턴", "위험 최소화 단계별 마이그레이션", "비즈니스 연속성 유지"],
        anti_patterns=["Big Bang 재작성", "비즈니스 중단 없이 전환 못함"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="규제(보안 감사, 개인정보보호법 등) 요건을 시스템에 어떻게 반영하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["법무/보안팀과 협업", "Privacy by Design", "감사 로그 설계"],
        anti_patterns=["나중에 추가", "기술팀 단독 결정"],
    ),
    InterviewQuestion(
        question="사내 플랫폼(Internal Developer Platform)을 구축한 경험을 말씀해 주세요.",
        category=QuestionCategory.LARGE_CORP,
        difficulty=3, frequency=3,
        answer_points=["개발자 경험(DX) 목표", "셀프서비스 인프라", "채택률과 성과 지표"],
        anti_patterns=["강제 사용", "개발자 피드백 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="대규모 마이그레이션(DB, 클라우드, 언어 등)을 어떻게 계획하고 실행하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=3, frequency=4,
        answer_points=["이중 쓰기(Dual Write) 전략", "데이터 검증 단계", "롤백 계획"],
        anti_patterns=["Big Bang 전환", "롤백 계획 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="여러 팀의 API를 통합/표준화하는 작업을 어떻게 하셨나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["API 거버넌스 체계", "하위 호환성 정책", "마이그레이션 가이드"],
        anti_patterns=["Breaking Change 무단 배포", "팀별 제각각 API"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="사내 오픈소스 또는 내부 라이브러리를 어떻게 관리하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["버전 관리와 배포 정책", "문서화와 예제", "유지보수 책임 명확화"],
        anti_patterns=["문서 없음", "책임자 없음"],
    ),
    InterviewQuestion(
        question="조직 간 의존성(Cross-team Dependency)을 어떻게 관리하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=4,
        answer_points=["의존성 명시와 계획", "인터페이스 계약", "병렬 개발 전략"],
        anti_patterns=["의존성 숨김", "블로킹 허용"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="대기업에서 빠른 실행 속도를 유지하기 위해 어떤 노력을 하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=4,
        answer_points=["의사결정 권한 위임", "불필요한 승인 프로세스 제거", "자율 팀 구조"],
        anti_patterns=["모든 것을 위로 보고", "속도 개선 시도 없음"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="사내 기술 공유 문화를 어떻게 만드셨나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=1, frequency=3,
        answer_points=["Tech Talk, 사내 세미나", "기술 블로그 운영", "지식 공유 인센티브"],
        anti_patterns=["강제 참석", "일방향 전달만"],
        star_applicable=True,
    ),
    InterviewQuestion(
        question="벤더(외부 솔루션)와 내재화(자체 개발)를 어떻게 결정하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["TCO(Total Cost of Ownership) 비교", "전략적 차별화 여부", "유지보수 역량"],
        anti_patterns=["항상 자체 개발", "항상 벤더 의존"],
    ),
    InterviewQuestion(
        question="대기업의 보안 정책과 개발 생산성의 균형을 어떻게 맞추시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=2, frequency=3,
        answer_points=["보안 자동화로 마찰 최소화", "보안팀과 협업 채널", "위험 기반 접근"],
        anti_patterns=["보안 회피", "생산성 완전 희생"],
    ),
    InterviewQuestion(
        question="대규모 온보딩을 어떻게 효율적으로 진행하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=1, frequency=3,
        answer_points=["온보딩 문서화", "버디 시스템", "30/60/90일 목표"],
        anti_patterns=["알아서 적응해라", "문서 없음"],
    ),
    InterviewQuestion(
        question="글로벌 서비스를 운영할 때 멀티 리전 아키텍처를 어떻게 설계하시나요?",
        category=QuestionCategory.LARGE_CORP,
        difficulty=3, frequency=3,
        answer_points=["데이터 레지던시 요건", "Active-Active vs Active-Passive", "글로벌 트래픽 라우팅"],
        anti_patterns=["단일 리전 운영", "레이턴시 고려 없음"],
    ),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_questions_by_category(category: QuestionCategory) -> list[InterviewQuestion]:
    """Return all questions for a given category."""
    return [q for q in QUESTION_BANK if q.category == category]


def get_questions_by_difficulty(difficulty: int) -> list[InterviewQuestion]:
    """Return questions filtered by difficulty (1-3)."""
    return [q for q in QUESTION_BANK if q.difficulty == difficulty]


def get_top_frequency_questions(
    category: QuestionCategory | None = None,
    min_frequency: int = 4,
    limit: int = 10,
) -> list[InterviewQuestion]:
    """Return high-frequency questions, optionally filtered by category."""
    pool = QUESTION_BANK if category is None else get_questions_by_category(category)
    filtered = [q for q in pool if q.frequency >= min_frequency]
    return sorted(filtered, key=lambda q: q.frequency, reverse=True)[:limit]


def get_star_questions(category: QuestionCategory | None = None) -> list[InterviewQuestion]:
    """Return questions suitable for STAR-format answers."""
    pool = QUESTION_BANK if category is None else get_questions_by_category(category)
    return [q for q in pool if q.star_applicable]


def build_answer_guide(question: InterviewQuestion) -> AnswerGuide:
    """Build a rule-based AnswerGuide from an InterviewQuestion."""
    star_structure: dict[str, str] = {}
    if question.star_applicable:
        star_structure = {
            "Situation": "어떤 상황/맥락이었는지 구체적으로 설명",
            "Task": "본인의 역할과 책임이 무엇이었는지",
            "Action": "어떤 행동을 취했는지 (본인 기여 중심)",
            "Result": "결과를 정량적으로 표현 (%, 시간, 금액 등)",
        }

    time_sec = 90 if question.difficulty == 1 else (120 if question.difficulty == 2 else 180)

    return AnswerGuide(
        question=question.question,
        key_points=question.answer_points,
        star_structure=star_structure,
        anti_patterns=question.anti_patterns,
        time_allocation_sec=time_sec,
    )


def get_tech_questions_for_stack(tech_stack: list[str]) -> list[InterviewQuestion]:
    """Return tech questions relevant to given tech stack keywords."""
    tech_categories = {
        QuestionCategory.TECH_COMMON,
        QuestionCategory.FRONTEND,
        QuestionCategory.BACKEND,
        QuestionCategory.DEVOPS,
        QuestionCategory.DATA,
        QuestionCategory.MOBILE,
    }
    results: list[InterviewQuestion] = []
    stack_lower = {s.lower() for s in tech_stack}

    for q in QUESTION_BANK:
        if q.category not in tech_categories:
            continue
        q_lower = q.question.lower()
        if any(kw in q_lower for kw in stack_lower):
            results.append(q)

    # Deduplicate and sort by frequency
    seen: set[str] = set()
    unique: list[InterviewQuestion] = []
    for q in sorted(results, key=lambda x: x.frequency, reverse=True):
        if q.question not in seen:
            seen.add(q.question)
            unique.append(q)
    return unique
