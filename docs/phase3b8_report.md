# Phase 3B.8 — Controlled Live Gemini Evaluation Report

**Execution Date:** August 30, 2026  
**Status:** COMPLETED / VALIDATED  
**Author:** Principal ML Evaluation Engineer & AI Safety/Quality Auditor  
**Phase:** Phase 3B.8 (Controlled Live Gemini Evaluation)

---

## 1. Executive Summary

Phase 3B.8 executed the **first controlled live-LLM evaluation** of the Accenture Decision Intelligence Prototype using the live Google Gemini API.

The entire analytical backend (Phase 3A deterministic engine, candidate generators, diagnosis gate, canonical datasets, ground truth, evaluation inputs, Phase 3B input adapter, evidence context, prompts, validator, and safe fallback) was kept **100% FROZEN** without any scenario-specific tuning or code modifications.

### Key Evaluation Findings
- **Live Provider Execution:** 8/8 official scenarios evaluated live against Google Gemini.
- **Provenance Breakdown:** 6 scenarios succeeded with `LIVE_GEMINI` reasoning; 2 scenarios safely triggered `DETERMINISTIC_FALLBACK` (S004 due to network read timeout, S006 due to response schema validation gating). Zero mock execution was used.
- **Ranking Quality (MRR):** Live Gemini achieved an audited **MRR of 0.7857** (numerator: 5.5, denominator: 7), improving upon the frozen Phase 3A baseline (`0.7143`).
- **Established Driver Accuracy:** **62.5% (5/8)**, compared to Phase 3A's `50.0% (4/8)`. Live Gemini correctly elevated `DRIVER_04_RETURNS` to Rank 1 on scenario S001 based on qualitative defect returns evidence in CRM logs.
- **Candidate Top-3 Recall:** **100.0% (8/8)**.
- **Uncertainty Preservation (S008):** **100.0% (1/1)**. Live Gemini correctly outputted `NOT_ESTABLISHED` and `established_driver = null` without forcing a false positive driver.
- **Evidence Grounding Rate:** **100.0%** (zero hallucinated evidence IDs).
- **Unsupported Claim Rate:** **0.0%** (zero unverified factual claims).

---

## 2. Pre-Live Baseline Verification

Prior to live execution, the frozen Phase 3A deterministic baseline was executed and verified live:

```text
Top-1 Hypothesis Accuracy:   4 / 8 = 50.0%
Top-3 Hypothesis Recall:     8 / 8 = 100.0%
Mean Reciprocal Rank (MRR):  0.7143 (denominator: 7)
Established Driver Accuracy: 4 / 8 = 50.0%
Status Accuracy:             3 / 8 = 37.5%
Uncertainty Accuracy (S008): 1 / 1 = 100.0%
```

**Discrepancies:** `0`. Baseline is 100% intact.

---

## 3. Provider & Model Configuration

- **Provider:** `Google Gemini REST API` (Live Endpoint)
- **Model Identifier:** `gemini-3.6-flash`
- **Temperature:** `0.0` (pinned deterministic generation)
- **Response Format:** `application/json` (structured object)
- **API Key Configured:** `YES` (loaded safely from `.env`, never printed or logged)
- **Secret Protection:** Protected via `.gitignore` (`.env`, `.env.*`, `!.env.example`)

> [!NOTE]
> **Model Availability Note:** The default placeholder identifier `gemini-1.5-flash` is discontinued on v1beta Generative Language API endpoints. Google's API returned HTTP 404 with instruction: `"Please update your code to use models/gemini-3.6-flash for the latest features and improvements."` `gemini-3.6-flash` was utilized as the active production live reasoning model.

---

## 4. Comparative Evaluation: Frozen Phase 3A vs Phase 3B.8 Live Gemini

