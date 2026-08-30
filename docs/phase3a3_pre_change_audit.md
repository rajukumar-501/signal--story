# Phase 3A.3 Pre-Change Audit Document

## 1. Executive Context
This pre-change audit provides a comprehensive baseline review of the analytical backend engine following Phase 3A.2. It details current schema structures, data flow, scoring mechanics, evidence attribution, and evaluation methods to prepare for the Phase 3A.3 final hardening and the separation of hypothesis ranking from diagnosis.

---

## 2. Comprehensive Component Audit

### 2.1. Current Output Schema
Currently in [`diagnosis.py`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/src/analytics/diagnosis.py), the engine produces:
```json
{
  "event": {
    "kpi": "gross_sales",
    "current_value": 38357.61,
    "previous_month_value": 313953.80,
    "baseline_value": 423842.74,
    "mom_change_percent": -0.8778,
    "baseline_change_percent": -0.9095,
    "change_percent": -0.8778,
    "baseline_status": "VALID"
  },
  "candidate_drivers": [
    {
      "rank": 1,
      "driver": "DRIVER_06_CUSTOMER",
      "score": 1.0,
      "status": "NOT_ESTABLISHED",
      "confidence": "NONE",
      "evidence": [...],
      "contradictions": [],
      "evidence_source_count": 1,
      "supporting_evidence_count": 1,
      "outcome_evidence_count": 1,
      "contradictory_evidence_count": 0,
      "temporal_alignment": "DURING"
    }
  ],
  "overall_status": "NOT_ESTABLISHED",
  "limitations": [
    "Analysis relies entirely on available structured datasets.",
    "Causal status is observational, not interventional."
  ]
}
```
**Inconsistency Identified:**
- The payload uses `candidate_drivers` to represent the list of investigated candidates, but does not provide an explicit `diagnosis` object containing `established_driver`, `overall_status`, `reason`, and `confidence`.
- Downstream evaluators or consumers could misinterpret rank #1 in `candidate_drivers` as the established cause even when its status is `NOT_ESTABLISHED`.

---

### 2.2. Candidate Generation
In [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/src/analytics/driver_generator.py), the generator runs 8 distinct driver evaluations:
1. `DRIVER_01_INVENTORY`: Stockouts and closing inventory drops.
2. `DRIVER_02_PRICING`: Competitor price gap growth MoM.
3. `DRIVER_03_MARKETING`: Marketing spend increase + conversion rate decline MoM.
4. `DRIVER_04_RETURNS`: Return rate increase MoM.
5. `DRIVER_05_SUPPORT`: Customer service ticket surge, negative sentiment growth, and CRM/sales call complaints growth MoM.
6. `DRIVER_06_CUSTOMER`: Channel / Customer segment share drops.
7. `DRIVER_07_MARKET`: Target market MoM growth vs. Rest-of-Company peer growth.
8. `DRIVER_08_PRODUCT_MIX`: Category share drops and mix shifts.

Each generator enforces scope filtering using `apply_scope()` in `data_model.py`.

---

### 2.3. Candidate Scoring
In [`evidence_scorer.py`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/src/analytics/evidence_scorer.py):
$$\text{BaseScore} = (\text{SignalScore} + \text{CorroborationScore}) \times \text{TemporalMultiplier}$$
- `SignalScore`: 0.5 to 6.0 based on `driver_change_pct`. If `supporting_evidence_count == 0`, `SignalScore = 0.0`.
- `CorroborationScore`: $(\text{distinct\_supporting\_sources} - 1) \times 3.0$ if $\ge 2$ sources.
- `TemporalMultiplier`: 1.0 if `DURING` or `BEFORE`, 0.0 if `AFTER` or `NO_CLEAR_ALIGNMENT`.

---

### 2.4. Candidate Ranking
In [`driver_ranker.py`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/src/analytics/driver_ranker.py):
- Candidates are sorted descending by `final_score` (defaulting to `base_score` if missing).
- Candidate status mapping:
  - If `final_score == 0.0` or `supporting_evidence_count == 0` or `contradictory_evidence_count > supporting_evidence_count`: `status = NOT_ESTABLISHED`, `confidence = NONE`.
  - Else if `final_score >= 7.0`: `status = STRONGLY_SUPPORTED`, `confidence = HIGH`.
  - Else if `final_score >= 4.0`: `status = PLAUSIBLE`, `confidence = MEDIUM`.
  - Else: `status = NOT_ESTABLISHED`, `confidence = NONE`.

---

