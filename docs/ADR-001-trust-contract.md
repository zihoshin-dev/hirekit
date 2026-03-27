# ADR-001: Trust Contract — Label Taxonomy and Advisory-Only Verdicts

**Status:** Accepted
**Date:** 2026-03-23
**Deciders:** HireKit core team

---

## Context

HireKit aggregates data from heterogeneous sources — DART filings, GitHub API, web scraping, LLM synthesis — to produce company analysis reports and application verdicts. These sources differ fundamentally in reliability:

- DART financial disclosures are authoritative and traceable.
- LLM-generated culture summaries are interpretive and may hallucinate.
- Scraped community posts are timely but unverified.
- Different evidence types expire at different rates, so freshness must follow explicit policy buckets rather than one fixed stale window.

Without explicit trust metadata, downstream consumers (scoring engine, UI, demo export) cannot distinguish a verified fact from a generated guess, leading to overconfident scores and misleading public demos.

---

## Decision

### 1. Six-Level Trust Label

Every `SourceResult` field carries one of six `TrustLabel` values:

| Label       | Meaning |
|-------------|---------|
| `verified`  | Directly grounded in a traceable, authoritative source with provenance URL. |
| `supporting`| Useful but weaker or partial evidence that should remain visible without being treated as verified truth. |
| `derived`   | Calculated or normalised from one or more `verified` facts (e.g., revenue growth rate). |
| `generated` | Synthesised by rule-engine or LLM; interpretive, never source-of-truth. |
| `stale`     | Underlying evidence is older than its assigned freshness policy; treat with caution. |
| `unknown`   | Unresolved: evidence missing, too weak, or contradictory. |

Labels flow **downward only** — a field may be downgraded (e.g., `verified` → `stale`) but never silently upgraded.

### 2. Advisory-Only Verdict

Application verdicts (`Go` / `Hold` / `Pass`) are explicitly **advisory only**. They are signals to help prioritise effort, not guarantees of interview, offer, or long-term fit. This constraint is encoded in the trust contract and must appear in all UI copy.

### 3. Cross-Validation Flag

`SourceResult.cross_validated = True` when two or more independent sources agree on the same data point. Scoring may weight cross-validated fields higher but must not change their `trust_label` automatically.

### 4. Freshness Policies

Freshness is policy-based, not global:

| Policy | Window |
|--------|--------|
| `job_posting` | 24 hours |
| `core_company_fact` | 7 days |
| `supporting_signal` | 30 days |

Any field older than its freshness policy is downgraded to `stale`.

### 5. Publication Boundary

Public demo exports (`publication_boundary = "public_demo"`) may include governed `verified`, `supporting`, `derived`, or `generated` fields when they are clearly labeled. Fields labelled `stale` or `unknown` must be suppressed or replaced with an explicit needs-verification placeholder.

---

## Consequences

- **All `SourceResult` instances must carry a `trust_label`.** The default is `"verified"`; sources that produce generated content must explicitly set `"generated"`.
- **Scores referencing `stale` or `unknown` fields must not be displayed** in public-facing outputs.
- **Verdict copy must always include the advisory disclaimer** ("Advisory only") — automated checks in `test_trust_contract.py` enforce this.
- **No trust label may be upgraded programmatically** without human review or a new verified source fetch.
- **Freshness windows are policy-based** (`24h / 7d / 30d`) and must remain aligned with `src/hirekit/core/trust_contract.py`.

---

## Alternatives Considered

| Alternative | Rejection reason |
|-------------|-----------------|
| Single boolean `is_verified` flag | Insufficient granularity; cannot distinguish derived from generated. |
| Confidence float only (0.0–1.0) | Continuous scale is hard to communicate to end users and hard to enforce at publication boundaries. |
| No trust metadata | Scores appear authoritative regardless of underlying data quality; unacceptable for public demo. |

---

## References

- `src/hirekit/core/trust_contract.py` — Literal types and validation helpers (stable public API)
- `src/hirekit/core/trust.py` — Enum wrappers for type-safe internal use
- `src/hirekit/sources/base.py` — `SourceResult` dataclass with `trust_label`, `evidence_id`, `cross_validated`
- `SECURE_RUNTIME_CONTRACT.md` — Publication boundary enforcement rules
