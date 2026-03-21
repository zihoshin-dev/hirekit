"""Tests for Korean cover letter coach engine."""

from hirekit.engine.cover_letter import CoverLetterCoach, CoverLetterDraft, CoverLetterSection


class TestCoverLetterSection:
    def test_grade_property(self):
        section = CoverLetterSection(key="growth", title="성장과정", score=85.0)
        assert section.grade == "S"

    def test_to_markdown_includes_title_and_content(self):
        section = CoverLetterSection(
            key="motivation", title="지원동기", content="카카오를 지원합니다.", score=70.0
        )
        section.word_count = len(section.content)
        md = section.to_markdown()
        assert "지원동기" in md
        assert "카카오를 지원합니다." in md
        assert "70" in md

    def test_to_markdown_includes_feedback(self):
        section = CoverLetterSection(key="personality", title="성격의 장단점", score=50.0)
        section.feedback = ["수치를 추가하세요.", "구체적 사례 필요"]
        md = section.to_markdown()
        assert "수치를 추가하세요." in md
        assert "구체적 사례 필요" in md


class TestCoverLetterDraft:
    def test_grade_property(self):
        draft = CoverLetterDraft(company="토스", overall_score=90.0)
        assert draft.grade == "S"

    def test_to_markdown_includes_company_and_position(self):
        draft = CoverLetterDraft(company="카카오", position="PM", overall_score=75.0)
        md = draft.to_markdown()
        assert "카카오" in md
        assert "PM" in md

    def test_to_markdown_includes_company_insights(self):
        draft = CoverLetterDraft(company="네이버", overall_score=60.0)
        draft.company_insights = {"핵심 사업": "검색 플랫폼"}
        md = draft.to_markdown()
        assert "검색 플랫폼" in md

    def test_to_markdown_includes_sections(self):
        draft = CoverLetterDraft(company="라인", overall_score=65.0)
        draft.sections = [
            CoverLetterSection(key="growth", title="성장과정", content="성장 내용", score=70.0)
        ]
        md = draft.to_markdown()
        assert "성장과정" in md
        assert "성장 내용" in md


class TestCoverLetterCoach:
    def test_draft_returns_four_sections(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="카카오", position="PM")
        assert len(draft.sections) == 4
        keys = [s.key for s in draft.sections]
        assert keys == ["growth", "motivation", "competency", "personality"]

    def test_draft_company_and_position_set(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="토스", position="백엔드 엔지니어")
        assert draft.company == "토스"
        assert draft.position == "백엔드 엔지니어"

    def test_draft_overall_score_in_range(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="네이버")
        assert 0.0 <= draft.overall_score <= 100.0

    def test_section_scores_assigned(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="삼성전자", position="SW 엔지니어")
        for section in draft.sections:
            assert 0.0 <= section.score <= 100.0

    def test_motivation_includes_company_name(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="카카오페이", position="PM")
        motivation = next(s for s in draft.sections if s.key == "motivation")
        assert "카카오페이" in motivation.content

    def test_company_insights_extracted_from_report(self):
        coach = CoverLetterCoach()
        report = {
            "sections": {
                1: {
                    "overview": "카카오는 국내 최대 모바일 플랫폼으로 성장 중.",
                    "strategy": "AI 투자와 글로벌 서비스 확대를 추진 중입니다.",
                }
            }
        }
        draft = coach.draft(company="카카오", company_report=report)
        assert len(draft.company_insights) > 0

    def test_draft_with_profile_injects_skills(self):
        coach = CoverLetterCoach()
        profile = {
            "years_of_experience": 3,
            "skills": {
                "technical": ["Python", "SQL"],
                "domain": ["핀테크"],
                "soft": ["커뮤니케이션"],
            },
            "career_assets": [{"asset": "데이터 분석", "source": "전 직장"}],
            "career_goal": "데이터 기반 PM",
        }
        draft = coach.draft(company="토스", position="PM", profile=profile)
        competency = next(s for s in draft.sections if s.key == "competency")
        assert "Python" in competency.content

    def test_strategy_notes_populated(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="라인")
        assert len(draft.strategy_notes) >= 3

    def test_to_markdown_full_output(self):
        coach = CoverLetterCoach()
        draft = coach.draft(company="쿠팡", position="물류 PM")
        md = draft.to_markdown()
        assert "쿠팡" in md
        assert "물류 PM" in md
        assert "성장과정" in md
        assert "지원동기" in md
        assert "직무역량" in md
        assert "성격의 장단점" in md
