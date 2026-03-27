# ADR: Phase-2 Private-Runtime Boundary

## Context

HireKit is undergoing a radical overhaul (T23) to prioritize a trust-first public "strategy war room" for experienced job changers. As the implementation of Phase 1 (Public Demo & Decision Support) matures, there is a risk of scope drift into features that require a private runtime, persistent user state, or authenticated workspaces.

This document explicitly defines the boundary between the Phase 1 Public Demo and the future Phase 2 Private Runtime to ensure architectural integrity and clear user expectations.

## Phase 1 Boundary (The "Public Demo-First" Scope)

### Core Philosophy
Phase 1 focuses on high-quality, evidence-backed company and role intelligence delivered through a **static, trust-visible public surface** (GitHub Pages) and a **local-only CLI/MCP environment**.

### Included in Phase 1
- **Public War Room**: A unified decision surface combining company, JD, and resume analysis (demonstrated via static snapshots in the web demo).
- **Trust Contract**: Explicit labeling of every claim (Verified, Supporting, Derived, Stale, Unknown).
- **Freshness Governance**: Automated checks and public artifacts (quality reports, update logs) for the demo corpus.
- **Explainable Strategy**: Decision-grade advice (Go/Hold/Pass) grounded in structured evidence.
- **Local Runtime**: Full analysis capabilities for private data (resumes, JDs) remain strictly local on the user's machine via CLI.

### Excluded from Phase 1 (The "Private-Runtime" Boundary)
The following are strictly reserved for Phase 2 and **must not** be implemented or promised in Phase 1 surfaces:
1. **Authenticated Workspace**: No login system, user accounts, or cloud-synced profiles.
2. **Persistent User Storage**: No cloud database for user resumes, JDs, or historical analysis reports.
3. **Auto-Apply/Automation**: No automated job applications, form-filling, or bulk outreach.
4. **Marketplace Sprawl**: No integration with job boards for direct hiring or recruitment marketplace features.
5. **Real-Time Community Tracking**: No heavy, high-frequency monitoring of social media/community feeds (Phase 1 uses point-in-time snapshots).
6. **Black-Box Predictions**: No "acceptance probability" scores or "AI-predicted" match percentages presented as deterministic truth.

## Public Boundary Rules

To enforce this boundary, all public surfaces (Landing, Demo, Tools, README) must adhere to these rules:

1. **Explicit Snapshot Labeling**: The web demo must be clearly labeled as a "Static Snapshot" or "GitHub Pages Static Demo."
2. **No "Login" CTAs**: No placeholder "Login" or "Sign Up" buttons that imply unavailable functionality.
3. **Privacy-First Messaging**: Explicitly state that private data (resumes/JDs) analyzed in the demo is **not stored** and remains processed only for the active session (or strictly local for CLI).
4. **Tool Separation**: Distinguish between the "Public Explorer" (Web) and the "Private Terminal" (CLI/Local).

## Future Responsibilities (Phase 2)
When Phase 2 begins, the following architectural shifts are expected:
- Introduction of an Identity Provider (IdP) for authenticated sessions.
- Migration from local-first storage to a secure multi-tenant cloud persistence layer.
- Implementation of secure enclave processing for private-data analysis at scale.

## Consequences
- **Implementation**: Developers must reject PRs that introduce "workspace-lite" features (e.g., local storage for multiple profiles in the web demo).
- **Marketing**: Public copy must focus on the depth and trust of intelligence, not the breadth of search automation.
- **Testing**: Regression tests (`test_public_copy_contract.py`) will explicitly check for forbidden claims (e.g., "Auto-apply," "Create Account").
