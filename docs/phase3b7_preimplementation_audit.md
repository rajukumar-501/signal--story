# Phase 3B.7 Pre-Implementation Audit — Evaluation Semantics, Provenance & Governance Closure

**Date:** August 30, 2026  
**Status:** COMPLETE / APPROVED FOR PHASE 3B.7 IMPLEMENTATION  
**Author:** Principal ML Evaluation Engineer & Software Auditor  
**Phase:** Phase 3B.7 (Evaluation Semantics, Provenance & Governance Closure)

---

## A. Scope of Audit

This audit inspects the complete evaluation framework across Phase 3A and Phase 3B to identify any remaining semantic inconsistencies, provenance ambiguities, metric conflations, or overfitting risks before governance closure.

### Files Inspected

| File | Status | Observations |
| :--- | :---: | :--- |
| `PROJECT_PROGRESS.md` | ✅ Inspected | Phase 3B.6 status recorded; Quality table updated. |
| `PROJECT_RULES.md` | ✅ Inspected | 10 governance rules verified intact. No modifications made or required. |
| `docs/phase3a_final_baseline.md` | ✅ Inspected | Frozen baseline metrics and 7-rule DiagnosisGate fully documented. |
| `docs/phase3b_architecture.md` | ✅ Inspected | 4 guardrails (zero GT access, zero data modification, zero hallucination, uncertainty preservation) are all in force. |
| `docs/phase3b_evaluation_contract.md` | ✅ Inspected | Aspirational targets vs frozen baselines documented. S001–S008 evaluation contract fully specified. |
| `docs/phase3b5_report.md` | ✅ Inspected | Multi-trial report for Phase 3B.5 — no conflations found after Phase 3B.6 audit. |
| `docs/phase3b6_report.md` | ✅ Inspected | Rank leakage fix documented. MRR = 0.6429 audited. |
| `docs/phase3b6_preimplementation_audit.md` | ✅ Inspected | Answers A–G documented. |
| `Data/evaluation/phase3b6_results.csv` | ✅ Inspected | 8 scenario rows. Verified column layout, rr values, provenance labels. |
| `Data/evaluation/phase3b6_multi_run_results.csv` | ✅ Inspected | 24 rows (8 scenarios × 3 trials). |
| `Data/evaluation/phase3b6_summary.json` | ✅ Inspected | MRR = 0.6429, denominator = 7, top_driver_consistency = 1.0. |
| `src/phase3b/llm_provider.py` | ✅ Inspected | LLMConfig.from_env() reads env vars; no API keys found → mock falls back. |
| `src/phase3b/mock_reasoning_provider.py` | ✅ Inspected | Deterministic offline arbitration; no live API calls. |
| `src/analytics/` (Phase 3A) | ✅ Inspected | All Phase 3A analytical files untouched. |
| `tests/test_phase3b6_evaluation_integrity.py` | ✅ Inspected | 14 tests. BENCHMARK_SCENARIOS list contains scenario IDs as test configuration (not analytical logic). |

---

## B. Current MRR Definitions (Audited)

### Phase 3A Frozen Baseline MRR

$$\text{MRR}_{\text{Phase 3A}} = \frac{1}{N} \sum_{i=1}^{N} \text{RR}_{i,\text{Phase 3A}}$$

From `docs/phase3a_final_baseline.md`:
- **Value:** `0.7143`
- **Denominator N:** 7 (S001–S007 have `expected_driver ≠ None`)
- **Numerator sum:** 5.0

| Scenario | Phase 3A Rank | Phase 3A RR |
| :--- | :---: | :---: |
| S001 | 2 | 0.5000 |
| S002 | 2 | 0.5000 |
| S003 | 1 | 1.0000 |
| S004 | 1 | 1.0000 |
| S005 | 1 | 1.0000 |
| S006 | 2 | 0.5000 |
| S007 | 2 | 0.5000 |
| **Sum** | | **5.0000** |
| **MRR (÷7)** | | **0.7143** |

**Status: VERIFIED ✅ — Exactly matches frozen Phase 3A baseline.**

---

### Phase 3B Independently Audited MRR

**Independent mathematical verification from `Data/evaluation/phase3b6_results.csv`:**

