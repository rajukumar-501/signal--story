# Phase 2B.1 Remediation Report (Updated for Phase 2B.2)

## 1. Problems Identified in Original Phase 2B
- **Sales-centric Evidence:** Original evidence packets solely contained sales metrics, excluding true drivers and auxiliary evidence.
- **Leakage:** Both temporal leakage and ground-truth hints were at risk of being fed to the future AI due to unsegregated evidence files.
- **Insufficient Detail in S003/S004/S005:** Specific unstructured data constraints and parameter changes were originally aggregated rather than being stored as atomic evidence.
- **Invalid Scenario Interpretations:** S007 (Category Mix Shift) and S008 (Unexplained Market Shock) were previously treated as standard revenue declines.

## 2. Fixes Applied
- We split the outputs into `data/scenarios/evaluation_inputs/` (completely sanitized from hints) and `data/scenarios/evaluation_ground_truth/` (expected output answers).
- The extraction pipeline produces discrete records marked with specific roles (OUTCOME, DRIVER, SUPPORTING, CONTRADICTORY, CONTEXT) and traceable source mappings.
- Added `evaluation_input_audit.csv` to ensure structural integrity across records.

## 3. Evidence Status & Limitations
| Scenario | KPI Verified | Driver Evidence | Unstructured Evidence | Root Cause Status | Confidence | Evidence Quality | Keep/Review |
|----------|--------------|-----------------|-----------------------|-------------------|------------|------------------|-------------|
| S001     | Yes          | Return Spike    | 0                     | STRONGLY_SUPPORTED| HIGH       | C                | Keep        |
| S002     | Yes          | Shift           | Present (CRM/Support) | STRONGLY_SUPPORTED| HIGH       | B                | Keep        |
| S003     | Yes          | Spend/CVR       | 0                     | STRONGLY_SUPPORTED| HIGH       | C                | Keep        |
| S004     | Yes          | Price Gap       | 0                     | PLAUSIBLE         | MEDIUM     | C                | Keep        |
| S005     | Yes          | Ticket Text     | Present (Support)     | PLAUSIBLE         | MEDIUM     | B                | Keep        |
| S006     | Yes          | Category Share  | Present (Support/CRM) | PLAUSIBLE         | MEDIUM     | B                | Keep        |
| S007     | Yes          | Category Share  | Present (Support/CRM) | STRONGLY_SUPPORTED| HIGH       | B                | Keep        |
| S008     | Yes          | None            | Present (Support/CRM) | NOT_ESTABLISHED   | LOW        | B                | Keep        |

**Explicit Limitations:**
- **S001, S003, S004:** These are structured evidence-dominant scenarios. Unstructured corroboration (CRM notes, support tickets, sales calls) is zero/unavailable in the current dataset. We have not artificially inflated the evidence quality.
- **S002, S006, S007, S008:** These scenarios often do not have a single "DRIVER" metric but instead contain "SUPPORTING" evidence (like ticket texts) or "OUTCOME" metrics (like E-Commerce sales increases). S008 deliberately lacks a driver to test uncertainty.

## 4. Scenario 7 & 8 Overhauls
- **S007 Interpretation:** Strictly defines its primary KPI as `category_share`, establishing it as a `PRODUCT_MIX / RELATIVE_PERFORMANCE_SHIFT`. Absolute category sales increased, but relative market share shifted.
- **S008 Uncertainty Handling:** Tests the AI's ability to resist hallucination. It explicitly has `root_cause_status = NOT_ESTABLISHED`.
