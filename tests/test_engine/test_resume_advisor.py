"""Tests for resume advisor engine."""

import tempfile
from pathlib import Path

from hirekit.engine.resume_advisor import ResumeAdvisor, ResumeFeedback


class TestResumeFeedback:
    def test_grade_calculation(self):
        fb = ResumeFeedback(overall_score=85)
        assert fb.grade == "S"

    def test_grade_d(self):
        fb = ResumeFeedback(overall_score=20)
        assert fb.grade == "D"

    def test_to_markdown(self):
        fb = ResumeFeedback(
            overall_score=70,
            strengths=["Good structure"],
            improvements=["Add metrics"],
        )
        md = fb.to_markdown()
        assert "70" in md
        assert "Good structure" in md
        assert "Add metrics" in md


class TestResumeAdvisor:
    def test_review_missing_file(self):
        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path="/nonexistent/file.md")
        assert "not found" in fb.improvements[0].lower()

    def test_review_basic_resume(self):
        resume_content = """
# John Doe
email: john@example.com

## Summary
Experienced PM with 5 years in fintech.

## Experience
- 메이크스타 PM (2021-2024): 7,500 SKU 관리, 매출 30% 성장
- 토스페이먼츠 (2020-2021): PG 결제 연동

## Education
서울대학교 경영학과

## Skills
Python, SQL, Data Analysis, Product Management
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(resume_content)
            path = f.name

        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path=path)

        # Should find most sections
        assert fb.overall_score > 40
        assert any("experience" in s.lower() for s in fb.strengths)
        assert any("skill" in s.lower() for s in fb.strengths)

        Path(path).unlink()

    def test_keyword_gap_detection(self):
        resume = "Python developer with SQL experience"
        jd = "Required: Kubernetes, Docker, AWS, Python, Go"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(resume)
            path = f.name

        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path=path, jd_text=jd)

        # Should detect missing keywords
        gaps_lower = [g.lower() for g in fb.keyword_gaps]
        assert any("kubernetes" in g for g in gaps_lower) or \
               any("docker" in g for g in gaps_lower)

        Path(path).unlink()

    def test_short_resume_warning(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Short resume")
            path = f.name

        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path=path)

        assert any("short" in issue.lower() or "Too" in issue for issue in fb.ats_issues)

        Path(path).unlink()
