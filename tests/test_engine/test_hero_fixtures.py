from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from hirekit.core.trust_contract import (
    TRUST_LABELS,
    require_publication_boundary,
    require_trust_label,
)
from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.confidence_rules import conflicting_keys, derive_confidence
from hirekit.engine.hero_verdict import compose_hero_verdict
from hirekit.engine.jd_matcher import JDAnalysis, JDMatcher
from hirekit.engine.resume_advisor import ResumeAdvisor, ResumeFeedback
from hirekit.engine.scorer import Scorecard, ScoreDimension
from hirekit.sources.base import SourceResult

FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "hero-flow"


def load_manifest() -> dict[str, dict[str, str]]:
    return cast(
        dict[str, dict[str, str]],
        json.loads((FIXTURE_ROOT / "manifest.json").read_text(encoding="utf-8")),
    )


def load_scenario(name: str) -> dict[str, str]:
    return load_manifest()[name]


def _read_json_object(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def load_company_data(name: str) -> dict[str, object]:
    scenario = load_scenario(name)
    return _read_json_object(FIXTURE_ROOT / scenario["company_fixture"])


def _source_entries(company_data: dict[str, object]) -> list[dict[str, object]]:
    raw_sources = company_data.get("sources", [])
    return cast(list[dict[str, object]], raw_sources)


def _signal_map(company_data: dict[str, object]) -> dict[str, str]:
    return cast(dict[str, str], company_data.get("signals", {}))


def to_source_results(company_data: dict[str, object]) -> list[SourceResult]:
    return [
        SourceResult(
            source_name=cast(str, source["source_name"]),
            section=cast(str, source["section"]),
            data=cast(dict[str, object], source.get("data", {})),
            collected_at=cast(str, source["collected_at"]),
            effective_at=cast(str, source.get("effective_at", "")),
            url=cast(str, source.get("url", "")),
            trust_label=require_trust_label(cast(str, source.get("trust_label", "verified"))),
            publication_boundary=require_publication_boundary(
                cast(str, source.get("publication_boundary", "internal_only"))
            ),
        )
        for source in _source_entries(company_data)
    ]


def build_report(
    scenario_name: str,
    *,
    dimension_scores: dict[str, float],
    dimension_confidences: dict[str, str],
) -> AnalysisReport:
    company_data = load_company_data(scenario_name)
    signals = _signal_map(company_data)
    sources = _source_entries(company_data)
    evidence_map = {
        "job_fit": signals["tech"],
        "career_leverage": signals["growth"],
        "growth": signals["growth"],
        "compensation": signals["compensation"],
        "culture_fit": cast(str, sources[0]["summary"]),
    }
    label_map = {
        "job_fit": "Job Fit",
        "career_leverage": "Career Leverage",
        "growth": "Growth",
        "compensation": "Compensation",
        "culture_fit": "Culture Fit",
    }
    weight_map = {
        "job_fit": 0.30,
        "career_leverage": 0.20,
        "growth": 0.20,
        "compensation": 0.15,
        "culture_fit": 0.15,
    }

    return AnalysisReport(
        company=cast(str, company_data["company"]),
        region=cast(str, company_data["region"]),
        tier=1,
        source_results=to_source_results(company_data),
        scorecard=Scorecard(
            company=cast(str, company_data["company"]),
            dimensions=[
                ScoreDimension(
                    name=name,
                    label=label_map[name],
                    weight=weight_map[name],
                    score=dimension_scores[name],
                    evidence=evidence_map[name],
                    confidence=dimension_confidences[name],
                )
                for name in (
                    "job_fit",
                    "career_leverage",
                    "growth",
                    "compensation",
                    "culture_fit",
                )
            ],
        ),
    )


class TestHeroFixtureManifest:
    def test_manifest_points_to_existing_files(self):
        manifest = load_manifest()
        for scenario in manifest.values():
            for key in ("company_fixture", "jd_fixture", "resume_fixture"):
                assert (FIXTURE_ROOT / scenario[key]).exists()

    def test_low_signal_case_requires_conservative_future_verdict(self):
        manifest = load_manifest()
        assert manifest["low_signal_case"]["expected_future_verdict"] == "Hold"

    def test_experienced_mover_and_switcher_matrix_is_present(self):
        manifest = load_manifest()
        expected = {
            "experienced_mover_strong": "Go",
            "experienced_mover_partial": "Hold",
            "experienced_mover_stale": "Hold",
            "experienced_switcher_misleading": "Hold",
            "experienced_switcher_contradictory": "Hold",
        }

        for scenario, verdict in expected.items():
            assert scenario in manifest
            assert manifest[scenario]["expected_future_verdict"] == verdict


class TestCompanyFixtures:
    def test_company_fixtures_include_traceable_source_metadata(self):
        manifest = load_manifest()
        for scenario in manifest.values():
            company_data = _read_json_object(FIXTURE_ROOT / scenario["company_fixture"])
            assert company_data["sources"]
            for source in _source_entries(company_data):
                assert source["source_name"]
                assert source["url"]
                assert source["collected_at"]
                assert source["effective_at"]
                assert source["trust_label"] in TRUST_LABELS

    def test_experienced_strong_mover_fixture_is_fresh_and_well_supported(self):
        company_data = load_company_data("experienced_mover_strong")
        sources = to_source_results(company_data)

        assert len(sources) >= 4
        assert all(not source.is_stale for source in sources)
        assert derive_confidence([source.source_name for source in sources], sources) == "high"

    def test_experienced_partial_mover_fixture_keeps_mixed_coverage(self):
        company_data = load_company_data("experienced_mover_partial")
        sources = to_source_results(company_data)

        assert any(source.is_stale for source in sources)
        assert any(source.trust_label == "verified" for source in sources)
        assert derive_confidence([source.source_name for source in sources], sources) == "medium"

    def test_experienced_stale_mover_fixture_is_all_stale(self):
        company_data = load_company_data("experienced_mover_stale")
        sources = to_source_results(company_data)

        assert sources
        assert all(source.is_stale for source in sources)
        assert derive_confidence([source.source_name for source in sources], sources) == "low"

    def test_experienced_misleading_switcher_fixture_uses_weak_public_sources(self):
        company_data = load_company_data("experienced_switcher_misleading")
        sources = to_source_results(company_data)

        assert all(source.source_name in {"company_website", "medium_velog", "naver_search"} for source in sources)
        assert all(not source.is_stale for source in sources)
        assert derive_confidence([source.source_name for source in sources], sources) == "medium"

    def test_experienced_contradictory_switcher_fixture_contains_conflicts(self):
        company_data = load_company_data("experienced_switcher_contradictory")
        sources = to_source_results(company_data)

        assert {"remote_policy"}.issubset(conflicting_keys(sources))
        assert derive_confidence([source.source_name for source in sources], sources) == "low"


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
        _ = resume_path.write_text(
            (FIXTURE_ROOT / "resume-high-signal.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        feedback = advisor.review(resume_path=resume_path)
        assert feedback.overall_score > 40
        assert all(section.endswith("(선택)") for section in feedback.missing_sections)

    def test_low_signal_resume_fixture_stays_sparse(self, tmp_path: Path):
        advisor = ResumeAdvisor()
        resume_path = tmp_path / "resume-low-signal.md"
        _ = resume_path.write_text(
            (FIXTURE_ROOT / "resume-low-signal.md").read_text(encoding="utf-8"), encoding="utf-8"
        )
        feedback = advisor.review(resume_path=resume_path)
        assert feedback.overall_score < 60
        assert feedback.missing_sections


class TestHeroVerdictRubric:
    def test_aligned_case_emits_explainable_reasons_and_next_actions(self):
        manifest = load_manifest()
        report = build_report(
            "hero_case",
            dimension_scores={
                "job_fit": 4.3,
                "career_leverage": 4.0,
                "growth": 4.2,
                "compensation": 3.8,
                "culture_fit": 3.6,
            },
            dimension_confidences={
                "job_fit": "high",
                "career_leverage": "high",
                "growth": "high",
                "compensation": "medium",
                "culture_fit": "medium",
            },
        )
        jd_analysis = JDAnalysis(
            match_score=84.0,
            strengths=["Python", "PostgreSQL", "Kubernetes"],
            gaps=["Kafka"],
        )
        resume_feedback = ResumeFeedback(
            overall_score=78.0,
            strengths=["결제 시스템 운영", "장애율 30% 감소"],
            missing_sections=[],
        )

        verdict = compose_hero_verdict(
            report=report,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
        )

        assert verdict.label == manifest["hero_case"]["expected_future_verdict"]
        assert any("근거" in reason for reason in verdict.reasons)
        assert any("적합" in reason for reason in verdict.reasons)
        assert verdict.next_actions
        assert any("지원" in action for action in verdict.next_actions)
        assert verdict.to_dict()["next_actions"] == verdict.next_actions

    def test_low_confidence_guardrail_downgrades_to_hold_with_cautions(self):
        manifest = load_manifest()
        report = build_report(
            "low_signal_case",
            dimension_scores={
                "job_fit": 4.0,
                "career_leverage": 3.8,
                "growth": 3.7,
                "compensation": 3.6,
                "culture_fit": 3.4,
            },
            dimension_confidences={
                "job_fit": "low",
                "career_leverage": "low",
                "growth": "low",
                "compensation": "low",
                "culture_fit": "low",
            },
        )
        jd_analysis = JDAnalysis(
            match_score=82.0,
            strengths=["Python", "API 개발"],
        )
        resume_feedback = ResumeFeedback(
            overall_score=76.0,
            strengths=["백엔드 운영", "자동화 경험"],
        )

        verdict = compose_hero_verdict(
            report=report,
            jd_analysis=jd_analysis,
            resume_feedback=resume_feedback,
        )

        assert verdict.label == manifest["low_signal_case"]["expected_future_verdict"]
        assert verdict.confidence == "low"
        assert verdict.cautions
        assert any("근거" in caution or "신뢰" in caution for caution in verdict.cautions)
        assert any("추가" in action or "검증" in action for action in verdict.next_actions)
