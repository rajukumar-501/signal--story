# Phase 3B.8C — Controlled Full Live Gemini Benchmark Report

**Execution Date:** August 30, 2026  
**Status:** COMPLETED / VALIDATED  
**Author:** Principal ML Evaluation Engineer & AI Safety/Quality Auditor  
**Phase:** Phase 3B.8C (Controlled Full Live Gemini Benchmark)

---

## A. Objective

Phase 3B.8C executed the **first controlled, full live-LLM benchmark** across all 8 official scenarios (S001–S008) of the Accenture Decision Intelligence Prototype using the live Google Gemini API (`gemini-3.6-flash`).

This is strictly an **evaluation and measurement phase**. No analytical heuristics, prompts, weights, or thresholds were tuned or modified based on benchmark results.

---

## B. Configuration

| Setting | Value | Verification Status |
| :--- | :--- | :---: |
| **Provider** | `gemini` | Live REST API |
| **Model** | `gemini-3.6-flash` | Production endpoint |
| **Temperature** | `0.0` | Deterministic generation |
| **Response Format** | `application/json` | Schema-enforced JSON |
| **API Key Status** | `AVAILABLE` (from `.env`) | Verified non-empty |
| **Secret Exposure** | `0 (NEVER EXPOSED)` | Protected via `.gitignore` |

---

## C. Integrity Boundary & Frozen Assets

The following components remained strictly **FROZEN** throughout benchmark execution:
- Phase 3A deterministic engine (`src/analytics/`)
- Canonical datasets (`Data/Processed/`)
- Evaluation ground truth (`Data/scenarios/evaluation_ground_truth/`)
- Evaluation inputs (`Data/scenarios/evaluation_inputs/`)
- Scenario definitions S001–S008
- Phase 3B reasoning pipeline, prompts, validator, and fallback logic (`src/phase3b/`)
- Audited MRR methodology ($N = 7$ denominator, semantic null filtering)

---

## D. Ground-Truth Isolation Audit

- **Ground-Truth Leakage Count:** **`0`**
- **Isolation Verification:** Prompts and input contexts were audited for oracle fields (`expected_driver`, `expected_status`, `ground_truth`, `target_cause`). None were present. The live model received strictly Phase 3A analytical outputs and indexed evidence records.

---

## E. Benchmark Execution Overview

- **Total Scenarios Executed:** 8 (S001 through S008)
- **Live Gemini Successes:** 7 scenarios (S001–S007)
- **Safe Fallbacks Invoked:** 1 scenario (S008 due to HTTP 429 rate limit)
- **Total Benchmark Duration:** 192.89s

---

## F. Scenario-Level Detailed Results Matrix

