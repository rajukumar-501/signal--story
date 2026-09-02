# Phase 6.2 — Signal Story Data Audit

**Purpose:** Inventory every existing API response field that can support deterministic narrative generation without inventing new analytical facts.

---

## 1. Signal / Anomaly Fields

Source: `data.phase3a.event`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `kpi` | `phase3a.event.kpi` | `gross_sales` | "Gross Sales fell…" |
| `current_value` | `phase3a.event.current_value` | `994.25` | Actual value in headline |
| `baseline_value` | `phase3a.event.baseline_value` | `3558.03` | 3-month baseline in headline |
| `baseline_change_percent` | `phase3a.event.baseline_change_percent` | `-0.7206` | Direction + magnitude (`-72.06%`) |
| `anomaly_direction` | derived from `baseline_change_percent` | negative | Arrow symbol ↓ / ↑ |
| `date` | `phase3a.event.date` or `request.date` | `2021-04-01` | "in April 2021" |
| `market` | `phase3a.event.market` or `request.market` | `China` | Scope context |
| `product_code` | `request.product_code` | `A2520150501` | Product context |

---

## 2. Baseline Fields

Source: `data.phase3a.event`, `data.connected_kpis.monthly_history`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `baseline_value` | `phase3a.event.baseline_value` | `3558.03` | "vs Jan–Mar baseline" |
| `baseline_periods` | `connected_kpis.monthly_history.periods` | `["Jan 2021","Feb 2021","Mar 2021","Apr 2021"]` | "Jan–Mar 3-Month Baseline" |
| `historical_values (gross_sales)` | `connected_kpis.monthly_history.gross_sales` | `[590.11,3074.39,7009.60,994.25]` | Sparkline / trend chart |
| `anomaly_index` | `connected_kpis.monthly_history.anomaly_index` | `3` | Which period is the anomaly |
| `baseline_methodology` | `kpi_contract.baseline_methodology` | `3-Month Rolling Mean` | Footnote for DOMAIN_ANALYST |
| `materiality_threshold` | `kpi_contract.materiality_threshold` | `15%` | Governance context |

---

## 3. Connected KPI Fields

Source: `data.connected_kpis.connected_kpis[]`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `kpi_id` | `connected_kpis[i].kpi_id` | `order_volume` | KPI identity |
| `display_name` | `connected_kpis[i].display_name` | `Gross Order Volume` | Human label |
| `change_percent` | `connected_kpis[i].change_percent` | `-73.56` | "Order Volume ↓73.6%" |
| `formatted_change` | `connected_kpis[i].formatted_change` | `-73.56%` | Display string |
| `formatted_value` | `connected_kpis[i].formatted_value` | `$994.25` | Actual value display |
| `evidence_role` | `connected_kpis[i].evidence_role` | `DRIVER_SIGNAL` | Role label for evidence chain |
| `status` | `connected_kpis[i].status` | `ANOMALY_DETECTED` | Badge in story |
| `source_dataset` | `connected_kpis[i].source_dataset` | `fact_marketing_monthly.csv` | DOMAIN_ANALYST: source |
| `grain` | `connected_kpis[i].grain` | `Monthly by Market…` | DOMAIN_ANALYST: grain |
| `alignment_dimensions` | `connected_kpis[i].alignment_dimensions` | `["date","market","product_code"]` | DOMAIN_ANALYST: alignment |

All 5 KPIs available: `gross_sales`, `order_volume`, `marketing_spend`, `conversion_rate`, `click_through_rate`.

---

## 4. Evidence Fields

Source: `data.phase3b.supporting_evidence[]`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `evidence_id` | `phase3b.supporting_evidence[i].evidence_id` | `EV-001` | Clickable evidence chip |
| `metric` | `phase3b.supporting_evidence[i].metric` | `marketing_spend` | Metric label |
| `finding` | `phase3b.supporting_evidence[i].finding` | `+64.94% vs baseline` | Observed change |
| `dataset` | `phase3b.supporting_evidence[i].dataset` | `fact_marketing_monthly.csv` | Source reference |
| `role` | `phase3b.supporting_evidence[i].role` | `DRIVER_SIGNAL` | Evidence role |

Also: `phase3b.evidence_trail[]` — grounded claim statements for narrative sentences.

---

## 5. Candidate Driver Fields

Source: `data.phase3a.candidate_drivers[]` and `data.adjusted_candidate_drivers[]`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `driver` | `candidate_drivers[i].driver` | `DRIVER_03_MARKETING` | Driver ID |
| `fit_score` | `candidate_drivers[i].fit_score` | `6.00` | Primary: score badge |
| `reason` | `candidate_drivers[i].reason` | `"Marketing spend…"` | Ruling rationale |
| `status` | derived from rank | `Primary` / `Rejected` | Status chip |

Rank 0 = primary supported driver. Others = alternatives checked.

---

## 6. Contradiction / Rejection Fields

Source: `data.phase3a.candidate_drivers[]` (non-primary entries)

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `driver` | `candidate_drivers[i].driver` | `DRIVER_02_PRICING` | "Competitor Price Undercutting" |
| `fit_score` | `candidate_drivers[i].fit_score` | `0.00` | Score = insufficient support |
| `reason` | `candidate_drivers[i].reason` | `"0.00% price gap"` | Why it was ruled out |

Also: `data.connected_kpis.qualitative_context` — CRM notes, support tickets confirming absence of alternative drivers.

---

## 7. Confidence / Diagnosis Fields

Source: `data.phase3b.diagnosis`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `status` | `phase3b.diagnosis.status` | `PLAUSIBLE` | Confidence badge |
| `driver` | `phase3b.diagnosis.driver` | `DRIVER_03_MARKETING` | Primary driver ID |
| `confidence` | `phase3b.diagnosis.confidence` | `PLAUSIBLE` | Confidence string |
| `explanation` | `phase3b.diagnosis.explanation` | narrative text | Supporting narrative |

