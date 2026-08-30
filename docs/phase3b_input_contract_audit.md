# Phase 3B Input Contract Audit

## 1. Executive Summary
This document audits the exact Phase 3A deterministic output interface to be consumed by the Phase 3B LLM reasoning layer. Phase 3A remains frozen and unmodified. Phase 3B consumes this structured contract to perform evidence-grounded synthesis, multi-hypothesis arbitration, and actionable explanation without direct access to raw ground truth or oracle answer keys.

---

## 2. Phase 3A Output Payload Schema

The top-level JSON dictionary returned by `run_analysis()` adheres to the following structure:

```json
{
  "event": {
    "kpi": "gross_sales",
    "current_value": 994.25,
    "previous_month_value": 7009.60,
    "baseline_value": 3558.03,
    "mom_change_percent": -0.8582,
    "baseline_change_percent": -0.7206,
    "change_percent": -0.8582,
    "baseline_status": "VALID"
  },
  "candidate_hypotheses": [ ... ],
  "candidate_drivers": [ ... ],
  "diagnosis": {
    "established_driver": "DRIVER_03_MARKETING",
    "overall_status": "PLAUSIBLE",
    "reason": "Driver DRIVER_03_MARKETING established with status PLAUSIBLE (score: 6.0, sources: 1).",
    "confidence": "MEDIUM"
  },
  "overall_status": "PLAUSIBLE",
  "limitations": [
    "Analysis relies entirely on available structured datasets.",
    "Causal status is observational, not interventional."
  ]
}
```

---

## 3. Discovered Field Specifications & Schemas

### 1. `candidate_hypotheses` Schema
Each element in `candidate_hypotheses` (and alias `candidate_drivers`) is a dictionary with:
- `driver` (`str`): Driver identifier (e.g., `"DRIVER_01_INVENTORY"` through `"DRIVER_08_PRODUCT_MIX"`).
- `rank` (`int`): Deterministic 1-based rank (1 to N).
- `score` (`float`): Final composite evidence score.
- `status` (`str`): `"STRONGLY_SUPPORTED"`, `"PLAUSIBLE"`, or `"NOT_ESTABLISHED"`.
- `confidence` (`str`): `"HIGH"`, `"MEDIUM"`, or `"NONE"`.
- `evidence` (`List[Dict]`): List of structured and textual evidence items.
- `contradictions` (`List[str]`): List of contradictory metric names or clash flags.
- `evidence_source_count` (`int`): Count of distinct supporting datasets.
- `supporting_source_count` (`int`): Alias for supporting source count.
- `supporting_evidence_count` (`int`): Total count of supporting evidence records.
- `outcome_evidence_count` (`int`): Total count of outcome evidence records.
- `contradictory_evidence_count` (`int`): Total count of contradictory evidence records.
- `temporal_alignment` (`str`): Temporal relationship between driver signal and KPI anomaly.

### 2. `diagnosis` Schema
The `diagnosis` block represents the gated deterministic verdict:
- `established_driver` (`Optional[str]`): Identified driver ID (e.g. `"DRIVER_03_MARKETING"`) or `None` if unestablished.
- `overall_status` (`str`): Diagnostic status (`"STRONGLY_SUPPORTED"`, `"PLAUSIBLE"`, `"NOT_ESTABLISHED"`).
- `reason` (`str`): Human-readable justification of the gate evaluation.
- `confidence` (`str`): Deterministic confidence (`"HIGH"`, `"MEDIUM"`, `"NONE"`).

### 3. `evidence` Item Schema
Every individual evidence record contains:
- `source_dataset` (`str`): Name of canonical table (e.g., `"fact_marketing_monthly"`, `"fact_crm_notes"`, `"fact_support_tickets"`).
- `record_id` (`Optional[str]`): Unique identifier when from granular datasets (e.g., `"SR-2021-04-001"`, `"CRM-1002"`) or `None` for monthly aggregates.
- `lineage` (`str`): Lineage classification (`"RAW"`, `"AGGREGATED"`, `"DERIVED"`).
- `date` (`str`): Date timestamp in `YYYY-MM-DD` format.
- `market` (`Optional[str]`): Scope market name or `None`.
- `product_code` (`Optional[str]`): Scope product code or `None`.
- `category` (`Optional[str]`): Scope product category or `None`.
- `channel` (`Optional[str]`): Scope customer channel or `None`.
- `metric` (`str`): Specific metric name or feature evaluated (e.g., `"spend_change"`, `"conversion_rate_change"`, `"stockout_hours"`).
- `value` (`Union[float, str]`): Quantitative value or text snippet.
- `evidence_role` (`str`): Role of evidence.

### 4. `evidence_role` Values
- `"SUPPORTING"`: Positive causal evidence directly supporting the hypothesis.
- `"OUTCOME"`: Downstream impact on target KPI (the effect itself).
- `"CONTRADICTORY"`: Counter-evidence that refutes or penalizes the hypothesis.
- `"CONTEXT"`: Baseline or background reference metric.

### 5. `evidence` Source Metadata
- Direct dataset origin is tracked via `source_dataset`.
- Lineage level is tracked via `lineage`.
- Granular tracking ID is stored in `record_id`.

### 6. `temporal_alignment` Values
- `"BEFORE"`: Driver signal occurred prior to KPI drop (leading indicator).
- `"DURING"`: Driver signal occurred in the same period as KPI drop (coincident indicator).
- `"AFTER"`: Driver signal occurred only after KPI drop (lagging indicator, cannot establish causality).
- `"NO_CLEAR_ALIGNMENT"`: Inconclusive temporal ordering.

### 7. `contradiction` Representation
- Represented as a list of metric names in `cand["contradictions"]` (e.g., `["inventory_stockout_clash"]`).
- Tracked quantitatively in `cand["contradiction_score"]` (15.0 penalty per clash) and `cand["contradictory_evidence_count"]`.
- Added to `cand["evidence"]` with `evidence_role = "CONTRADICTORY"`.

### 8. `confidence` and `status` Values
- **Status values**: `"STRONGLY_SUPPORTED"`, `"PLAUSIBLE"`, `"NOT_ESTABLISHED"`.
- **Confidence values**: `"HIGH"`, `"MEDIUM"`, `"NONE"`.

### 9. `established_driver` Representation
- Set to driver string ID when gate criteria pass (Score $\ge 4.0$, supporting evidence $> 0$, temporal alignment `BEFORE`/`DURING`, contradictions not dominant).
- Set to `None` (JSON `null`) when criteria fail.

### 10. `NOT_ESTABLISHED` Representation
- `diagnosis.established_driver = None`
- `diagnosis.overall_status = "NOT_ESTABLISHED"`
- `diagnosis.confidence = "NONE"`
- `diagnosis.reason` details the specific gating failure (e.g., low score, dominating contradictions, invalid baseline).

---

## 4. Contract Freeze Verification
Phase 3A modules (`src/analytics/`) are verified frozen. Phase 3B will consume this contract strictly through standard read interfaces.