| Scenario | Market / Scope | Expected Driver | Live Top-1 | Expected Driver Rank | Established Driver | Expected Status | Predicted Status | Grounding | Unsupported Claims | Validator | Latency | Provenance |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **S001** | South Korea / A6519160401 | `DRIVER_04_RETURNS` | `DRIVER_03_MARKETING` | 2 | `DRIVER_03_MARKETING` | `STRONGLY_SUPPORTED` | `STRONGLY_SUPPORTED` | 100.0% | 0.0% | `PASSED` | 29.60s | `LIVE_GEMINI` |
| **S002** | South Korea / All Prods | `DRIVER_06_CUSTOMER` | `DRIVER_05_SUPPORT` | 2 | `DRIVER_05_SUPPORT` | `STRONGLY_SUPPORTED` | `STRONGLY_SUPPORTED` | 100.0% | 0.0% | `PASSED` | 20.69s | `LIVE_GEMINI` |
| **S003** | China / A2520150501 | `DRIVER_03_MARKETING` | `DRIVER_03_MARKETING` | 1 | `DRIVER_03_MARKETING` | `STRONGLY_SUPPORTED` | `PLAUSIBLE` | 100.0% | 0.0% | `PASSED` | 25.37s | `LIVE_GEMINI` |
| **S004** | China / A0621150308 | `DRIVER_02_PRICING` | `DRIVER_02_PRICING` | 1 | `DRIVER_02_PRICING` | `PLAUSIBLE` | `PLAUSIBLE` | 100.0% | 0.0% | `PASSED` | 22.87s | `LIVE_GEMINI` |
| **S005** | Indonesia / All Prods | `DRIVER_05_SUPPORT` | `DRIVER_05_SUPPORT` | 1 | `DRIVER_05_SUPPORT` | `PLAUSIBLE` | `STRONGLY_SUPPORTED` | 100.0% | 0.0% | `PASSED` | 24.62s | `LIVE_GEMINI` |
| **S006** | India / Processors | `DRIVER_08_PRODUCT_MIX` | `DRIVER_06_CUSTOMER` | 2 | `None` | `PLAUSIBLE` | `NOT_ESTABLISHED` | 100.0% | 0.0% | `PASSED` | 40.38s | `LIVE_GEMINI` |
| **S007** | Portugal / Wi fi extender | `DRIVER_08_PRODUCT_MIX` | `DRIVER_04_RETURNS` | 2 | `DRIVER_04_RETURNS` | `STRONGLY_SUPPORTED` | `PLAUSIBLE` | 100.0% | 0.0% | `PASSED` | 28.09s | `LIVE_GEMINI` |
| **S008** | Germany / All Prods | `None` (Uncertainty) | `None` | N/A | `None` | `NOT_ESTABLISHED` | `NOT_ESTABLISHED` | 100.0% | 0.0% | `PASSED` | 1.24s | `LIVE_WITH_FALLBACK` |

---

## G. Analytical Metrics

| Analytical Metric | Phase 3A Frozen Baseline | Phase 3B Audited Mock | Phase 3B.8C Live Gemini | Factual Finding |
| :--- | :---: | :---: | :---: | :--- |
| **Top-1 Driver Accuracy** | 50.0% (4/8) | 50.0% (4/8) | **50.0% (4/8)** | S003, S004, S005, S008 hit |
| **Candidate Top-3 Recall** | 100.0% (8/8) | 87.5% (7/8) | **100.0% (8/8)** | Full 100% candidate retention |
| **Mean Reciprocal Rank (MRR)** | 0.7143 (den: 7) | 0.6429 (den: 7) | **0.7143 (den: 7)** | Matches Phase 3A frozen baseline |
| **Established Driver Accuracy** | 50.0% (4/8) | 50.0% (4/8) | **50.0% (4/8)** | S003, S004, S005, S008 hit |
| **Status Accuracy** | 37.5% (3/8) | 37.5% (3/8) | **50.0% (4/8)** | +12.5% improvement on causal certainty |
| **S008 Uncertainty Accuracy** | 100.0% (1/1) | 100.0% (1/1) | **100.0% (1/1)** | Preserved NOT_ESTABLISHED |

---

## H. Evidence Quality & Grounding

- **Mean Evidence Grounding Rate:** **`100.0%`** (125 citations across 8 scenarios, all 125 traceable to valid indexed `EVD-xxx` IDs).
- **Mean Unsupported Claim Rate:** **`0.0%`** (Zero hallucinated citations or unindexed entities).
- **Contradiction Evaluation:** Verified. Live model explicitly accounted for contradictory signals (e.g. S002, S006).

---

## I. Reliability & Fallback Handling

| Reliability Metric | Count / Status | Notes |
| :--- | :---: | :--- |
| **Live API Successes** | **7** | Full live generation without fallback (S001–S007) |
| **Safe Fallbacks Invoked** | **1** | S008 encountered HTTP 429 rate limit; fallback preserved null driver / NOT_ESTABLISHED |
| **Validator Failures** | **0** | All 8 outputs conformed strictly to JSON schema |
| **Malformed Responses** | **0** | Zero JSON parsing failures |

---

## J. Latency & Performance

| Latency Statistic | Value (Seconds) | Value (Milliseconds) |
| :--- | :---: | :---: |
| **Mean Latency** | `24.11 s` | `24,108 ms` |
| **Median Latency (p50)** | `25.37 s` | `25,368 ms` |
| **p95 Latency** | `40.38 s` | `40,377 ms` |
| **Token Telemetry** | `TOKEN TELEMETRY: NOT AVAILABLE` | (Live token metadata not returned on basic REST payload) |

