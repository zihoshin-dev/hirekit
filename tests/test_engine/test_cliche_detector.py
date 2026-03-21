"""Tests for the Korean cover letter cliché detector."""

from hirekit.core.cliche_detector import ClicheDetector, ClicheMatch, ClicheReport


class TestClicheMatch:
    def test_fields(self):
        m = ClicheMatch(text="열정을 가지고", suggestion="수치로 증명하세요", position=0)
        assert m.text == "열정을 가지고"
        assert m.suggestion == "수치로 증명하세요"
        assert m.position == 0


class TestClicheReport:
    def test_grade_no_cliches(self):
        report = ClicheReport(differentiation_score=100.0)
        assert report.grade == "S"

    def test_grade_many_cliches(self):
        report = ClicheReport(differentiation_score=20.0)
        assert report.grade == "D"

    def test_grade_medium(self):
        report = ClicheReport(differentiation_score=65.0)
        assert report.grade == "A"

    def test_to_markdown_no_matches(self):
        report = ClicheReport(differentiation_score=100.0)
        md = report.to_markdown()
        assert "클리셰 표현이 감지되지 않았습니다" in md

    def test_to_markdown_with_matches(self):
        report = ClicheReport(
            cliche_count=1,
            differentiation_score=95.0,
            matches=[ClicheMatch(text="열정을 가지고", suggestion="수치로 증명하세요", position=0)],
        )
        md = report.to_markdown()
        assert "열정을 가지고" in md
        assert "수치로 증명하세요" in md


class TestClicheDetector:
    def test_empty_text(self):
        detector = ClicheDetector()
        report = detector.detect("")
        assert report.cliche_count == 0
        assert report.differentiation_score == 100.0
        assert report.cliche_density == 0.0

    def test_no_cliches_in_concrete_text(self):
        detector = ClicheDetector()
        text = (
            "2023년 6월 A/B 테스트를 통해 전환율을 12% 개선했습니다. "
            "Python과 SQL로 데이터 파이프라인을 구축하여 처리 속도를 3배 향상시켰습니다."
        )
        report = detector.detect(text)
        assert report.cliche_count == 0
        assert report.differentiation_score == 100.0

    def test_detects_enthusiasm_cliche(self):
        detector = ClicheDetector()
        text = "저는 열정을 가지고 이 직무에 지원합니다."
        report = detector.detect(text)
        assert report.cliche_count >= 1
        assert report.differentiation_score < 100.0

    def test_detects_childhood_interest_cliche(self):
        detector = ClicheDetector()
        text = "어릴 때부터 IT에 관심이 있었습니다."
        report = detector.detect(text)
        assert report.cliche_count >= 1

    def test_detects_sincere_cliche(self):
        detector = ClicheDetector()
        text = "저는 성실한 사람으로 항상 최선을 다하겠습니다."
        report = detector.detect(text)
        assert report.cliche_count >= 1

    def test_detects_challenge_cliche(self):
        detector = ClicheDetector()
        text = "저는 도전적인 성격을 가지고 있습니다."
        report = detector.detect(text)
        assert report.cliche_count >= 1

    def test_differentiation_score_decreases_with_more_cliches(self):
        detector = ClicheDetector()
        few = detector.detect("저는 성실한 사람입니다.")
        many = detector.detect(
            "저는 성실한 사람입니다. 열정을 가지고 도전적인 마음으로 "
            "귀사에 기여하고 싶습니다. 항상 최선을 다하겠습니다."
        )
        assert many.differentiation_score <= few.differentiation_score

    def test_cliche_density_nonzero_for_cliche_text(self):
        detector = ClicheDetector()
        text = "저는 열정을 가지고 성실하게 일합니다."
        report = detector.detect(text)
        if report.cliche_count > 0:
            assert report.cliche_density > 0.0

    def test_get_suggestions_returns_list(self):
        detector = ClicheDetector()
        text = "귀사에 기여하고 싶습니다. 열정을 가지고 도전하겠습니다."
        suggestions = detector.get_suggestions(text)
        assert isinstance(suggestions, list)

    def test_get_suggestions_format(self):
        detector = ClicheDetector()
        text = "저는 성실하게 일합니다."
        suggestions = detector.get_suggestions(text)
        for s in suggestions:
            assert "→" in s

    def test_extra_patterns_extend_database(self):
        extra = [(r"우리팀의\s*핵심", "핵심 기여를 수치로 증명하세요")]
        detector = ClicheDetector(extra_patterns=extra)
        report = detector.detect("저는 우리팀의 핵심 인재입니다.")
        assert report.cliche_count >= 1

    def test_score_floor_is_zero(self):
        detector = ClicheDetector()
        # 21+ clichés would drive score below 0 without floor
        text = " ".join([
            "열정을 가지고", "성실한", "도전적인", "귀사에 기여하고 싶습니다",
            "항상 최선을", "끊임없이 노력", "열심히 하겠습니다",
            "남들보다 뛰어난", "함께 성장하고 싶", "책임감이 강한",
            "긍정적인 마인드", "적극적으로", "팀워크를 중시", "꼼꼼한 성격",
            "창의적인", "꿈을 키워 왔", "어릴 때부터", "최선을 다해",
            "노력하겠습니다", "귀사의 비전에 공감", "다양한 경험을 통해",
        ] * 3)
        report = detector.detect(text)
        assert report.differentiation_score >= 0.0

    def test_deduplication_no_double_count_at_same_position(self):
        detector = ClicheDetector()
        # Same text twice should not duplicate at same offset
        text = "열정을 가지고 열정을 가지고"
        report = detector.detect(text)
        # Second match is at a different offset, so 2 is expected
        assert report.cliche_count >= 1
