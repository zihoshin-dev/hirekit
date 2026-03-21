"""Tests for interview preparation engine."""

from hirekit.engine.interview_prep import InterviewGuide, InterviewPrep


class TestInterviewGuide:
    def test_to_markdown_includes_company(self):
        guide = InterviewGuide(company="카카오", position="PM")
        guide.common_questions = [
            {"question": "Why 카카오?", "answer": "Mission alignment."}
        ]
        md = guide.to_markdown()
        assert "카카오" in md
        assert "PM" in md
        assert "Why 카카오?" in md

    def test_empty_guide(self):
        guide = InterviewGuide(company="Test")
        md = guide.to_markdown()
        assert "Test" in md


class TestInterviewPrep:
    def test_default_questions_generated(self):
        prep = InterviewPrep()
        guide = prep.prepare(company="카카오", position="PM")

        assert guide.company == "카카오"
        assert guide.position == "PM"
        assert len(guide.common_questions) == 5
        assert len(guide.reverse_questions) == 5

    def test_company_name_substituted(self):
        prep = InterviewPrep()
        guide = prep.prepare(company="토스")

        for q in guide.common_questions:
            if "토스" in q["question"]:
                break
        else:
            # At least one question should mention the company
            assert any("토스" in q["question"] for q in guide.common_questions)

    def test_tips_in_no_llm_mode(self):
        prep = InterviewPrep()
        guide = prep.prepare(company="네이버")

        assert len(guide.tips) >= 3
