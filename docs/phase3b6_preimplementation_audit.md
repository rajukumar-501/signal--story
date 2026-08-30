# Phase 3B.6 Pre-Implementation Audit — Evaluation Integrity & Live-LLM Validation Hardening

**Date:** August 30, 2026  
**Status:** COMPLETE / APPROVED FOR IMPLEMENTATION  
**Author:** Principal ML Evaluation Engineer & Software Auditor  
**Phase:** Phase 3B.6 (Evaluation Integrity & Live-LLM Validation Hardening)

---

## Executive Summary

This pre-implementation audit examines the evaluation methodology across Phase 3B.3, Phase 3B.4, and Phase 3B.5 to identify mathematical defects, rank contamination, provenance conflation, and telemetry assumptions prior to establishing the hardened Phase 3B.6 evaluation harness.

---

## Audit Findings: Detailed Answers to Core Questions A through G

### A. Ranking Calculation
- **Finding:** In `tests/test_phase3b3_benchmark.py` and `tests/test_phase3b5_live_validation.py` (lines 204–211), the calculation was:
  ```python
  if p3b_driver:
      if expected_driver:
          p3b_rank_of_expected = 1 if p3b_driver == expected_driver else p3a_rank_of_expected
          p3b_rr = 1.0 if p3b_driver == expected_driver else p3a_rr
      else:
          p3b_rank_of_expected = None
          p3b_rr = None
  else:
      p3b_rank_of_expected = None if expected_driver is None else p3a_rank_of_expected
      p3b_rr = None if expected_driver is None else p3a_rr
  ```
- **Defect Analysis:** When Phase 3B did not select the expected driver as Top 1, the code defaulted to `p3a_rank_of_expected` and `p3a_rr`. This was mathematically invalid because it reused Phase 3A's ranking instead of determining the expected driver's rank strictly from Phase 3B's candidate arbitration output.
- **Corrected Methodology:**
  1. Extract Phase 3B's ordered candidate ranking from `report.get("candidate_comparisons")` (which orders all investigated hypotheses by arbitrated score) or from `[report["diagnosis"]["driver"]]`.
  2. If `expected_driver` is in `phase3b_ranking`, set `phase3b_rank_of_expected = phase3b_ranking.index(expected_driver) + 1` and `phase3b_rr = 1.0 / phase3b_rank_of_expected`.
  3. If `expected_driver` is absent from Phase 3B's candidate ranking (or if no driver was established), set `phase3b_rank_of_expected = None` and `phase3b_rr = 0.0`.
  4. Never read, reference, or fall back to `p3a_rank_of_expected` or `p3a_rr`.

---

### B. MRR Calculation
- **Finding:** MRR was calculated as the mean of reciprocal ranks across scenarios where an expected driver exists.
- **Defect Analysis:** Because `phase3b_rr` was contaminated by Phase 3A fallback when Phase 3B did not match Top 1, the reported Phase 3B MRR was artificially tied to Phase 3A MRR.
- **Corrected Methodology:**
  $$\text{MRR}_{\text{Phase3B}} = \frac{1}{N_{\text{driver-seeking}}} \sum_{i=1}^{N_{\text{driver-seeking}}} \text{RR}_{i,\text{Phase3B}}$$
  Where $\text{RR}_{i,\text{Phase3B}} = \frac{1}{\text{rank}_{i,\text{Phase3B}}}$ if the expected driver is present in Phase 3B's ranking, and $0.0$ if absent.

---

### C. Denominator Justification
- **Finding:** The denominator is strictly **7**.
- **Verification:**
  - Scenarios S001 through S007 are **driver-seeking scenarios** with explicit ground-truth root causes (`DRIVER_04_RETURNS`, `DRIVER_06_CUSTOMER`, `DRIVER_03_MARKETING`, `DRIVER_02_PRICING`, `DRIVER_05_SUPPORT`, `DRIVER_08_PRODUCT_MIX`, `DRIVER_08_PRODUCT_MIX`).
  - Scenario S008 is an **uncertainty / macro-slowdown scenario** with `expected_established_driver = None` and `expected_status = "NOT_ESTABLISHED"`.
  - Reciprocal rank is undefined for scenarios with no expected driver. S008 must be evaluated independently for uncertainty correctness and excluded from the MRR denominator.

---

### D. Variance Measurement
- **Finding:** In Phase 3B.5, `cross_trial_variance` was assigned a constant value (`0.0`) based on the premise that `temperature = 0.0` guarantees determinism.
- **Defect Analysis:** In live LLM providers or distributed systems, identical prompts at `temperature = 0.0` can still exhibit subtle token order or formatting variance across trials. Assigning `0.0` without calculating actual output similarity violates measurement rigor.
- **Corrected Methodology:**
  Calculate actual empirical agreement across trials:
  1. `driver_agreement_rate`: Fraction of trials agreeing on the exact Top-1 driver per scenario.
  2. `status_agreement_rate`: Fraction of trials agreeing on the exact diagnosis status per scenario.
  3. `top_driver_consistency`: Percentage of scenarios with 100% agreement across all runs.
  4. `rank_stability`: Variance of expected driver ranks across trials.

---

### E. Provider Mode Separation
- **Finding:** Previous benchmarks executed `MockReasoningProvider` and labeled it under live validation contexts.
- **Corrected Methodology:**
  1. `evaluation_mode = "MOCK"`: Evaluates offline deterministic arbitration pipeline, schema contracts, and logic without network calls.
  2. `evaluation_mode = "LIVE"`: Evaluates live commercial LLM endpoints using `LLMReasoningProvider`.
  3. If live credentials (`GEMINI_API_KEY`, `OPENAI_API_KEY`) are not present in the environment, report `LIVE_EVALUATION_STATUS = "NOT_RUN"` with a clear reason. Never simulate or fabricate live API responses.

---

### F. Token Telemetry
- **Finding:** Character approximations (`len(json.dumps(payload)) // 4`) were calculated but not explicitly demarcated as estimates.
- **Corrected Methodology:**
  1. Explicitly record `estimated_input_tokens` and `estimated_output_tokens` for character-based approximations.
  2. Record `actual_input_tokens` and `actual_output_tokens` only when returned by the live provider API metadata (or set to `None`/`"UNAVAILABLE"` in mock mode).

---

### G. Latency Measurement
- **Finding:** Sub-millisecond mock execution times ($0.4\text{ ms}$) were reported without explicit distinction from network HTTP API latency.
- **Corrected Methodology:**
  1. Report `mock_latency_p50_ms` and `mock_latency_p95_ms` separately for mock execution.
  2. Report `live_latency_p50_ms` and `live_latency_p95_ms` separately for live execution.

---

## Immutability & Boundary Confirmation

| Item | Requirement | Status |
| :--- | :--- | :---: |
| **Phase 3A Code Freeze** | Zero changes to `src/analytics/` | **CONFIRMED** |
| **Canonical Datasets** | Zero changes to `Data/Processed/` | **CONFIRMED** |
| **Evaluation Inputs & Ground Truth** | Zero changes to `Data/scenarios/` | **CONFIRMED** |
| **Scenario Definitions** | S001–S008 definitions unchanged | **CONFIRMED** |
| **Frozen 3A Baseline Metrics** | Top-1: 50.0%, Top-3: 100.0%, MRR: 0.7143 | **CONFIRMED** |
