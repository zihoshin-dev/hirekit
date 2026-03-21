"""Tests for the scoring engine."""

from hirekit.engine.scorer import Scorecard, ScoreDimension, create_default_scorecard


class TestScorecard:
    def test_total_score_calculation(self):
        """Weighted sum should normalize to 100-point scale."""
        card = Scorecard(
            company="TestCorp",
            dimensions=[
                ScoreDimension(name="a", label="A", weight=0.5, score=5.0),
                ScoreDimension(name="b", label="B", weight=0.5, score=3.0),
            ],
        )
        # (5*0.5 + 3*0.5) * 20 = 4.0 * 20 = 80
        assert card.total_score == 80.0

    def test_grade_s(self):
        card = Scorecard(
            company="Test",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=5.0)],
        )
        assert card.grade == "S"  # 100 points

    def test_grade_a(self):
        card = Scorecard(
            company="Test",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=3.5)],
        )
        assert card.grade == "A"  # 70 points

    def test_grade_b(self):
        card = Scorecard(
            company="Test",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=3.0)],
        )
        assert card.grade == "B"  # 60 points

    def test_grade_c(self):
        card = Scorecard(
            company="Test",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=2.0)],
        )
        assert card.grade == "C"  # 40 points

    def test_grade_d(self):
        card = Scorecard(
            company="Test",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=1.0)],
        )
        assert card.grade == "D"  # 20 points

    def test_default_scorecard_has_5_dimensions(self):
        card = create_default_scorecard("TestCorp")
        assert len(card.dimensions) == 5
        assert card.company == "TestCorp"

    def test_default_weights_sum_to_one(self):
        card = create_default_scorecard("Test")
        total_weight = sum(d.weight for d in card.dimensions)
        assert abs(total_weight - 1.0) < 0.001

    def test_summary_format(self):
        card = Scorecard(
            company="Kakao",
            dimensions=[ScoreDimension(name="a", label="A", weight=1.0, score=4.0)],
        )
        assert "Kakao" in card.summary()
        assert "80" in card.summary()
        assert "S" in card.summary()