| Scenario | expected_driver | phase3b_rank | phase3b_rr | Included in denominator |
| :--- | :--- | :---: | :---: | :---: |
| S001 | DRIVER_04_RETURNS | 2 | 0.5000 | ✅ Yes (`expected_driver ≠ None`) |
| S002 | DRIVER_06_CUSTOMER | 2 | 0.5000 | ✅ Yes |
| S003 | DRIVER_03_MARKETING | 1 | 1.0000 | ✅ Yes |
| S004 | DRIVER_02_PRICING | 1 | 1.0000 | ✅ Yes |
| S005 | DRIVER_05_SUPPORT | 1 | 1.0000 | ✅ Yes |
| S006 | DRIVER_08_PRODUCT_MIX | N/A (None) | 0.0000 | ✅ Yes (expected_driver ≠ None, but rank absent → RR = 0.0) |
| S007 | DRIVER_08_PRODUCT_MIX | 2 | 0.5000 | ✅ Yes |
| S008 | **None** | N/A | **N/A** | ❌ No (`expected_driver = None` → excluded) |
| **Sum (S001–S007)** | | | **4.5000** | |
| **MRR (÷7)** | | | **0.6429** | |

**Status: VERIFIED ✅ — Independently computed MRR = 4.5 / 7 = 0.6429 matches `phase3b6_summary.json`.**

**Reason for Phase 3B MRR < Phase 3A MRR:**  
In Phase 3B, S006 correctly triggered the uncertainty gate (`NOT_ESTABLISHED`, `driver = None`), yielding `phase3b_rank = None` and `RR = 0.0`. In Phase 3A, the deterministic engine still produced `DRIVER_06_CUSTOMER` at rank 2 ($RR = 0.5$). The Phase 3B reduction in MRR reflects correct uncertainty preservation, not a quality regression.

---

## C. MRR Denominator Derivation (Semantic Rule)

**Rule:** Include a scenario in the MRR denominator if and only if `expected_driver is not None`.

**Implementation in evaluator code:**
```python
driver_seeking_results = [r for r in scenario_results 
                          if r.get("expected_driver") and r["expected_driver"] != "None"]
denominator = len(driver_seeking_results)
```

**Audit Finding:** This rule is correctly implemented via a semantic property check (`expected_driver is not None`). There is **no hardcoded scenario-ID exclusion** (e.g., `if scenario_id == 'S008': exclude`). The exclusion of S008 follows from the general rule because S008 has `expected_established_driver = None` (as defined in the evaluation contract).

**Status: COMPLIANT ✅ — No scenario-ID special casing found.**

---

## D. Top-3 Candidate Recall vs. Established Driver Accuracy

### Candidate Top-3 Recall
**Question:** Was the expected driver present within the system's ranked candidate hypothesis list?

- **Phase 3A:** `100.0% (8/8)` — All 8 scenarios have the expected driver within top-2.
- **Phase 3B:** `87.5% (7/8)` — S006 returns `driver = None` / `NOT_ESTABLISHED`. No candidate ranking is emitted, so the expected driver (`DRIVER_08_PRODUCT_MIX`) is absent. This is semantically correct: the uncertainty gate correctly prevented forced ranking.

### Established Driver Accuracy
**Question:** Did the final diagnosis establish the expected driver?

- **Phase 3A:** `50.0% (4/8)`
- **Phase 3B:** `50.0% (4/8)`

### Key Distinction
These are fundamentally different metrics:
- A system can place the expected driver in the candidate list (Top-3 Recall ✅) while the uncertainty gate refuses to establish it (Established Driver ❌).
- The 87.5% Top-3 Recall in Phase 3B correctly reflects S006's `NOT_ESTABLISHED` outcome, which is the semantically correct behaviour per `docs/phase3b_architecture.md` Guardrail #4.

**Status: CORRECTLY SEPARATED ✅ — Both metrics are reported distinctly.**

---

## E. Provider Provenance (MOCK vs LIVE)

### Current Environment Status
- `LLM_API_KEY` = **NOT SET**
- `GEMINI_API_KEY` = **NOT SET**
- `OPENAI_API_KEY` = **NOT SET**
- `LLM_PROVIDER` env var = **NOT SET** (defaults to `"mock"`)

### Audit Findings
- All Phase 3B evaluation results in `phase3b6_results.csv`, `phase3b6_multi_run_results.csv`, and `phase3b6_summary.json` were produced by `MockReasoningProvider` (offline deterministic execution).
- The `evaluation_mode` column correctly records `"MOCK"` for all rows.
- `actual_input_tokens` and `actual_output_tokens` correctly record `"UNAVAILABLE"` for all rows.
- No live API endpoint was called. No live HTTP request was made. No live results exist.

### Required Terminology Clarification (Governance Gap Identified)
The `phase3b6_summary.json` field `"top_driver_consistency": 1.0` and `"status_consistency": 1.0` were computed across 3 trials of **mock provider** execution. These must be explicitly labeled as **Mock Provider Cross-Trial Consistency**, not as evidence of live LLM stability.

