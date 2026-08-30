# Phase 5.2D — Pre-Implementation Audit: Decision Actionability, Operational Safety & Human Oversight

## 1. Executive Summary
This audit inspects the current decision presentation, causal phrasing, risk disclosures, and human oversight mechanisms of **Signal Story (Accenture Decision Intelligence Platform)** based on findings from `docs/phase5_2c_data_gap_inspection.md`.

It establishes the technical specification for implementing:
1. **Action Safety Guardrails & Operational Risk Model** (`SAFE_TO_REVIEW`, `REQUIRES_HUMAN_APPROVAL`, risk tiers `LOW`–`CRITICAL`).
2. **Deterministic Decision Preconditions** ("Before acting" verification checklist).
3. **Causal Language Precision** (ensuring all user-facing copy uses observational and inferential phrasing rather than unfounded claims of definitive causality).
4. **Human-in-the-Loop Analyst Review State Machine** (`NOT_REVIEWED`, `REVIEWED`, `APPROVED`, `REJECTED`, `NEEDS_MORE_EVIDENCE`).

---

## 2. Baseline Codebase Inspection & Gap Findings

### A. Current Action Presentation
* In `static/app.js` and `static/index.html`, Card 4 currently displays a basic 3-line text block (`Finding:`, `Why it matters:`, `Next step:`).
* **Gap**: Lacks explicit operational risk levels, execution safety classification, prerequisites, business area assignment, and required owner approval metadata.

### B. Causal Language Audit
* **Current Phrasing**: Most backend modules in Phase 3A/3B already use gated terminology (`STRONGLY_SUPPORTED`, `PLAUSIBLE`, `NOT_ESTABLISHED`).
* **Frontend Gap**: A few UI headers, table headers, and tooltips retain legacy phrasing (e.g. "Root cause", "Causal Engine") that could invite evaluator skepticism.
* **Target Precision**: Standardize to "Primary Supported Driver", "Strongest Supported Explanation", "Evidence Indicates", and "Observed Telemetry".

### C. Operational Risk & Safety Model
* **Current State**: No machine-readable contract classifies the commercial, operational, or reputational risks of executing recommendations.
* **Target State**: Formalize `Data/semantic/decision_action_contract.json` covering all 8 driver domains.

### D. Human Oversight & Analyst Sign-off
* **Current State**: Decision UI presents recommendations without a mechanism for the business analyst to record human agreement, review, or rejection.
* **Target State**: Add interactive, non-intrusive Analyst Review Controls allowing decision sign-off (`[Approve]`, `[Mark Reviewed]`, `[Request Evidence]`, `[Reject]`) backed by session state and API endpoints.

---

## 3. Implementation Plan & Architectural Map

### Files to Create:
1. `Data/semantic/decision_action_contract.json` — Machine-readable action safety rules, risk tiers, preconditions, and owners for all 8 drivers.
2. `src/governance/decision_governance.py` — Deterministic evaluation engine mapping diagnoses to action safety, risk tiers, and preconditions.
3. `tests/test_phase5_2d_decision_governance.py` — 10+ unit tests covering risk classification, safety gates, causal language, review state transitions, and S003 regression immutability.
4. `docs/phase5_2d_implementation_report.md` — Detailed implementation documentation.

### Files to Modify:
1. `src/server.py` — Expose `GET /api/decision-governance`, `POST /api/analyst-review`, and embed `decision_governance` in `POST /api/analyze`.
2. `static/index.html` — Upgrade Card 4 into a full Decision Actionability & Safety Card with Preconditions, Operational Risks, and Analyst Review Bar.
3. `static/styles.css` — Enterprise styling for risk pills, precondition checklists, and review action buttons.
4. `static/app.js` — Dynamic data binding for decision safety, risk levels, preconditions, and analyst sign-off interactions.
5. `PROJECT_PROGRESS.md` — Milestone log update.

### Immutability Verification:
`src/analytics/`, `src/phase3b/`, `Data/Processed/`, and `Data/scenarios/` remain **100% FROZEN & UNMODIFIED**.
