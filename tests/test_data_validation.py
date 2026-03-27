"""79개 기업 데이터 검증 및 _meta 필드 스키마 테스트."""

import importlib.util
import json
import os
import subprocess
import sys

import pytest

COMPANIES_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "demo", "data", "companies")
META_JSON = os.path.join(os.path.dirname(__file__), "..", "docs", "demo", "data", "meta.json")
VERIFY_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "tools", "verify_company_data.py")
ADD_META_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "tools", "add_meta_fields.py")
VERIFY_MODULE_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "verify_company_data.py")
FRESHNESS_MODULE_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "check_freshness.py")

META_SCHEMA_KEYS = {
    "collected_at": str,
    "verified_at": (str, type(None)),
    "confidence": float,
    "staleness_days": int,
    "cross_validated": bool,
    "version": int,
}


def get_company_files():
    companies_path = os.path.abspath(COMPANIES_DIR)
    return sorted(f for f in os.listdir(companies_path) if f.endswith(".json"))


def load_company(fname):
    path = os.path.join(os.path.abspath(COMPANIES_DIR), fname)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_verify_module():
    spec = importlib.util.spec_from_file_location(
        "verify_company_data_module",
        os.path.abspath(VERIFY_MODULE_PATH),
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_freshness_module():
    spec = importlib.util.spec_from_file_location(
        "check_freshness_module",
        os.path.abspath(FRESHNESS_MODULE_PATH),
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestVerifyScript:
    def test_verify_script_runs_without_error(self):
        """verify_company_data.py가 에러 없이 실행되는지 확인."""
        result = subprocess.run(
            [sys.executable, os.path.abspath(VERIFY_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode in (0, 1), (
            f"스크립트가 예상치 못한 코드({result.returncode})로 종료됨\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "결과 요약" in result.stdout, "출력에 결과 요약이 없음"

    def test_add_meta_script_dry_run(self):
        """add_meta_fields.py --dry-run이 에러 없이 실행되는지 확인."""
        result = subprocess.run(
            [sys.executable, os.path.abspath(ADD_META_SCRIPT), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert result.returncode == 0, (
            f"add_meta_fields --dry-run 실패\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_verify_module_detects_kakaobank_employee_inconsistency(self):
        module = load_verify_module()
        data = load_company("카카오뱅크.json")
        with open(os.path.abspath(META_JSON), encoding="utf-8") as f:
            meta = json.load(f)
        meta_record = next(company for company in meta if company.get("name") == "카카오뱅크")
        with open(
            os.path.join(os.path.dirname(__file__), "..", "docs", "demo", "data", "pension_data.json"),
            encoding="utf-8",
        ) as f:
            pension_data = json.load(f)

        issues = module.build_employee_consistency_issues(
            "카카오뱅크",
            data,
            meta_record=meta_record,
            pension_record=pension_data.get("카카오뱅크"),
        )

        issue_types = {issue["issue_type"] for issue in issues}
        assert "employee_count_inconsistency" in issue_types
        assert "employee_count_contamination_flag" in issue_types

    def test_verify_script_report_includes_subsidiary_audit(self):
        module = load_verify_module()
        report = module.verify_companies()

        assert "subsidiary_audit" in report
        assert isinstance(report["subsidiary_audit"]["issues"], list)
        assert any(
            issue.get("issue_type") == "dart_corp_name_contamination" and issue.get("company") == "카카오뱅크"
            for issue in report["issues"]
        )

    def test_verify_script_report_exposes_public_snapshot_governance(self):
        module = load_verify_module()
        report = module.verify_companies()

        assert report["total_companies"] == report["snapshot_company_count"]
        assert report["source_file_count"] >= report["snapshot_company_count"]

        governance = report["governance"]
        assert governance["dataset_mode"] == "public_snapshot"
        assert governance["publication_boundary"] == "public_demo"
        assert governance["snapshot_source"] == "initial_snapshot"
        assert governance["sources_updated"] == ["snapshot"]

    def test_publish_gate_rejects_incomplete_governed_artifacts(self):
        module = load_verify_module()

        incomplete_report = {
            "governance": {
                "dataset_mode": "public_snapshot",
                "publication_boundary": "public_demo",
                "snapshot_source": "initial_snapshot",
                "required_artifacts": ["meta.json", "update_log.json", "quality_report.json"],
                "missing_artifacts": ["quality_report.json"],
                "publish_ready": False,
            }
        }

        issues = module.build_publish_governance_issues(incomplete_report)

        assert any(issue["issue_type"] == "publish_artifact_incomplete" for issue in issues)
        assert any(issue["severity"] == "high" for issue in issues)


class TestFreshnessScriptContract:
    def test_freshness_contract_is_snapshot_based(self):
        module = load_freshness_module()
        log = module.load_update_log()
        summary = module.build_freshness_contract(log, meta_count=len(get_company_files()))

        assert summary["dataset_mode"] == "public_snapshot"
        assert summary["publication_boundary"] == "public_demo"
        assert summary["snapshot_source"] == "initial_snapshot"
        assert summary["requires_live_dataset"] is False


class TestMetaJsonConsistency:
    @pytest.mark.xfail(
        reason=(
            "비바리퍼블리카.json이 companies/에 별도 존재하지만 meta.json에는 "
            "'토스 (비바리퍼블리카)'로 통합되어 있어 1개 불일치 (80 vs 79). "
            "데이터 정합성 수정 전까지 known issue."
        ),
        strict=True,
    )
    def test_meta_json_company_count_matches_files(self):
        """meta.json 기업 수와 companies/ 디렉토리 파일 수가 일치해야 함."""
        files = get_company_files()
        with open(os.path.abspath(META_JSON), encoding="utf-8") as f:
            meta = json.load(f)
        assert len(files) == len(meta), f"companies/ 파일 수({len(files)}) != meta.json 기업 수({len(meta)})"


class TestCompanyJsonValidity:
    @pytest.mark.parametrize("fname", get_company_files())
    def test_company_json_is_valid(self, fname):
        """모든 기업 JSON이 유효한 JSON이고 필수 필드를 포함해야 함."""
        data = load_company(fname)
        assert isinstance(data, dict), f"{fname}: dict가 아님"
        for field in ("company", "region", "sections", "scorecard"):
            assert field in data, f"{fname}: 필수 필드 '{field}' 없음"

    @pytest.mark.parametrize("fname", get_company_files())
    def test_sections_keys_are_numeric(self, fname):
        """sections 키가 숫자 문자열이어야 함."""
        data = load_company(fname)
        sections = data.get("sections", {})
        for key in sections.keys():
            assert key.isdigit(), f"{fname}: sections 키 '{key}'가 숫자가 아님"

    @pytest.mark.parametrize("fname", get_company_files())
    def test_scorecard_dimension_scores_in_range(self, fname):
        """scorecard dimensions 점수가 0-5 범위여야 함."""
        data = load_company(fname)
        scorecard = data.get("scorecard", {})
        dimensions = scorecard.get("dimensions", [])
        for dim in dimensions:
            if not isinstance(dim, dict):
                continue
            score = dim.get("score")
            name = dim.get("name", "unknown")
            if score is not None:
                assert 0 <= score <= 5, f"{fname}: scorecard.{name}.score={score} out of range [0, 5]"


class TestMetaFieldSchema:
    @pytest.mark.parametrize("fname", get_company_files())
    def test_meta_field_schema_when_present(self, fname):
        """_meta 필드가 있으면 스키마를 준수해야 함."""
        data = load_company(fname)
        if "_meta" not in data:
            pytest.skip(f"{fname}: _meta 없음 (add_meta_fields.py 미실행)")

        meta = data["_meta"]
        assert isinstance(meta, dict), f"{fname}: _meta가 dict가 아님"

        for key, expected_type in META_SCHEMA_KEYS.items():
            assert key in meta, f"{fname}: _meta.{key} 없음"
            if isinstance(expected_type, tuple):
                assert isinstance(meta[key], expected_type), f"{fname}: _meta.{key} 타입 오류 (got {type(meta[key])})"
            else:
                assert isinstance(meta[key], expected_type), f"{fname}: _meta.{key} 타입 오류 (got {type(meta[key])})"

        assert 0.0 <= meta["confidence"] <= 1.0, f"{fname}: _meta.confidence={meta['confidence']} out of [0, 1]"
        assert meta["staleness_days"] >= 0, f"{fname}: _meta.staleness_days 음수"
        assert meta["version"] >= 1, f"{fname}: _meta.version < 1"