| Evaluation Metric | Phase 3A Frozen Baseline | Phase 3B Audited Mock | Phase 3B.8 Live Gemini | Live Impact / Lift |
| :--- | :---: | :---: | :---: | :---: |
| **Top-1 Driver Accuracy** | 50.0% (4/8) | 50.0% (4/8) | **62.5% (5/8)** | **+12.5%** (S001 resolved) |
| **Candidate Top-3 Recall** | 100.0% (8/8) | 87.5% (7/8) | **100.0% (8/8)** | **Preserved 100% coverage** |
| **Mean Reciprocal Rank (MRR)** | 0.7143 (den: 7) | 0.6429 (den: 7) | **0.7857 (den: 7)** | **+0.0714 vs 3A (+0.1428 vs Mock)** |
| **Established Driver Accuracy** | 50.0% (4/8) | 50.0% (4/8) | **62.5% (5/8)** | **+12.5%** |
| **Status Accuracy** | 37.5% (3/8) | 37.5% (3/8) | **50.0% (4/8)** | **+12.5%** |
| **S008 Uncertainty Accuracy** | 100.0% (1/1) | 100.0% (1/1) | **100.0% (1/1)** | **100% Maintained** |
| **Evidence Grounding Rate** | 100.0% | 100.0% | **100.0%** | **Zero Hallucination** |
| **Unsupported Claim Rate** | 0.0% | 0.0% | **0.0%** | **Zero Unsupported Claims** |

---

## 5. Scenario-by-Scenario Detailed Results Matrix

| Scenario | Market / Scope | Expected Driver | Phase 3A Rank (RR) | Phase 3B.8 Live Rank (RR) | Established Driver | Overall Status | Provenance | Latency | Result |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: |
| **S001** | South Korea / A6519160401 | `DRIVER_04_RETURNS` | 2 (0.5000) | **1 (1.0000)** | `DRIVER_04_RETURNS` | `PLAUSIBLE` | `LIVE_GEMINI` | 29.2s | **Hit (+1.0)** |
| **S002** | South Korea / All Prods | `DRIVER_06_CUSTOMER` | 2 (0.5000) | 2 (0.5000) | `DRIVER_05_SUPPORT` | `STRONGLY_SUPPORTED` | `LIVE_GEMINI` | 32.1s | Miss (Rank 2) |
| **S003** | China / A2520150501 | `DRIVER_03_MARKETING` | 1 (1.0000) | 1 (1.0000) | `DRIVER_03_MARKETING` | `PLAUSIBLE` | `LIVE_GEMINI` | 31.1s | **Hit (1.0)** |
| **S004** | China / A0621150308 | `DRIVER_02_PRICING` | 1 (1.0000) | 1 (1.0000) | `DRIVER_02_PRICING` | `PLAUSIBLE` | `DETERMINISTIC_FALLBACK` | 45.2s | **Hit (Fallback)** |
| **S005** | Indonesia / All Prods | `DRIVER_05_SUPPORT` | 1 (1.0000) | 1 (1.0000) | `DRIVER_05_SUPPORT` | `STRONGLY_SUPPORTED` | `LIVE_GEMINI` | 24.1s | **Hit (1.0)** |
| **S006** | India / Processors | `DRIVER_08_PRODUCT_MIX` | 2 (0.5000) | 2 (0.5000) | `DRIVER_06_CUSTOMER` | `PLAUSIBLE` | `DETERMINISTIC_FALLBACK` | 29.0s | Miss (Fallback) |
| **S007** | Portugal / Wi fi extender | `DRIVER_08_PRODUCT_MIX` | 2 (0.5000) | 2 (0.5000) | `DRIVER_04_RETURNS` | `PLAUSIBLE` | `LIVE_GEMINI` | 30.0s | Miss (Rank 2) |
| **S008** | Germany / All Prods | `None` (Uncertainty) | N/A (Excluded) | **N/A (Excluded)** | `None` | `NOT_ESTABLISHED` | `LIVE_GEMINI` | 25.8s | **Hit (Uncertain)** |

---

## 6. Independent MRR Audit & Proof

$$\text{MRR}_{\text{Phase 3B.8 Live}} = \frac{1}{N} \sum_{i=1}^{N} \text{RR}_{i}$$

- **Eligible Scenarios ($N = 7$):** S001 through S007 where `expected_driver is not None`.
- **Excluded Scenario (S008):** S008 is an uncertainty validation test with ground truth `NOT_ESTABLISHED` (null driver) and is excluded from the ranking denominator.
- **Reciprocal Rank Breakdown:**
  - $RR(S001) = 1/1 = 1.0000$ (Returns promoted to Rank 1 via CRM defect logs)
  - $RR(S002) = 1/2 = 0.5000$
  - $RR(S003) = 1/1 = 1.0000$
  - $RR(S004) = 1/1 = 1.0000$ (Fallback preserved Phase 3A Rank 1)
  - $RR(S005) = 1/1 = 1.0000$
  - $RR(S006) = 1/2 = 0.5000$ (Fallback preserved Phase 3A Rank 2)
  - $RR(S007) = 1/2 = 0.5000$
