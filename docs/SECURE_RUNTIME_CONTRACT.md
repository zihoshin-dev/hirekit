# Secure Runtime Contract

HireKit has three different execution/publication boundaries and they must never be confused.

## 1. `public_demo`

- Surface: `docs/`, GitHub Pages, static snapshot JSON under `docs/demo/data/`
- Allowed data: publication-safe company snapshots, trust labels, freshness metadata, scorecards, public-source summaries
- Forbidden data: resumes, JD text pasted by users, personal notes, application history, private comparisons
- Promise: useful public preview only, never a private personalized runtime

## 2. `internal_only`

- Surface: local CLI, local MCP calls, development, QA, release checks
- Allowed data: richer analysis payloads, internal diagnostics, operator review outputs
- Forbidden data: publishing these payloads directly to `docs/` without explicit public filtering
- Promise: trust-aware local analysis, still advisory-only

## 3. `private_user`

- Surface: future authenticated runtime only
- Allowed data: resumes, JD text, application notes, private work history, saved campaigns
- Forbidden data: GitHub Pages, public snapshots, static-site assets
- Promise: private workflows must stay outside the current public demo architecture

## Verdict Contract

- `Go / Hold / Pass` is advisory only
- Verdicts must include confidence and supporting reasons
- Verdicts do not guarantee interviews, offers, or long-term fit

## Current Scope

- Current repo ships `public_demo` and `internal_only`
- `private_user` is documented for future architecture, not implemented in the static demo
