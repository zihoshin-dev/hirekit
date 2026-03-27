#!/usr/bin/env python3
"""Release-facing eval harness with explicit category scorecards."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


EVAL_CATEGORIES = [
    {
        "category": "hero",
        "label": "hero benchmark fixtures",
        "commands": [[sys.executable, "-m", "pytest", "tests/test_engine/test_hero_fixtures.py", "-q"]],
    },
    {
        "category": "trust",
        "label": "trust-critical grounding",
        "commands": [[sys.executable, "-m", "pytest", "tests/test_engine/test_confidence_and_grounding.py", "-q"]],
    },
    {
        "category": "public_copy",
        "label": "public copy contract",
        "commands": [[sys.executable, "-m", "pytest", "tests/test_public_copy_contract.py", "-q"]],
    },
    {
        "category": "snapshot",
        "label": "public snapshot contract",
        "commands": [[sys.executable, "-m", "pytest", "tests/test_public_snapshot_contract.py", "-q"]],
    },
    {
        "category": "dataset",
        "label": "dataset validation and publish gate",
        "commands": [
            [sys.executable, "-m", "pytest", "tests/test_data_validation.py", "-q"],
            [sys.executable, "tools/verify_company_data.py"],
        ],
    },
]


def build_eval_plan(selected_categories=None):
    if selected_categories is None:
        return deepcopy(EVAL_CATEGORIES)

    selected = {str(category) for category in selected_categories}
    plan = [deepcopy(step) for step in EVAL_CATEGORIES if step["category"] in selected]
    available = {str(step["category"]) for step in plan}
    missing = sorted(category for category in selected if category not in available)
    if missing:
        raise ValueError(f"unknown eval categories: {', '.join(missing)}")
    return plan


def run_command(command):
    completed = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    return {
        "command": list(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_eval(selected_categories=None):
    plan = build_eval_plan(selected_categories)
    category_results = []
    overall_passed = True

    for step in plan:
        command_results = []
        category_passed = True

        for command in step["commands"]:
            result = run_command(command)
            command_results.append(result)
            if result["returncode"] != 0:
                category_passed = False
                overall_passed = False

        category_results.append(
            {
                "category": step["category"],
                "label": step["label"],
                "status": "passed" if category_passed else "failed",
                "commands": command_results,
            }
        )

    exit_code = 0 if overall_passed else 1
    return {
        "exit_code": exit_code,
        "passed": overall_passed,
        "categories": category_results,
    }


def render_scorecard(result):
    lines = ["[eval] release scorecard"]
    for category in result["categories"]:
        lines.append(f"- {category['category']}: {category['status']}")
        for command in category["commands"]:
            lines.append(f"  command: {' '.join(command['command'])}")
            lines.append(f"  returncode: {command['returncode']}")
    lines.append(f"overall: {'passed' if result['passed'] else 'failed'}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run HireKit release eval scorecards")
    parser.add_argument("--category", action="append", dest="categories", help="limit to selected categories")
    parser.add_argument("--json", action="store_true", help="print JSON result")
    args = parser.parse_args(argv)

    result = run_eval(args.categories)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_scorecard(result))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