---

## 8. Decision Recommendation Fields

Source: `data.decision_governance`

| Field | Path | Example (S003) | Narrative Use |
|---|---|---|---|
| `recommended_action` | `decision_governance.recommended_action` | `"Audit underperforming…"` | "WHAT NEXT" action |
| `required_owner` | `decision_governance.required_owner` | `Marketing Operations Lead` | OWNER chip |
| `affected_business_area` | `decision_governance.affected_business_area` | `Performance Marketing & Growth` | ACTION AREA chip |
| `risk_level` | `decision_governance.risk_level` | `HIGH` | RISK badge |
| `approval_required` | `decision_governance.approval_required` | `true` | "Human Review: Required" |
| `finding_statement` | `decision_governance.finding_statement` | text | Supported explanation sentence |
| `why_it_matters` | `decision_governance.why_it_matters` | text | Business implication |
| `causal_language_class` | `decision_governance.causal_language_class` | `SUPPORTED_INFERENCE` | Language precision gate |
| `human_review.status` | `decision_governance.human_review.status` | `NOT_REVIEWED` | Review state |

---

## 9. Persona Fields

Source: `data.persona_view`

| Field | Path | Narrative Use |
|---|---|---|
| `active_persona` | `persona_view.active_persona` | Routes to EXECUTIVE vs ANALYST story depth |
| `summary` | `persona_view.summary` | Pre-built narrative for each persona |
| `finding_statement` | `persona_view.finding_statement` | Persona-adapted finding |
| `recommended_action` | `persona_view.recommended_action` | Persona-adapted action |
| `emphasis_levers` | `persona_view.emphasis_levers` | DOMAIN_ANALYST: z-score, funnel mechanics, contradiction matrix |
| `detail_level` | `persona_view.detail_level` | `EXECUTIVE_SUMMARY` vs `DEEP_ANALYTICAL_TRACE` |

---

## 10. Abstention Fields

Source: `data.abstention_governance`

| Field | Path | Example (S008) | Narrative Use |
|---|---|---|---|
| `is_abstaining` | `abstention_governance.is_abstaining` | `true` | Triggers abstention story state |
| `abstention_state` | `abstention_governance.abstention_state` | `NO_ACTION_RECOMMENDED_UNTIL_VALIDATED` | State badge |
| `confidence` | `abstention_governance.confidence` | `NONE` | Confidence: NONE |
| `reasons` | `abstention_governance.reasons[]` | strings | "Why we are abstaining" |
| `required_next_evidence` | `abstention_governance.required_next_evidence[]` | strings | "Evidence needed next" |
| `guidance_statement` | `abstention_governance.guidance_statement` | text | Abstention decision text |

---

## 11. Sparse History Fields

Source: `data.sparse_history`

| Field | Path | Example (S009) | Narrative Use |
|---|---|---|---|
| `is_limited_history` | `sparse_history.is_limited_history` | `true` | Triggers sparse story state |
| `description` | `sparse_history.description` | text | Explanation sentence |
| `baseline_method_applied` | `sparse_history.baseline_method_applied` | `Peer Product Category Benchmark / Contextual Baseline` | Baseline method disclosure |
| `months_available` | `sparse_history.months_available` | `1` | `< 3 mos` disclosure |
| `confidence_impact` | `sparse_history.confidence_impact` | `LOW` | Confidence: LOW |

---

## 12. Entitlement / Redaction Fields

Source: `data.entitlement`

| Field | Path | Use |
|---|---|---|
| `is_redacted` | `entitlement.is_redacted` | Master flag — triggers all story redactions |
| `redacted_fields` | `entitlement.redacted_fields[]` | Which fields: `actual_value`, `baseline_value` |
| `role` | `entitlement.role` | `RESTRICTED_USER` triggers redaction |

Story must check `is_redacted` **before** writing any financial value to the DOM.

---

## 13. AI / LLM Fields

Source: `data.metadata`, `data.phase3b`

| Field | Path | Use |
|---|---|---|
| `metadata.provider` | `metadata.provider` | `gemini` vs `mock` — controls AI banner display |
| `metadata.gemini_configured` | `metadata.gemini_configured` | Whether Gemini API key is set |
| `metadata.validation_status` | `metadata.validation_status` | `FALLBACK_PRESERVED` → use fallback disclaimer |
| `phase3b.executive_summary` | `phase3b.executive_summary` | LLM-generated narrative (already safety-validated by 10-rule gate) |
| `phase3b.validation_status` | `phase3b.validation_status` | `PASSED` or `FALLBACK_PRESERVED` |

---

## Summary Table: Fields Used by Story Stage

| Story Stage | Primary Fields |
|---|---|
| WHAT HAPPENED | `phase3a.event`, `connected_kpis.monthly_history` |
| WHAT CHANGED | `connected_kpis.connected_kpis[]`, `connected_kpis.deterministic_explanation` |
| EVIDENCE CHAIN | `phase3b.supporting_evidence[]`, `phase3b.evidence_trail[]` |
| RULED OUT | `phase3a.candidate_drivers[]` (non-primary), `connected_kpis.qualitative_context` |
| WHAT NEXT | `decision_governance.*`, `phase3b.diagnosis.status` |
| GLANCE TEXT | Synthesized from all above |
| AI NARRATIVE | `phase3b.executive_summary` (if provider=gemini + PASSED) |
| ABSTENTION | `abstention_governance.*` |
| SPARSE | `sparse_history.*` |
| PERSONA | `persona_view.*` |
| REDACTION | `entitlement.*` |
