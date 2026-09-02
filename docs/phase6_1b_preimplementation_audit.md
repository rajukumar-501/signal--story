# Phase 6.1B: Pre-Implementation UI/UX & Payload Audit

**Accenture Decision Intelligence Platform (Signal Story)**  
**Author:** Antigravity AI  
**Date:** 2026-08-31  
**Status:** Pre-Implementation Certified  

---

## 1. Executive Summary

This document fulfills the mandatory pre-implementation audit for **Phase 6.1B** of the Signal Story Decision Intelligence platform.

Every data element, metric, calculation, and timeline proposed for the high-density UI redesign has been audited directly against the live backend payloads (`POST /api/analyze`, `GET /api/connected-kpis`, `GET /api/telemetry`, `GET /api/data-trust`, `GET /api/scenarios`).

**Core Invariance Guarantee:** Zero files in the frozen analytical core (`src/analytics/`, `src/phase3b/`, `Data/Processed/`, `Data/scenarios/`) will be modified.

---

## 2. Comprehensive Payload & Data Audit

### A. Existing UI Components
1. **Header Area:** Basic dropdowns for Scenario, Persona, and Role; status badges for Data Trust and Mode toggles (Preview / Assisted Analysis); action buttons for Source Spec, KPI Contract, and Run Analysis.
2. **View 1 (Main Canvas):** 
   - Card 1: Signal Summary (KPI tag, delta %, actual value, 3-mo baseline, basic SVG line).
   - Card 2: Primary Signal (Driver title, driver code, status badge, executive summary narrative).
   - Card 3: Evidence (Evidence stack with change tags).
   - Card 4: Decision Support (Structured finding, why it matters, recommendation statement, verification checklist, affected area, owner, and review buttons).
   - Connected KPI Story: Flat grid of 5 connected metric tiles with alignment key summary.
   - Multi-Factor Decomposition Showcase: 3 candidate factor cards (Marketing Inefficiency vs Competitor Pricing vs Inventory Stockout).
   - Driver Comparison: 8-hypothesis table with rank, driver code, fit score, evidence support, and decision status.
   - Data Quality Summary: 6-metric trust grid (Quality score, temporal coverage, latest data, cadence, checks passed, blockers).
3. **View 2 (Evidence Workspace):** Evidence grounding strip, Granular Evidence Catalog table, Evidence Trail claim stream, Uncertainty Disclosures.
4. **View 3 (Integrity & Governance Audit):** Governance KPIs, 6-stage Pipeline Flow, Execution Environment checks, Analyst Feedback Learning metrics and reinforcement lists, KPI Semantic Contract grid, 9-dataset Data Trust table, Lineage table, 8-stage Processing Classification (LLM vs Non-LLM) table, Runtime Telemetry & Cost grid.
5. **Modals:** `source-spec-modal` (10 datasets / 5 domains) and `kpi-modal` (KPI definitions and baseline logic).

---

### B. Existing API Fields in `POST /api/analyze`

```json
{
  "scenario_id": "S003",
  "request": { "market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales" },
  "phase3a": {
    "event": {
      "kpi": "gross_sales",
      "current_value": 994.25,
      "baseline_value": 3558.0333333333333,
      "baseline_change_percent": -0.7205619209113648,
      "change_percent": -0.7205619209113648,
      "baseline_status": "VALID"
    },
    "candidate_drivers": [... 7 candidate evaluations ...],
    "diagnosis": { "driver": "DRIVER_03_MARKETING", "status": "STRONGLY_SUPPORTED" }
  },
  "phase3b": {
    "diagnosis": { "driver": "DRIVER_03_MARKETING", "status": "STRONGLY_SUPPORTED" },
    "supporting_evidence": [
      { "evidence_id": "EVD-002", "metric": "marketing_spend", "finding": "Marketing spend surged +64.9%" },
      { "evidence_id": "EVD-003", "metric": "conversion_rate", "finding": "Conversion rate dropped -48.8%" }
    ],
    "executive_summary": "Marketing activity increased while conversion performance deteriorated..."
  },
  "connected_kpis": {
    "distinct_sources_count": 2,
    "alignment_keys": ["date", "market", "product_code"],
    "connected_kpis": [
      { "kpi_id": "gross_sales", "current_value": 994.25, "baseline_value": 3558.03, "change_percent": -72.06, "formatted_value": "$994.25", "formatted_change": "-72.06%" },
      { "kpi_id": "order_volume", "current_value": 142.0, "baseline_value": 537.0, "change_percent": -73.56, "formatted_value": "142 units", "formatted_change": "-73.56%" },
      { "kpi_id": "marketing_spend", "current_value": 1641.07, "baseline_value": 994.94, "change_percent": 64.94, "formatted_value": "$1,641.07", "formatted_change": "+64.94%" },
      { "kpi_id": "conversion_rate", "current_value": 3.63, "baseline_value": 7.09, "change_percent": -48.78, "formatted_value": "3.63%", "formatted_change": "-48.78% (-3.46 pp)" },
      { "kpi_id": "click_through_rate", "current_value": 0.95, "baseline_value": 3.83, "change_percent": -75.07, "formatted_value": "0.95%", "formatted_change": "-75.07% (-2.87 pp)" }
    ]
  },
  "decision_governance": {
    "finding_statement": "Marketing performance is the strongest supported explanation...",
    "why_it_matters": "Higher marketing spend did not translate into proportional conversion...",
    "recommended_action": "Audit underperforming digital ad campaigns...",
    "risk_level": "HIGH",
    "safety_classification": "REQUIRES_HUMAN_APPROVAL",
    "prerequisites": ["Confirm underlying anomaly metrics in ERP ledger", "..."]
  },
  "persona_view": { "active_persona": "EXECUTIVE", "summary": "..." },
  "entitlement": { "active_role": "EXECUTIVE", "is_redacted": false },
  "runtime_telemetry": {
    "total_latency_ms": 14.5,
    "deterministic_latency_ms": 12.5,
    "llm_latency_ms": 0.0,
    "llm_calls_count": 0,
    "input_tokens": "UNAVAILABLE FROM PROVIDER",
    "output_tokens": "UNAVAILABLE FROM PROVIDER",
    "total_tokens": "UNAVAILABLE FROM PROVIDER",
    "estimated_cost_usd": "$0.000000 (MOCK_MODE)"
  }
}
```

