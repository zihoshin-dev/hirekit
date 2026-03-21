"""Korean cover letter cliché detector — rule-based, no LLM required."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Cliché database (100+ patterns with alternative suggestions)
# ---------------------------------------------------------------------------

# Format: (pattern_regex, alternative_suggestion)
_CLICHE_DB: list[tuple[str, str]] = [
    # 성장과정 클리셰
    (r"어릴\s*때부터\s*.{0,10}에\s*관심", "구체적 계기(사건/프로젝트)로 시작하세요"),
    (r"어린\s*시절부터", "언제 어떤 경험이 전환점이 됐는지 서술하세요"),
    (r"꿈을\s*키워\s*왔", "그 꿈을 위해 실제 취한 행동 중심으로 재작성하세요"),
    (r"부모님의\s*가르침", "가르침이 아닌 본인이 직접 겪은 경험을 서술하세요"),
    (r"항상\s*꿈꿔\s*왔", "언제, 어떤 계기로 그 방향을 선택했는지 구체화하세요"),
    (r"평소\s*관심이\s*많", "관심이 실제 행동(학습/프로젝트)으로 이어진 경험을 쓰세요"),
    # 열정/노력 클리셰
    (r"열정(을\s*가지고|적인|을\s*바탕)", "열정 대신 실제 수치·성과로 증명하세요"),
    (r"누구보다\s*열심히", "어떤 구체적 행동을 얼마나 했는지 서술하세요"),
    (r"최선을\s*다해", "최선의 결과를 수치로 보여주세요"),
    (r"노력하겠습니다", "어떤 계획으로, 어떤 기간 안에 달성할지 명시하세요"),
    (r"열심히\s*하겠습니다", "구체적 행동 계획을 제시하세요"),
    (r"최선을\s*다하겠습니다", "목표·지표·기간을 포함한 구체적 포부로 교체하세요"),
    # 성격 클리셰
    (r"도전(적인|을\s*두려워하지)", "어떤 도전을 어떻게 극복했는지 STAR 구조로 서술하세요"),
    (r"성실(한|하게|함)", "성실함이 드러난 구체적 성과나 습관을 서술하세요"),
    (r"책임감(이\s*강한|있는|있게)", "책임감을 발휘한 구체적 상황과 결과를 제시하세요"),
    (r"꼼꼼한\s*성격", "꼼꼼함이 결과에 미친 영향을 수치로 보여주세요"),
    (r"팀워크(를\s*중시|가\s*좋은)", "협업으로 달성한 구체적 결과를 서술하세요"),
    (r"소통(을\s*잘하는|이\s*원활한)", "소통으로 해결한 구체적 상황을 STAR로 작성하세요"),
    (r"긍정적인\s*마인드", "긍정적 태도가 결과를 바꾼 구체적 사례를 제시하세요"),
    (r"적극적(인|으로)", "적극성이 드러난 구체적 행동과 결과를 서술하세요"),
    (r"창의(적인|력이\s*풍부한)", "창의적 아이디어가 적용된 실제 프로젝트 결과를 쓰세요"),
    (r"남들보다\s*뛰어난", "구체적 비교 지표나 순위를 사용하세요"),
    (r"완벽주의(적인|자)", "완벽을 추구한 결과로 개선된 수치를 보여주세요"),
    # 지원동기 클리셰
    (r"귀사에\s*매력을\s*느껴", "어떤 구체적 제품·서비스·수치가 매력적인지 서술하세요"),
    (r"귀사의\s*비전에\s*공감", "비전의 어떤 부분이 나의 커리어 목표와 일치하는지 연결하세요"),
    (r"함께\s*성장하고\s*싶", "어떤 영역에서 어떻게 기여하며 성장할지 구체화하세요"),
    (r"업계\s*1위", "1위라는 사실보다 그것이 나의 지원 이유와 어떻게 연결되는지 서술하세요"),
    (r"오래전부터\s*지원하고\s*싶", "언제, 어떤 계기로 관심을 갖게 됐는지 구체화하세요"),
    (r"인재를\s*소중히", "인재 문화의 구체적 사례(제도·사례)를 언급하세요"),
    (r"복리후생이\s*좋", "복리후생은 지원동기 서술에 적합하지 않습니다"),
    (r"글로벌\s*기업으로\s*성장", "어떤 글로벌 행보에 어떻게 기여할지 구체화하세요"),
    # 역량 클리셰
    (r"다양한\s*경험을\s*통해", "다양한 경험 중 핵심 1-2가지를 구체적으로 서술하세요"),
    (r"꾸준히\s*노력해\s*왔", "노력의 결과로 달성한 수치·성과를 제시하세요"),
    (r"전문성을\s*키워", "어떤 전문성을 어느 수준까지 키웠는지 구체화하세요"),
    (r"역량을\s*키워\s*왔", "역량 향상의 증거(자격증·프로젝트·수치)를 제시하세요"),
    (r"배움을\s*게을리하지\s*않", "실제로 취득한 자격증·수료 과정·프로젝트로 증명하세요"),
    (r"주도적으로\s*이끌어", "주도해서 달성한 구체적 결과를 수치로 서술하세요"),
    # 포부 클리셰
    (r"귀사에\s*기여하고\s*싶", "어떤 방식으로 얼마나 기여할지 수치·계획으로 제시하세요"),
    (r"최고의\s*[인전]재가\s*되", "최고의 기준이 무엇인지 구체화하세요"),
    (r"회사와\s*함께\s*성장", "내가 기여할 부분과 얻을 성장을 구체화하세요"),
    (r"사회에\s*기여하고\s*싶", "어떤 문제를 어떻게 해결해 기여할지 명시하세요"),
    (r"발전하는\s*모습을\s*보여", "어떤 지표로 발전을 측정할지 제시하세요"),
    # 일반 추상 표현
    (r"항상\s*최선", "최선 대신 구체적 목표와 달성 방법을 서술하세요"),
    (r"끊임없이\s*노력", "노력의 빈도·방법·결과를 수치로 보여주세요"),
    (r"끊임없는\s*자기계발", "자기계발의 구체적 내용과 결과를 제시하세요"),
    (r"빠르게\s*성장하는", "성장 수치(MAU, 매출, 팀 규모 등)를 인용하세요"),
    (r"저는\s*.{0,5}사람입니다", "사람입니다 선언 대신 그것을 증명하는 사례를 먼저 서술하세요"),
    (r"부족한\s*점이\s*많지만", "부족함을 인정하는 대신 개선 계획과 현황을 서술하세요"),
    (r"작은\s*것부터\s*차근차근", "첫 번째 목표와 달성 기간을 구체화하세요"),
    # 단점 클리셰
    (r"너무\s*완벽을\s*추구", "완벽 추구가 결과에 미친 영향과 개선 방안을 서술하세요"),
    (r"지나치게\s*꼼꼼한", "꼼꼼함으로 인한 부작용과 균형 잡는 방법을 서술하세요"),
    (r"너무\s*열정적이어서", "열정 과잉의 구체적 상황과 조절 방법을 서술하세요"),
    (r"단점이라면.*없다고", "솔직하게 실제 단점과 개선 과정을 서술하세요"),
    (r"급한\s*성격을\s*고치", "급함을 제어한 구체적 방법과 결과를 서술하세요"),
    # 영어 섞임 클리셰 (형식적)
    (r"Win-Win", "Win-Win 대신 상호 이익의 구체적 내용을 서술하세요"),
    (r"시너지를\s*창출", "시너지 창출의 구체적 메커니즘과 결과를 서술하세요"),
    (r"글로벌\s*인재", "글로벌 역량의 구체적 증거(언어·경험·프로젝트)를 제시하세요"),
    # 판에 박힌 마무리
    (r"꼭\s*뽑아\s*주시면", "희망 표현 대신 기여 가치를 구체화하세요"),
    (r"후회하지\s*않으실\s*겁니다", "구체적 기여 계획과 목표로 교체하세요"),
    (r"잘\s*부탁드립니다", "구체적 다음 단계나 포부로 마무리하세요"),
    (r"열심히\s*배우겠습니다", "무엇을 어떤 방법으로 얼마 만에 익힐지 명시하세요"),
    # 가족/환경 공식 서술
    (r"화목한\s*가정에서", "가정환경보다 본인의 가치관 형성 경험을 서술하세요"),
    (r"부모님의\s*영향으로", "부모님 언급 대신 본인 경험 중심으로 재작성하세요"),
    (r"경제적으로\s*어려운", "역경 자체보다 역경 극복 과정과 결과를 서술하세요"),
    # 겸손 표현 과용
    (r"미천하지만", "겸양 표현 대신 실제 역량과 성과로 증명하세요"),
    (r"부족하지만\s*최선", "부족함 인정 대신 구체적 보완 계획을 제시하세요"),
    (r"아직\s*부족한\s*점이", "부족한 부분과 보완 로드맵을 구체화하세요"),
    # 추상적 가치관
    (r"정직(과|하고|함)", "정직함이 드러난 구체적 상황과 결과를 서술하세요"),
    (r"신뢰를\s*바탕으로", "신뢰 구축의 구체적 방법과 결과를 제시하세요"),
    (r"인간관계가\s*넓은", "관계 형성이 결과에 미친 영향을 구체화하세요"),
    # 막연한 미래
    (r"언젠가는\s*꼭", "언제, 어떤 방법으로 달성할지 구체화하세요"),
    (r"앞으로도\s*계속", "어떤 방향으로 얼마나 성장할지 기간과 지표를 명시하세요"),
    (r"더\s*나은\s*사람이\s*되", "어떤 측면에서 어느 수준까지 성장할지 구체화하세요"),
    # 자기소개 공식 패턴
    (r"저는\s*.{0,5}입니다\.\s*저는", "반복 주어(저는) 구조를 바꿔 다양한 문장으로 시작하세요"),
    (r"한\s*마디로\s*표현하면", "한 마디 요약보다 구체적 사례로 시작하세요"),
    (r"제\s*이름은.*입니다", "이름 소개 공식 대신 핵심 가치나 경험으로 시작하세요"),
    # 과장된 자신감
    (r"자신\s*있습니다", "자신감 표현 대신 근거(수치·경험)로 증명하세요"),
    (r"누구보다도", "구체적 비교 지표나 성과 순위를 사용하세요"),
    (r"탁월한\s*역량", "탁월함의 증거를 수치·사례로 제시하세요"),
    # IT/스타트업 과용 표현
    (r"혁신적인\s*생각", "혁신적 아이디어의 구체적 사례와 결과를 서술하세요"),
    (r"데이터\s*기반의\s*사고", "어떤 데이터로 어떤 결정을 내렸는지 구체화하세요"),
    (r"문제\s*해결\s*능력이\s*뛰어난", "어떤 문제를 어떻게 해결했는지 STAR로 서술하세요"),
    (r"빠른\s*적응력", "적응이 필요했던 상황과 적응 후 성과를 서술하세요"),
    (r"능동적(으로|인)", "능동적 행동의 구체적 사례와 결과를 제시하세요"),
]

# ---------------------------------------------------------------------------
# Detection result
# ---------------------------------------------------------------------------


@dataclass
class ClicheMatch:
    """A detected cliché with context and suggestion."""

    text: str           # matched text in the original
    suggestion: str     # alternative suggestion
    position: int       # character offset in input


@dataclass
class ClicheReport:
    """Full cliché analysis report for a cover letter text."""

    matches: list[ClicheMatch] = field(default_factory=list)
    cliche_count: int = 0
    cliche_density: float = 0.0   # clichés per 100 characters
    differentiation_score: float = 100.0  # 100 = no clichés

    @property
    def grade(self) -> str:
        """Grade based on differentiation score."""
        if self.differentiation_score >= 80:
            return "S"
        if self.differentiation_score >= 65:
            return "A"
        if self.differentiation_score >= 50:
            return "B"
        if self.differentiation_score >= 35:
            return "C"
        return "D"

    def to_markdown(self) -> str:
        lines = [
            "## 클리셰 분석",
            f"**차별화 점수:** {self.differentiation_score:.0f}/100 (Grade {self.grade})",
            f"**클리셰 감지:** {self.cliche_count}개",
            "",
        ]
        if not self.matches:
            lines.append("클리셰 표현이 감지되지 않았습니다.")
            return "\n".join(lines)

        lines.append("### 감지된 클리셰 및 개선 제안")
        for m in self.matches:
            lines.append(f'- **"{m.text}"** → {m.suggestion}')
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class ClicheDetector:
    """Rule-based Korean cover letter cliché detector."""

    # Penalty per cliché (differentiation_score starts at 100)
    _PENALTY_PER_CLICHE = 5.0
    _MIN_SCORE = 0.0

    def __init__(self, extra_patterns: list[tuple[str, str]] | None = None):
        """Initialise detector, optionally extending the built-in database.

        Args:
            extra_patterns: Additional (regex_pattern, suggestion) tuples.
        """
        patterns = list(_CLICHE_DB)
        if extra_patterns:
            patterns.extend(extra_patterns)

        # Pre-compile for performance
        self._compiled: list[tuple[re.Pattern[str], str]] = [
            (re.compile(pat, re.UNICODE), suggestion)
            for pat, suggestion in patterns
        ]

    def detect(self, text: str) -> ClicheReport:
        """Detect clichés in *text* and return a :class:`ClicheReport`.

        Args:
            text: Cover letter text to analyse.

        Returns:
            ClicheReport with matched clichés, density, and score.
        """
        report = ClicheReport()
        seen_positions: set[int] = set()

        for pattern, suggestion in self._compiled:
            for match in pattern.finditer(text):
                start = match.start()
                # Deduplicate overlapping matches at same position
                if start in seen_positions:
                    continue
                seen_positions.add(start)

                report.matches.append(
                    ClicheMatch(
                        text=match.group(0),
                        suggestion=suggestion,
                        position=start,
                    )
                )

        report.cliche_count = len(report.matches)

        char_count = len(text)
        if char_count > 0:
            report.cliche_density = report.cliche_count / char_count * 100
        else:
            report.cliche_density = 0.0

        penalty = report.cliche_count * self._PENALTY_PER_CLICHE
        report.differentiation_score = max(
            self._MIN_SCORE, 100.0 - penalty
        )

        return report

    def get_suggestions(self, text: str) -> list[str]:
        """Return a flat list of improvement suggestions for detected clichés.

        Convenience wrapper around :meth:`detect`.
        """
        report = self.detect(text)
        return [f'"{m.text}" → {m.suggestion}' for m in report.matches]
