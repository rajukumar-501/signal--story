# Phase 3B Ground-Truth Discovery & Isolation Specification

## 1. Project Structure Inspected

- **Project Root**: `c:\Users\rajuk\OneDrive\Desktop(1)\Accenture_Decision_Intelligence`
- **Phase 3A Analytics Source**: `src/analytics/`
- **Canonical Processed Data**: `Data/Processed/`
- **Evaluation Inputs Directory**: `Data/scenarios/evaluation_inputs/`
- **Evaluation Ground Truth Directory**: `Data/scenarios/evaluation_ground_truth/`
- **Scenario Artifacts Directory**: `Data/scenarios/`
- **Evaluation Benchmark Results**: `Data/evaluation/`
- **Test Suites**: `tests/`

---

## 2. Discovered Locations & Classifications

### A. Allowed Runtime Data (Accessible by Phase 3A & Future Phase 3B Runtime)
- **Directory**: `Data/Processed/` (10 canonical datasets)
  - `dim_product.csv`
  - `dim_customer.csv`
  - `dim_market.csv`
  - `fact_sales_monthly.csv` (contains integrated return metrics `is_return`, `return_qty`, `return_sales_amount`)
  - `fact_inventory_monthly.csv`
  - `fact_competitor_pricing_monthly.csv`
  - `fact_marketing_monthly.csv`
  - `fact_support_tickets.csv`
  - `fact_crm_notes.csv`
  - `fact_sales_calls.csv`
- **Phase 3A Output Payload**: Runtime diagnostic objects containing `event`, `candidate_hypotheses`, and `diagnosis`.

### B. Evaluation-Input Files (Evaluation Benchmark Ingestion Only)
- **Directory**: `Data/scenarios/evaluation_inputs/`
  - `S001_input.csv` through `S008_input.csv`
- **Fields Present**: `scenario_id`, `evidence_id`, `evidence_role`, `source_dataset`, `record_id`, `date`, `market`, `product_code`, `customer_code`, `metric_name`, `metric_value`, `baseline_value`, `change_value`, `change_percent`, `evidence_text`, `evidence_strength`, `direction`, `is_contradictory`, `calculation_formula`.
- **Purpose**: Input evidence packets used to feed the evaluation runner without revealing oracle target labels.

### C. Evaluation Ground Truth (STRICTLY PROHIBITED FROM RUNTIME / LLM)
- **Directory**: `Data/scenarios/evaluation_ground_truth/`
  - `S001_truth.csv` through `S008_truth.csv`
- **Master Files**:
  - `Data/scenarios/ground_truth.csv`
  - `tests/scenario_ground_truth.json`
- **Ground-Truth Fields Discovered**:
  - `true_root_cause`
  - `root_cause_status`
  - `confidence`
  - `secondary_factors`
  - `alternative_explanations`
  - `supporting_evidence_sources`
  - `contradictory_evidence_sources`
  - `known_limitations`
- **Access Rule**: **MUST REMAIN EVALUATION-ONLY**. Accessible strictly by the evaluation harness *after* reasoning has completed.

---

## 3. Data Flow Architecture & Technical Isolation Boundary

```
                     ┌──────────────────────────────┐
                     │ Canonical Processed Datasets │
                     │       Data/Processed/        │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │    Phase 3A Engine (Frozen)  │
                     │       src/analytics/         │
                     └──────────────┬───────────────┘
                                    │
                                    ▼ Phase 3A Output Payload
                     ┌──────────────────────────────┐
                     │   Future Phase 3B Runtime    │
                     │         (LLM Layer)          │
                     └──────────────┬───────────────┘
                                    │
                                    ▼ Final Generated Diagnosis
                     ┌──────────────────────────────┐
                     │      Evaluation Harness      │
                     │  tests/test_phase3b_eval.py  │
                     └──────────────┬───────────────┘
                                    │ Evaluates after generation
                                    ▼
                     ┌──────────────────────────────┐
                     │   Evaluation Ground Truth    │
                     │ Data/scenarios/eval_truth/   │
                     └──────────────────────────────┘
```

---

## 4. Strict Runtime Isolation Rules

1. **Zero Ground-Truth Ingestion**: Phase 3B runtime code must never import, load, scan, parse, index, or embed files located in `Data/scenarios/evaluation_ground_truth/` or `Data/scenarios/ground_truth.csv`.
2. **Zero Field Leakage**: Parameter signatures and JSON runtime payloads consumed by Phase 3B must not contain `true_root_cause`, `root_cause_status`, `expected_driver`, or `expected_established_driver`.
3. **Evaluation Post-Execution Only**: Ground-truth labels are read solely by evaluation scripts after the model has returned its final response.
4. **Zero Phase 3A Modification**: The deterministic analytical engine (`src/analytics/`) remains completely untouched and frozen.

---

## 5. Isolation Verification Test Suite (`tests/test_phase3b_isolation.py`)

| Test ID | Test Name | Purpose | Result |
| :--- | :--- | :--- | :---: |
| **TEST 1** | `test_01_path_isolation` | Verifies `Data/scenarios/evaluation_ground_truth/` is completely segregated from `Data/Processed/` | **PASS** |
| **TEST 2** | `test_02_source_reference_check` | Confirms production `src/analytics/` files contain no references to ground-truth files | **PASS** |
| **TEST 3** | `test_03_ground_truth_field_leakage` | Verifies runtime entrypoints (`run_analysis`) accept no ground-truth oracle fields | **PASS** |
| **TEST 4** | `test_04_phase_3a_integrity` | Confirms all 10 core Phase 3A analytics modules exist and compile with zero errors | **PASS** |
| **TEST 5** | `test_05_ground_truth_preservation` | Confirms all 8 ground-truth files (`S001_truth.csv`..`S008_truth.csv`) are intact and non-empty | **PASS** |
| **TEST 6** | `test_06_evaluation_access_separation` | Confirms end-to-end execution generates complete diagnoses without ground-truth access | **PASS** |

---

## 6. Integrity Audit Results

1. **Phase 3A Analytical Source Integrity**: **PASS** (Zero files in `src/analytics/` modified).
2. **Canonical Datasets Integrity**: **PASS** (All 10 processed datasets intact in `Data/Processed/`).
3. **Ground-Truth Files Integrity**: **PASS** (All 8 truth files and master CSV unchanged).
4. **Evaluation Input Integrity**: **PASS** (All 8 input CSVs unchanged).
5. **No Ground-Truth Leakage into Prompts / Configs**: **PASS**.

---

## 7. Known Limitations
- Evaluation harness tests must continue to maintain explicit separation between test setup (ground truth loading) and execution calls (`run_analysis()`).
- Unstructured evidence files (`fact_crm_notes.csv`, `fact_sales_calls.csv`) in `Data/Processed/` contain realistic business noise and must be evaluated without leaking true causes into prompting.

---

## 8. Conclusion

**`PHASE_3B_ISOLATION_READY`**