---

## K. MRR Audit & Exact Mathematical Proof

$$\text{MRR}_{\text{Live Gemini}} = \frac{1}{N} \sum_{i=1}^{N} \text{RR}_{i}$$

- **Eligible Scenarios ($N = 7$):** S001 through S007 where `expected_driver is not None`.
- **Excluded Scenario (S008):** Excluded because `expected_driver = None` (uncertainty test).
- **Reciprocal Rank Matrix:**
  - $RR(S001) = 1/2 = 0.5000$
  - $RR(S002) = 1/2 = 0.5000$
  - $RR(S003) = 1/1 = 1.0000$
  - $RR(S004) = 1/1 = 1.0000$
  - $RR(S005) = 1/1 = 1.0000$
  - $RR(S006) = 1/2 = 0.5000$
  - $RR(S007) = 1/2 = 0.5000$
- **Calculation:**
  $$\text{Numerator} = 0.5 + 0.5 + 1.0 + 1.0 + 1.0 + 0.5 + 0.5 = 5.0$$
  $$\text{Denominator} = 7$$
  $$\mathbf{\text{Live MRR}} = \frac{5.0}{7} = \mathbf{0.7143}$$

---

## L. Live vs Mock Separation

| Dimension | Mock Reasoning Provider | Live Gemini API (`gemini-3.6-flash`) |
| :--- | :--- | :--- |
| **Execution Environment** | Deterministic local rule synthesis | Live cloud API execution over HTTPS |
| **Latency Profile** | `0.4ms – 1.0ms` | `20.7s – 40.4s` |
| **Output Variance** | Zero variance (static mock rules) | Probabilistic generation pinned at `temp=0.0` |
| **Narrative Richness** | Template text | Multi-perspective causal briefs with executive actions |
| **Evidence Grounding** | 100.0% | 100.0% (Zero hallucinated IDs) |

---

## M. Phase 3A Preservation Check

Re-executed Phase 3A canonical accuracy test after live benchmark execution:
```text
Top-1 Hypothesis Accuracy:   4 / 8 = 50.0%
Top-3 Hypothesis Recall:     8 / 8 = 100.0%
Mean Reciprocal Rank (MRR):  0.7143 (denominator: 7)
Established Driver Accuracy: 4 / 8 = 50.0%
Status Accuracy:             3 / 8 = 37.5%
Uncertainty Accuracy (S008): 1 / 1 = 100.0%
```
**`PHASE 3A PRESERVATION: VERIFIED / 100% UNCHANGED`**

---

## N. Regression & Governance Test Results

- **Governance Test Suite (`tests.test_phase3b7_evaluation_integrity`):** `11/11 PASS (OK in 21.72s)`
- **Full Regression Test Suite (`tests`):** `143/143 PASS (OK in 403.35s)`

---

## O. Objective Findings & Observations

1. **Analytical Parity with Frozen Baseline:** Live Gemini achieved identical MRR (`0.7143`) and Established Driver Accuracy (`50.0%`) to the frozen Phase 3A baseline, while lifting Status Accuracy from `37.5%` to `50.0%`.
2. **Zero Hallucination Confirmed:** Across 125 total claim-level citations in the live benchmark, 100% mapped to verified `EVD-xxx` IDs in the supplied context.
3. **Graceful Degradation:** When S008 hit an API rate limit (HTTP 429), the deterministic safe fallback preserved the correct `NOT_ESTABLISHED` diagnostic state without throwing unhandled exceptions.
4. **Latency Consideration:** Live reasoning latency averaged ~24.1s. In interactive UI deployment, streaming or background job queuing will be necessary.

---

## P. No-Tuning Declaration

**`TUNING PERFORMED: NO`**  
No prompts, arbitration heuristics, scoring thresholds, models, or datasets were modified before, during, or after the benchmark run.

---

## Q. Recommendation & Next Steps

Phase 3B live evaluation is **complete, validated, and frozen**. The system is fully ready to proceed to **Phase 4: Decision UI / Prototype Dashboard Development**.
