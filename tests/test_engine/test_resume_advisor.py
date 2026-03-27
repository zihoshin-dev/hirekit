"""Tests for resume advisor engine."""

import tempfile
from pathlib import Path

from hirekit.engine.resume_advisor import ResumeAdvisor, ResumeFeedback

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "hero-flow"


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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(resume)
            path = f.name

        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path=path, jd_text=jd)

        # Should detect missing keywords
        gaps_lower = [g.lower() for g in fb.keyword_gaps]
        assert any("kubernetes" in g for g in gaps_lower) or any("docker" in g for g in gaps_lower)

        Path(path).unlink()

    def test_short_resume_warning(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Short resume")
            path = f.name

        advisor = ResumeAdvisor()
        fb = advisor.review(resume_path=path)

        assert any("short" in issue.lower() or "Too" in issue for issue in fb.ats_issues)

        Path(path).unlink()

    def test_high_signal_resume_fixture_beats_low_signal_fixture(self):
        jd_text = (FIXTURE_ROOT / "jd-high-signal.txt").read_text(encoding="utf-8")
        advisor = ResumeAdvisor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as high_file:
            high_file.write((FIXTURE_ROOT / "resume-high-signal.md").read_text(encoding="utf-8"))
            high_path = high_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as low_file:
            low_file.write((FIXTURE_ROOT / "resume-low-signal.md").read_text(encoding="utf-8"))
            low_path = low_file.name

        high_feedback = advisor.review(resume_path=high_path, jd_text=jd_text)
        low_feedback = advisor.review(resume_path=low_path, jd_text=jd_text)

        assert high_feedback.overall_score > low_feedback.overall_score

        Path(high_path).unlink()
        Path(low_path).unlink()

    def test_low_signal_resume_fixture_exposes_keyword_gaps(self):
        jd_text = (FIXTURE_ROOT / "jd-high-signal.txt").read_text(encoding="utf-8")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as low_file:
            low_file.write((FIXTURE_ROOT / "resume-low-signal.md").read_text(encoding="utf-8"))
            low_path = low_file.name

        advisor = ResumeAdvisor()
        feedback = advisor.review(resume_path=low_path, jd_text=jd_text)

        gaps_lower = [gap.lower() for gap in feedback.keyword_gaps]
        assert any("kubernetes" in gap for gap in gaps_lower) or any("docker" in gap for gap in gaps_lower)

        Path(low_path).unlink()

    def test_switcher_mapping_outputs_truthful_strengths_and_transferability(self):
        jd_text = (FIXTURE_ROOT / "jd-experienced-switcher-misleading.txt").read_text(encoding="utf-8")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as resume_file:
            resume_file.write((FIXTURE_ROOT / "resume-experienced-switcher-misleading.md").read_text(encoding="utf-8"))
            resume_path = resume_file.name

        advisor = ResumeAdvisor()
        feedback = advisor.review(resume_path=resume_path, jd_text=jd_text)

        assert any("제품과 운영을 함께 이해하는 경험" in item for item in feedback.strengths)
        assert any("크로스펑셔널 협업 경험" in item for item in feedback.strengths)
        assert any("데이터 기반 의사결정 역량" in item for item in feedback.missing_proof)
        assert any("제품 로드맵과 실행 우선순위 정리" in item for item in feedback.transferability_opportunities)

        Path(resume_path).unlink()

    def test_missing_proof_guardrail_does_not_treat_skill_keyword_as_proven(self):
        jd_text = (FIXTURE_ROOT / "jd-high-signal.txt").read_text(encoding="utf-8")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as resume_file:
            resume_file.write((FIXTURE_ROOT / "resume-low-signal.md").read_text(encoding="utf-8"))
            resume_path = resume_file.name

        advisor = ResumeAdvisor()
        feedback = advisor.review(resume_path=resume_path, jd_text=jd_text)

        assert any("Python 기반 API 개발 경험" in item for item in feedback.missing_proof)
        assert not any("Python 기반 API 개발 경험" in item for item in feedback.strengths)

        Path(resume_path).unlink()
