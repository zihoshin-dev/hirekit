from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RUN_EVAL_PATH = ROOT / "tools" / "run_eval.py"


def load_run_eval_module():
    spec = importlib.util.spec_from_file_location("run_eval_module", RUN_EVAL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestReleaseEvalEntryPoint:
    def test_eval_plan_has_explicit_category_coverage(self):
        module = load_run_eval_module()
        plan = module.build_eval_plan()

        assert [step["category"] for step in plan] == ["hero", "trust", "public_copy", "snapshot", "dataset"]
        assert any("test_hero_fixtures.py" in " ".join(step["commands"][0]) for step in plan)
        assert any("test_confidence_and_grounding.py" in " ".join(step["commands"][0]) for step in plan)
        assert any("test_public_copy_contract.py" in " ".join(step["commands"][0]) for step in plan)
        assert any("test_public_snapshot_contract.py" in " ".join(step["commands"][0]) for step in plan)
        assert any("test_data_validation.py" in " ".join(step["commands"][0]) for step in plan)
        assert any("verify_company_data.py" in " ".join(command) for step in plan for command in step["commands"])

    def test_run_eval_fails_on_category_error(self, monkeypatch):
        module = load_run_eval_module()

        class DummyCompletedProcess:
            def __init__(self, returncode: int):
                self.returncode = returncode
                self.stdout = ""
                self.stderr = ""

        def fake_run(command, capture_output, text, cwd):
            if any("test_confidence_and_grounding.py" in part for part in command):
                return DummyCompletedProcess(1)
            return DummyCompletedProcess(0)

        monkeypatch.setattr(module.subprocess, "run", fake_run)

        result = module.run_eval()

        assert result["exit_code"] == 1
        assert result["categories"][0]["status"] == "passed"
        assert result["categories"][1]["status"] == "failed"
        assert result["categories"][1]["commands"][0]["returncode"] == 1
        assert result["categories"][0]["commands"][0]["command"][0] == sys.executable
