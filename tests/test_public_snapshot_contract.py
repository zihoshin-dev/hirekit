from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
META_PATH = ROOT / "docs/demo/data/meta.json"
LOG_PATH = ROOT / "docs/demo/data/update_log.json"
VERIFY_MODULE_PATH = ROOT / "tools/verify_company_data.py"


def load_meta() -> list[dict[str, object]]:
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def load_log() -> dict[str, object]:
    return json.loads(LOG_PATH.read_text(encoding="utf-8"))


def load_verify_module():
    spec = importlib.util.spec_from_file_location(
        "verify_company_data_module",
        VERIFY_MODULE_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestPublicSnapshotContract:
    def test_meta_and_update_log_counts_match(self):
        meta = load_meta()
        log = load_log()
        assert log["companies_updated"] == len(meta)

    def test_update_log_exposes_public_contract_fields(self):
        log = load_log()
        assert log["publication_boundary"] == "public_demo"
        assert isinstance(log["cross_validated"], bool)
        assert log["sources_updated"]

    def test_update_log_states_that_the_demo_is_snapshot_based(self):
        log = load_log()
        assert log["source"] == "initial_snapshot"
        assert log["sources_updated"] == ["snapshot"]
        assert log["publication_boundary"] == "public_demo"
        assert log["cross_validated"] is False

    def test_public_meta_has_minimum_company_fields(self):
        meta = load_meta()
        assert meta
        for company in meta:
            for key in ("name", "score", "grade", "description", "tech_stack", "scorecard"):
                assert key in company

    def test_public_meta_companies_have_traceable_snapshot_metadata(self):
        meta = load_meta()
        for company in meta:
            source_count = company.get("sources", 0)
            assert isinstance(source_count, int)
            assert source_count >= 1
            assert company.get("corp_name") or company.get("name")
            snapshot_meta = company.get("_meta")
            assert isinstance(snapshot_meta, dict)
            assert snapshot_meta.get("publication_boundary") == "public_demo"
            assert isinstance(snapshot_meta.get("cross_validated"), bool)
            assert snapshot_meta.get("confidence") in {"high", "medium", "low"}
            assert snapshot_meta.get("snapshot_updated_at")

    def test_governed_quality_report_uses_public_snapshot_semantics(self):
        module = load_verify_module()
        report = module.verify_companies()

        assert report["total_companies"] == report["snapshot_company_count"]
        assert report["source_file_count"] >= report["snapshot_company_count"]

        governance = report["governance"]
        assert governance["dataset_mode"] == "public_snapshot"
        assert governance["publication_boundary"] == "public_demo"
        assert governance["snapshot_source"] == "initial_snapshot"

    def test_governed_quality_report_exposes_publish_gate_contract(self):
        module = load_verify_module()
        report = module.verify_companies()

        governance = report["governance"]
        assert governance["publish_ready"] is True
        assert governance["missing_artifacts"] == []
        assert governance["required_artifacts"] == ["meta.json", "update_log.json", "quality_report.json"]
