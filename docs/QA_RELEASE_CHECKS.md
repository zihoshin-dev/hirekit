# QA Release Checks

Run these checks before calling the current HireKit work production-ready.

## Python regression bundle

```bash
.venv/bin/python -m pytest tests/test_core/test_trust_contract.py -q
.venv/bin/python -m pytest tests/test_engine/test_confidence_and_grounding.py -q
.venv/bin/python -m pytest tests/test_engine/test_company_analyzer.py -q
.venv/bin/python -m pytest tests/test_engine/test_hero_fixtures.py -q
.venv/bin/python -m pytest tests/test_engine/test_jd_matcher.py tests/test_engine/test_resume_advisor.py -q
.venv/bin/python -m pytest tests/test_core/test_company_resolver.py -q
.venv/bin/python -m pytest tests/test_public_snapshot_contract.py tests/test_public_copy_contract.py -q
.venv/bin/python -m pytest tests/test_engine/test_llm_pipeline.py -q
.venv/bin/python -m pytest tests/test_cli/test_app.py tests/test_mcp_server.py -q
.venv/bin/python -m pytest tests/test_output/test_markdown.py -q
.venv/bin/python -m pytest tests/test_engine/test_career_strategy.py -q
.venv/bin/python -m pytest tests/test_engine/test_proof_of_work.py -q
.venv/bin/python tools/check_freshness.py
```

## Static-site regression bundle

```bash
npm install
npx playwright install chromium
npx playwright test tests/e2e/test_demo_war_room.spec.ts tests/e2e/test_tools_flow.spec.ts
```

## Scope guard

- Public pages must stay snapshot-only.
- `Go / Hold / Pass` must remain advisory.
- No resume/JD/private user data may be published under `docs/`.
