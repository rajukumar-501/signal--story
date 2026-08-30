# Phase 3A.3 Comparative Analysis Report

## 1. Executive Summary
This report presents the comparative analysis between **Phase 3A.2** (Analytical Correctness Hardening) and **Phase 3A.3** (Output Contract Separation & Diagnosis Gating). 

The primary innovation of Phase 3A.3 is the rigorous architectural decoupling of:
1. **Candidate Hypotheses (`candidate_hypotheses`)**: The complete, ordered list of investigated causal hypotheses, preserving weak signals for reasoning.
2. **Final Diagnosis (`diagnosis`)**: The deterministic conclusion representing only verified, gate-passed drivers (`established_driver`, `overall_status`, `reason`, `confidence`).

---

## 2. Metrics Comparison Matrix

| Evaluation Metric | Phase 3A.1 Baseline | Phase 3A.2 Hardened | Phase 3A.3 Contract Hardened | Delta (3A.2 $\rightarrow$ 3A.3) |
| :--- | :---: | :---: | :---: | :---: |
| **Top-1 Hypothesis Accuracy** | 12.5% (1/8) | 50.0% (4/8) | **50.0% (4/8)** | Stable (+0.0%) |
| **Top-3 Hypothesis Recall** | 75.0% (6/8) | 87.5% (7/8) | **100.0% (8/8)** | **+12.5% (Perfect Recall)** |
| **Mean Reciprocal Rank (MRR)** | N/A | N/A | **0.7143** (den: 7) | **Baseline Established** |
| **Established Driver Accuracy** | N/A | N/A | **50.0% (4/8)** | **Baseline Established** |
| **Status Accuracy** | 50.0% (4/8) | 37.5% (3/8) | **37.5% (3/8)** | Stable |
| **Uncertainty Accuracy (S008)** | 0.0% (0/1) | 100.0% (1/1) | **100.0% (1/1)** | Fully Preserved |

---

## 3. Scenario-by-Scenario Detailed Breakdown

| Scenario | Expected Established Driver | Expected Status | 3A.2 Top Driver | 3A.3 Established Driver | 3A.3 Overall Status | 3A.3 Top-3 Candidate Hypotheses | Reciprocal Rank |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **S001** | `DRIVER_04_RETURNS` | `STRONGLY_SUPPORTED` | `DRIVER_03_MARKETING` | `DRIVER_03_MARKETING` | `PLAUSIBLE` | `DRIVER_03_MARKETING`, `DRIVER_04_RETURNS`, `DRIVER_06_CUSTOMER` | 0.5000 |
| **S002** | `DRIVER_06_CUSTOMER` | `STRONGLY_SUPPORTED` | `DRIVER_05_SUPPORT` | `DRIVER_05_SUPPORT` | `STRONGLY_SUPPORTED` | `DRIVER_05_SUPPORT`, `DRIVER_06_CUSTOMER`, `DRIVER_08_PRODUCT_MIX` | 0.5000 |
| **S003** | `DRIVER_03_MARKETING` | `STRONGLY_SUPPORTED` | `DRIVER_03_MARKETING` | `DRIVER_03_MARKETING` | `PLAUSIBLE` | `DRIVER_03_MARKETING`, `DRIVER_04_RETURNS`, `DRIVER_08_PRODUCT_MIX` | 1.0000 |
| **S004** | `DRIVER_02_PRICING` | `PLAUSIBLE` | `DRIVER_02_PRICING` | `DRIVER_02_PRICING` | `PLAUSIBLE` | `DRIVER_02_PRICING`, `DRIVER_04_RETURNS`, `DRIVER_01_INVENTORY` | 1.0000 |
| **S005** | `DRIVER_05_SUPPORT` | `PLAUSIBLE` | `DRIVER_05_SUPPORT` | `DRIVER_05_SUPPORT` | `STRONGLY_SUPPORTED` | `DRIVER_05_SUPPORT`, `DRIVER_06_CUSTOMER`, `DRIVER_08_PRODUCT_MIX` | 1.0000 |
| **S006** | `DRIVER_08_PRODUCT_MIX` | `PLAUSIBLE` | `DRIVER_06_CUSTOMER` | `None` | `NOT_ESTABLISHED` | `DRIVER_06_CUSTOMER`, `DRIVER_08_PRODUCT_MIX`, `DRIVER_01_INVENTORY` | 0.5000 |
| **S007** | `DRIVER_08_PRODUCT_MIX` | `STRONGLY_SUPPORTED` | `DRIVER_04_RETURNS` | `DRIVER_04_RETURNS` | `PLAUSIBLE` | `DRIVER_04_RETURNS`, `DRIVER_08_PRODUCT_MIX`, `DRIVER_01_INVENTORY` | 0.5000 |
| **S008** | `None` (Uncertain) | `NOT_ESTABLISHED` | `DRIVER_06_CUSTOMER` | `None` | `NOT_ESTABLISHED` | `DRIVER_06_CUSTOMER`, `DRIVER_08_PRODUCT_MIX`, `DRIVER_01_INVENTORY` | null |

---

## 4. Key Takeaways & Diagnostic Semantics

1. **Resolution of S008 Contract Ambiguity:**
   - In Phase 3A.2, S008 had `DRIVER_06_CUSTOMER` at rank 1 with score 1.0 (status `NOT_ESTABLISHED`), causing evaluation confusion.
   - In Phase 3A.3, `DiagnosisGate` clearly evaluates that score 1.0 is below the $\ge 4.0$ establishment threshold, correctly outputting `diagnosis.established_driver = null` and `diagnosis.overall_status = "NOT_ESTABLISHED"` while preserving the investigated hypotheses list.
   - S008 is evaluated under Uncertainty Accuracy and excluded from the driver-ranking MRR denominator.
2. **Perfect Top-3 Recall (100.0%):**
   - Every target cause is captured in the top 2 candidate hypotheses across all 7 driver-seeking scenarios (yielding a strong Mean Reciprocal Rank of 0.7143 over the 7 scenarios).
3. **Foundation for Phase 3B LLM Reasoning:**
   - Because all target root causes are present in the top-2 ranked candidate hypotheses with full structured evidence, the Phase 3B LLM reasoning layer will have 100% information coverage to arbitrate between the top candidate hypotheses (e.g. S001 Returns vs Marketing, S002 Customer Channel shift vs Support Tickets).
