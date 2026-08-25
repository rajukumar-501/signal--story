# Scenario Ground Truth Methodology

This document outlines the methodology used to independently verify the scenarios discovered in Phase 2A and to generate the final evaluation datasets.

## 1. Goal

The goal is to evaluate candidate scenarios programmatically using canonical datasets and ensure that each anomaly is verifiable without assumptions.

## 2. Evidence Hierarchy & Classification

To provide a robust test harness for the AI system, all evidence is classified into roles:
- **OUTCOME**: What happened (e.g., Gross sales fell 85%).
- **DRIVER**: Data directly supporting the root cause (e.g., Marketing spend increased 132%).
- **SUPPORTING**: Independent data strengthening the explanation (e.g., Ticket texts).
- **CONTRADICTORY**: Data weakening the explanation (e.g., Stockouts occurring during a marketing push).
- **CONTEXT**: Useful background information.

## 3. Causal Status & Confidence

We do not use casual causal language. Root cause certainty is mapped using formal statuses:
- **STRONGLY_SUPPORTED**: High evidence volume linking the outcome to the driver.
- **PLAUSIBLE**: Driver exists but alternative explanations remain strong.
- **NOT_ESTABLISHED**: Insufficient data to name a cause (e.g., S008 tests AI uncertainty handling).
- **PROVEN**: Narrowly reserved *only* for causes directly established by deterministic business logic or controlled/interventional evidence. Ordinary observational correlations are never marked as PROVEN.

## 4. Separation & Anti-Leakage Rules

To prevent Data Leakage:
1. **Ground-Truth Separation**: The inputs fed to the AI (`evaluation_inputs/`) are completely segregated from the expected answers (`evaluation_ground_truth/`).
2. **Semantic Leakage Control**: AI inputs are actively tested for evaluator terminology (`true_root_cause`, `expected_answer`, etc.).
3. **Temporal Cutoff**: No evidence is ingested from after the `information_cutoff_date` (which is typically the end of the event month).

## 5. Traceability

Every piece of evidence stored in `evaluation_inputs` contains a `source_dataset` and a `record_id` (where applicable). Computed metrics contain a `calculation_formula` allowing the harness to audit the evidence lineage.