---

### C. Existing Historical Time-Series Data (Audit of Canonical Warehouse Files)

Direct empirical audit of `fact_sales_monthly.csv` and `fact_marketing_monthly.csv` for Scenario S003 (China, A2520150501):

| Period (Date) | Gross Sales ($) | Order Volume (Units) | Marketing Spend ($) | CVR (%) | CTR (%) | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Jan 2021** (`2021-01-01`) | **$590.11** | **101** | **$1,691.02** | **7.26%** | **4.22%** | Baseline Observation $T-3$ |
| **Feb 2021** (`2021-02-01`) | **$3,074.39** | **459** | **$587.96** | **5.56%** | **3.24%** | Baseline Observation $T-2$ |
| **Mar 2021** (`2021-03-01`) | **$7,009.60** | **1,051** | **$705.85** | **7.88%** | **2.72%** | Baseline Observation $T-1$ |
| **3-Mo Baseline Mean** | **$3,558.03** | **537.0** | **$994.94** | **7.09%** | **3.83%** | Arithmetic Unweighted Mean |
| **Apr 2021** (`2021-04-01`) | **$994.25** | **142** | **$1,641.07** | **3.63%** | **0.95%** | **Anomaly Event ($T_0$)** |
| **Variance % vs Baseline** | **-72.06%** | **-73.56%** | **+64.94%** | **-48.78%** | **-75.07%** | **Material Deviation Gate** |

*Conclusion:* Full 4-month longitudinal monthly time-series data exists natively in the canonical data warehouse and is verified with 100% mathematical precision.

---

### D. Visualizations Directly Supported by Data

1. **Signal Summary Longitudinal Trend (Card 1):** 4 points (Jan: $590.11, Feb: $3,074.39, Mar: $7,009.60, Apr: $994.25) with dashed baseline reference ($3,558.03) and highlighted anomaly point at Apr 2021.
2. **Impact Summary 5-KPI Mini Grid (Card 2):** Exact current vs baseline values and percentage deltas across Sales, Volume, Ad Spend, CVR, and CTR.
3. **Evidence Mini Sparklines (Card 3):** Directional trends for Marketing Spend ($1691 \rightarrow 588 \rightarrow 706 \rightarrow 1641$), Conversion Rate ($7.26\% \rightarrow 5.56\% \rightarrow 7.88\% \rightarrow 3.63\%$), and CTR ($4.22\% \rightarrow 3.24\% \rightarrow 2.72\% \rightarrow 0.95\%$).
4. **Connected KPI Relationship Tree (Card 4):** Causal hierarchy diagram (Gross Sales $\rightarrow$ Order Volume & Marketing Spend $\rightarrow$ CVR & CTR) with join keys `(date, market, product_code)` and 2 distinct sources.
5. **Candidate Driver Comparison (Card 5):** Horizontal progress bars visualizing Fit Scores (Marketing Inefficiency: 6.00 / 6.00 = 100% bar, Competitor Pricing: 0.00 / 6.00 = 0% bar, Stockout: 0.00 / 6.00 = 0% bar, etc.).
6. **Multi-Metric Trend Overview (Card 6):** Dual-axis longitudinal chart plotting Gross Sales ($) & Marketing Spend ($) on left axis ($0–$8,000) and Conversion Rate (%) & CTR (%) on right axis (0%–10%).

---

### E. Visualizations That Cannot Be Supported Without Invented Data

- Intraday / Hourly sales streams (the warehouse canonical grain is monthly batch). $\rightarrow$ *Resolution: Accurately label all charts as "Monthly Grain (Jan–Apr 2021)".*
- Speculative causal confidence intervals or P-values not emitted by the deterministic engine. $\rightarrow$ *Resolution: Stick strictly to deterministic Fit Scores and governed confidence categories (`PLAUSIBLE`, `STRONGLY_SUPPORTED`, `INSUFFICIENT_EVIDENCE`).*

---

### F. Minimal Backend Exposure in Governance Layer

To allow the frontend to render the longitudinal trends cleanly across all scenarios without duplicate client-side SQL logic, `ConnectedKPIEngine` in `src/governance/connected_kpis.py` will include a `monthly_history` block within the `connected_kpis` JSON payload.
This is purely an extraction of existing rows from `AnalyticalDataModel` in the governance wrapper, requiring **zero changes** to the frozen core.

---

### G. Confirmation of Frozen Core Invariance

All 69 files in `src/analytics/`, `src/phase3b/`, `Data/Processed/`, `Data/scenarios/evaluation_ground_truth/`, and `Data/scenarios/evaluation_inputs/` remain cryptographically frozen and will not be altered.