### 2.5. Overall Status Calculation
Currently, `DriverRanker.determine_overall_status(ranked_candidates)` checks if the top candidate has status `STRONGLY_SUPPORTED` or `PLAUSIBLE`. If so, it returns that status; otherwise, it returns `NOT_ESTABLISHED`.
However, it does not explicitly encapsulate this into a structured `diagnosis` dictionary with an explicit `established_driver` (`str | None`), `overall_status`, `reason`, and `confidence`.

---

### 2.6. Evidence Roles
Every evidence item created by `_create_evidence()` or record appenders in `driver_generator.py` contains:
- `OUTCOME`: The KPI drop being analyzed.
- `SUPPORTING`: Driver-specific metrics (e.g. stockouts, price gaps, return rate growth, ticket volume growth).
- `CONTRADICTORY`: Clashing metrics (e.g. price becoming cheaper, inventory stockout_flag = 0).

`OUTCOME` evidence is strictly prevented from increasing `SignalScore` or `CorroborationScore`.

---

### 2.7. Contradiction Handling
In [`contradiction_engine.py`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/src/analytics/contradiction_engine.py):
- Contradiction items (tagged `CONTRADICTORY`) are identified.
- Cross-hypothesis contradictions (e.g. inventory stockouts occurring during an alleged marketing inefficiency) are added.
- Penalty: $\text{c\_score} = \text{len(contradictions)} \times 15.0$.
- Final score: $\text{final\_score} = \max(0.0, \text{base\_score} - \text{c\_score})$.

---

### 2.8. Temporal Alignment
Evaluated across `prev_1m` (BEFORE), `target_date` (DURING), and `next_1m` (AFTER):
- `BEFORE`: Signal observed prior to event month.
- `DURING`: Signal observed in event month.
- `AFTER`: Signal observed only after event month (multiplied by 0.0).
- `NO_CLEAR_ALIGNMENT`: No signal observed (multiplied by 0.0).

---

### 2.9. Ground-Truth Isolation
- No ground truth datasets or scenario IDs are referenced in production analytical code (`src/analytics/`).
- Enforced by automated tests in `tests/test_phase3a_engine.py` inspecting `sys.modules`, function signatures, and disallowed tokens.

---

### 2.10. Current S008 Behavior
In scenario S008 (Germany gross sales in March 2020), sales dropped by ~90%.
- `DRIVER_07_MARKET` peer comparison checks target market growth vs rest of company. Because the entire company dropped by ~86%, the relative difference was negligible (-1.1%), so `DRIVER_07_MARKET` was negated.
- Weak candidates (such as minor channel shifts in Customer or Product Mix) scored 1.0 and were assigned status `NOT_ESTABLISHED`.
- Overall status correctly resolved to `NOT_ESTABLISHED`.
- **Gap to address in 3A.3:** The output must explicitly provide `diagnosis.established_driver = null` while preserving the ranked investigated hypotheses in `candidate_hypotheses`.

---

### 2.11. Current Evaluation Methodology
- Phase 3A.2 evaluation in `tests/test_phase3a2_accuracy.py` evaluated `top1_correct` by comparing `cands[0]["driver"]` with `expected_driver`.
- When `expected_driver` was `"NOT_ESTABLISHED"`, it failed `top1_correct` because `cands[0]["driver"]` was `DRIVER_06_CUSTOMER` (even though its status was `NOT_ESTABLISHED`).
- **Correction in 3A.3:** Separate hypothesis ranking evaluation (`top1_hypothesis_correct`, `top3_hypothesis_contains_expected`, `reciprocal_rank`) from established diagnosis evaluation (`established_driver_correct`, `status_correct`, `uncertainty_accuracy`).

---

### 2.12. Remaining Inconsistencies & Required Hardening
1. **Contract Structure:** Change `candidate_drivers` to `candidate_hypotheses`, and add explicit `diagnosis` dictionary (`established_driver`, `overall_status`, `reason`, `confidence`).
2. **Diagnosis Gate:** Create a dedicated deterministic gate method `DiagnosisGate.evaluate(event, ranked_hypotheses)` that explicitly checks all 7 criteria to establish a diagnosis or return `null`.
3. **Evaluation Metrics:** Add Mean Reciprocal Rank (MRR), Established Driver Accuracy, and Uncertainty Accuracy to `Data/evaluation/phase3a3_results.csv`.
4. **Behavior & Diagnosis Tests:** Create `tests/test_phase3a3_diagnosis_contract.py` covering the 12 required test specifications.

---
*Audit Completed. Ready for Phase 3A.3 implementation.*