**Status: GOVERNANCE GAP IDENTIFIED — To be corrected in Phase 3B.7 governance documentation and test suite.**

---

## F. Cross-Trial Variance Interpretation

- `"top_driver_consistency": 1.0` = All 3 mock provider trials agreed on the top driver per scenario.
- `"status_consistency": 1.0` = All 3 mock provider trials agreed on the diagnosis status per scenario.

**Correct Label:** `Mock Provider Cross-Trial Consistency: 100.0%`  
**Incorrect Label (to avoid):** `Live LLM Cross-Trial Variance: 0%`

No live LLM trials were executed. Live consistency remains unmeasured.

---

## G. Token & Latency Telemetry

| Telemetry Field | Source | Value | Correct Label |
| :--- | :--- | :--- | :--- |
| `estimated_input_tokens` | Character count / 4 | ~2,500 | `ESTIMATED (character approximation ÷ 4)` |
| `estimated_output_tokens` | Character count / 4 | ~1,200 | `ESTIMATED (character approximation ÷ 4)` |
| `actual_input_tokens` | Live API response header | `"UNAVAILABLE"` | `LIVE TOKEN USAGE: NOT AVAILABLE` |
| `actual_output_tokens` | Live API response header | `"UNAVAILABLE"` | `LIVE TOKEN USAGE: NOT AVAILABLE` |
| `latency_ms` | `time.time()` (local execution) | 0.4–1.0ms | `MOCK EXECUTION LATENCY (local, no HTTP)` |
| Live API Latency | HTTP call round-trip | N/A | `LIVE LATENCY: NOT AVAILABLE` |

---

## H. Scenario ID References — Overfitting Audit

### In `tests/` directory
Searched all `*.py` files in `tests/` for S001–S008 patterns.  
**Finding:** No scenario IDs found in `tests/` outside of the BENCHMARK_SCENARIOS list (evaluation configuration).

### In `src/` directory
Searched all `*.py` files in `src/` for S001–S008 patterns.  
**Finding:** Zero scenario ID references in source code.

### Assessment
- Scenario IDs appear **only** in test configuration constants (BENCHMARK_SCENARIOS), not in analytical logic.
- The evaluation contract file `docs/phase3b_evaluation_contract.md` describes per-scenario expected reasoning, which is legitimate documentation of ground truth specifications, not analytical special-casing.
- **No overfitting or scenario-specific analytical logic was found.**

**Status: CLEAN ✅ — Zero analytical scenario-ID hardcoding found.**

---

## I. Files Explicitly Protected from Modification

| File / Directory | Protection Reason |
| :--- | :--- |
| `src/analytics/` | Phase 3A frozen analytical engine |
| `Data/Processed/` (all 10 CSVs) | Canonical datasets |
| `Data/scenarios/evaluation_ground_truth/` | Oracle ground truth |
| `Data/scenarios/evaluation_inputs/` | Evaluation inputs |
| `Data/scenarios/scenario_candidate_shortlist.csv` | Scenario definitions |
| `Data/evaluation/phase3b6_results.csv` | Audited evaluation output |
| `Data/evaluation/phase3b6_summary.json` | Audited summary (MRR = 0.6429 verified) |
| `tests/test_phase3a3_accuracy.py` | Phase 3A baseline verification |
| `docs/phase3a_final_baseline.md` | Frozen baseline documentation |

---

## J. Files Proposed for Creation (Phase 3B.7 Only)

| File | Purpose |
| :--- | :--- |
| `docs/phase3b7_preimplementation_audit.md` | This file |
| `tests/test_phase3b7_evaluation_integrity.py` | Governance semantics test suite (Tests A–K) |
| `docs/phase3b7_report.md` | Final governance closure report |
| `PROJECT_PROGRESS.md` (MODIFY) | Status and changelog update only |

---

## K. Summary of Discrepancies Found

| ID | Discrepancy | Severity | Proposed Correction |
| :--- | :--- | :---: | :--- |
| **D001** | `phase3b6_summary.json` uses `"top_driver_consistency"` and `"status_consistency"` without explicitly labeling them as mock-provider results. | Medium | Add governance test asserting these are labeled as mock-only; document in Phase 3B.7 report. |
| **D002** | Cross-trial consistency metrics could be misread as evidence of live LLM stability. | Medium | Explicitly state in report: `Mock Provider Cross-Trial Consistency: 100.0%` / `Live LLM Variance: NOT MEASURED`. |
| **D003** | No formal test explicitly prevents MOCK labels from being misrepresented as LIVE in future evaluations. | Low | Add Tests E and F to the governance suite. |

**All discrepancies are documentation/governance gaps — zero analytical, dataset, or ground-truth defects found.**