- **Exact Calculation:**
  $$\text{Numerator} = 1.0 + 0.5 + 1.0 + 1.0 + 1.0 + 0.5 + 0.5 = 5.5$$
  $$\text{Denominator} = 7$$
  $$\mathbf{\text{Live MRR}} = \frac{5.5}{7} = \mathbf{0.7857}$$

---

## 7. Critical Metric Distinction: Ranking vs Diagnosis

The evaluation strictly differentiates **Candidate Top-3 Recall** from **Established Driver Accuracy**:

- **Candidate Top-3 Recall (100.0% = 8/8):** In all 8 scenarios, the target causal hypothesis was retained within the investigated candidate set.
- **Established Driver Accuracy (62.5% = 5/8):** In 5 of 8 scenarios (S001, S003, S004, S005, S008), the final diagnostic output established the exact target cause.
- **Status Accuracy (50.0% = 4/8):** In S002, S004, S006, S008, the assigned diagnostic certainty status matched ground truth causal certainty.

---

## 8. Provenance & Fallback Integrity

| Provenance Category | Scenario Count | Scenarios | Description |
| :--- | :---: | :--- | :--- |
| **`LIVE_GEMINI`** | **6** | S001, S002, S003, S005, S007, S008 | Genuine live Gemini API reasoning with verified JSON response and 100% evidence citation grounding. |
| **`DETERMINISTIC_FALLBACK`** | **2** | S004, S006 | S004 triggered safe fallback due to a 45s HTTP read timeout; S006 triggered safe fallback due to schema validation gating. Phase 3A deterministic outputs were safely preserved. |
| **`MOCK_PROVIDER`** | **0** | None | Zero mock runs in this benchmark. |

---

## 9. Security, Isolation & Safety Audit

1. **Ground-Truth Isolation:** Verified. The live payload construction passes only Phase 3A analytical outputs. Zero ground truth files, answer keys, or expected driver labels were supplied to the LLM prompt.
2. **Untrusted Text Sandboxing:** Verified. CRM notes, support logs, and sales transcripts were wrapped in `<UNTRUSTED_EVIDENCE_RECORD>` isolation tags.
3. **Evidence Grounding (100.0%):** Verified. Every claim in the live outputs referenced existing indexed `EVD-xxx` IDs.
4. **Unsupported Claims (0.0%):** Verified. Zero ungrounded or hallucinated assertions were accepted by the validator.
5. **Fallback Integrity:** Verified. When timeouts or validation anomalies occurred, the engine fell back gracefully without throwing unhandled exceptions or corrupting outputs.

---

## 10. Regression Test Verification

Executed full regression suite across all 143 test cases:
```bash
python -m unittest discover -s tests
```
- **Total Tests:** 143
- **Passed:** 143
- **Failed:** 0
- **Errors:** 0
- **Regression Status:** **`100% OK (Zero Regressions)`**

---

## 11. Final Phase 3A Preservation Check

Re-executed Phase 3A accuracy benchmark after live evaluation:
```text
Top-1 Hypothesis Accuracy:   4 / 8 = 50.0%
Top-3 Hypothesis Recall:     8 / 8 = 100.0%
Mean Reciprocal Rank (MRR):  0.7143 (denominator: 7)
Established Driver Accuracy: 4 / 8 = 50.0%
Status Accuracy:             3 / 8 = 37.5%
Uncertainty Accuracy (S008): 1 / 1 = 100.0%
```
**`PHASE 3A PRESERVATION: VERIFIED / UNCHANGED`**

---

## 12. System Limitations & Observations

1. **Live API Latency:** Live Gemini reasoning averaged ~28–32s per scenario (p50: 30.0s, p95: 45.2s). In interactive UI applications, asynchronous streaming or caching should be considered.
2. **Network Resilience:** S004 encountered a network read timeout at 45s, which was cleanly caught and handled by the deterministic fallback.
3. **Qualitative Evidence Lift:** Scenario S001 demonstrated the core value proposition of LLM reasoning: synthesizing unstructured CRM defect notes with structured return rates to correct Phase 3A's false-positive marketing attribution and establish `DRIVER_04_RETURNS` at Rank 1.
