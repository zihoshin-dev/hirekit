from __future__ import annotations

import json
from pathlib import Path

from hirekit.core.trust_contract import TRUST_LABELS
from hirekit.engine.jd_matcher import JDMatcher
from hirekit.engine.resume_advisor import ResumeAdvisor


FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "hero-flow"


def load_manifest() -> dict[str, dict[str, str]]:
    return json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8"))


class TestHeroFixtureManifest:
    def test_manifest_points_to_existing_files(self):
        manifest = load_manifest()
        for scenario in manifest.values():
            for key in ("company_fixture", "jd_fixture", "resume_fixture"):
                assert (FIXTURE_ROOT / scenario[key]).exists()

    def test_low_signal_case_requires_conservative_future_verdict(self):
        manifest = load_manifest()
        assert manifest["low_signal_case"]["expected_future_verdict"] == "Hold"


class TestCompanyFixtures:
    def test_company_fixtures_include_traceable_source_metadata(self):
        manifest = load_manifest()
        for scenario in manifest.values():
            company_data = json.loads((FIXTURE_ROOT / scenario["company_fixture"]).read_text(encoding="utf-8"))
            assert company_data["sources"]
            for source in company_data["sources"]:
                assert source["source_name"]
                assert source["url"]
                assert source["collected_at"]
                assert source["effective_at"]
                assert source["trust_label"] in TRUST_LABELS


class TestHeroTextFixtures:
    def test_high_signal_jd_fixture_extracts_core_requirements(self):
        matcher = JDMatcher()
        jd_text = (FIXTURE_ROOT / "jd-high-signal.txt").read_text(encoding="utf-8")
        analysis = matcher.analyze(jd_source=jd_text)
        joined_skills = " ".join(analysis.required_skills).lower()
        assert "python" in joined_skills
        assert "postgresql" in joined_skills or "mysql" in joined_skills

    def test_high_signal_resume_fixture_is_reviewable(self, tmp_path: Path):
        advisor = ResumeAdvisor()
        resume_path = tmp_path / "resume-high-signal.md"
        resume_path.write_text((FIXTURE_ROOT / "resume-high-signal.md").read_text(encoding="utf-8"), encoding="utf-8")
        feedback = advisor.review(resume_path=resume_path)
        assert feedback.overall_score > 40
        assert all(section.endswith("(선택)") for section in feedback.missing_sections)

    def test_low_signal_resume_fixture_stays_sparse(self, tmp_path: Path):
        advisor = ResumeAdvisor()
        resume_path = tmp_path / "resume-low-signal.md"
        resume_path.write_text((FIXTURE_ROOT / "resume-low-signal.md").read_text(encoding="utf-8"), encoding="utf-8")
        feedback = advisor.review(resume_path=resume_path)
        assert feedback.overall_score < 60
        assert feedback.missing_sections
