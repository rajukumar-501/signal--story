# Phase 4.1 — Backend-to-UI Data Contract & Field Mapping

**Author:** Lead Product Engineer & UX Architect  
**Milestone:** Phase 4.1 (Contract Mapping)  
**Status:** VALIDATED & COMPLETE  
**Project:** Accenture Decision Intelligence Prototype

---

## 1. Contract Flow Paradigm

$$\mathbf{BACKEND\ OUTPUT} \longrightarrow \mathbf{UI\ DATA\ MODEL} \longrightarrow \mathbf{UI\ COMPONENT} \longrightarrow \mathbf{USER\ DECISION}$$

The UI consumes the frozen Phase 3A deterministic output and Phase 3B reasoning report without modifying or recomputing analytical inferences.

---

## 2. Field-by-Field Mapping Specification

### A. Anomaly Detection & Business Context (View 1: Executive Decision)

| Backend Source Module | Backend Source Field | Meaning / Content | Data Classification | UI Component Target | User Decision Enabled |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/analytics/event_detector.py` | `event.kpi` | Target KPI evaluated (e.g. `gross_sales`) | **Observed Evidence** | Anomaly Header Badge | Identifies the impacted business metric |
| `src/analytics/event_detector.py` | `event.current_value` | Actual value during event period ($994.25) | **Observed Evidence** | Metric Stat Display | Measures current performance |
| `src/analytics/event_detector.py` | `event.baseline_value` | Historical reference baseline ($3,558.03) | **Analytical Inference** | Baseline Stat Display | Provides historical baseline comparison |
| `src/analytics/event_detector.py` | `event.change_percent` | Percentage shift (-72.06%) | **Analytical Inference** | Anomaly Magnitude Banner | Assesses severity of anomaly |
| `src/analytics/event_detector.py` | `event.baseline_status` | Baseline validity (`VALID` / `INSUFFICIENT_DATA`) | **Uncertainty** | Reliability Indicator | Confirms statistical validity of baseline |
| `src/phase3b/engine.py` | `what_happened` | Natural language anomaly summary | **Causal Interpretation** | Anomaly Overview Narrative | High-level situation comprehension |

---

### B. Causal Diagnosis & Recommendation (View 1: Executive Decision)

| Backend Source Module | Backend Source Field | Meaning / Content | Data Classification | UI Component Target | User Decision Enabled |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/phase3b/engine.py` | `diagnosis.driver` | Primary root cause identifier (`DRIVER_03_MARKETING`) | **Causal Interpretation** | Primary Driver Hero Card | Directs operational investigation |
| `src/phase3b/engine.py` | `diagnosis.status` | Causal certainty (`STRONGLY_SUPPORTED`, `PLAUSIBLE`, `NOT_ESTABLISHED`) | **Causal Interpretation** | Certainty Badge | Calibrates organizational response urgency |
| `src/phase3b/engine.py` | `diagnosis.confidence` | Confidence level (`HIGH`, `MEDIUM`, `NONE`) | **Causal Interpretation** | Confidence Meter | Sets executive decision threshold |
| `src/phase3b/engine.py` | `executive_summary` | Executive synthesis brief | **Causal Interpretation** | Executive Summary Box | Briefs C-level leadership in seconds |
| `src/phase3b/engine.py` | `recommended_next_steps` | List of targeted operational actions | **Recommendation** | Recommended Action Plan | Dictates concrete corrective actions |

---

### C. Evidence & Hypothesis Arbitration (View 2: Evidence & Reasoning)

| Backend Source Module | Backend Source Field | Meaning / Content | Data Classification | UI Component Target | User Decision Enabled |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/phase3b/engine.py` | `candidate_comparisons` | Array of 8 drivers with alignment & contradiction stats | **Analytical Inference** | Candidate Arbitration Table | Evaluates competing hypotheses |
| `src/phase3b/engine.py` | `candidate_comparisons[i].scope_alignment` | Match level (`MARKET`, `GLOBAL`, `NONE`) | **Observed Evidence** | Scope Match Pill | Verifies geographical exactness |
| `src/phase3b/engine.py` | `candidate_comparisons[i].temporal_alignment` | Timing (`BEFORE`, `DURING`, `AFTER`, `NO_CLEAR_ALIGNMENT`) | **Observed Evidence** | Temporal Role Pill | Confirms cause preceded effect |
| `src/phase3b/engine.py` | `candidate_comparisons[i].contradiction_count` | Penalized contradictory signals count | **Observed Evidence** | Contradiction Counter | Flags conflicting indicators |
| `src/phase3b/engine.py` | `why_selected` | Detailed reasoning for winning driver | **Causal Interpretation** | Winner Rationale Panel | Explains why alternative causes lost |
| `src/phase3b/engine.py` | `why_alternatives_rejected` | List of disqualification reasons for other 7 drivers | **Causal Interpretation** | Rejection Accordion | Prevents chasing false root causes |
| `src/phase3b/engine.py` | `claims` | Granular claims tagged by type and cited `EVD-xxx` IDs | **Causal Interpretation** | Claim Citation Stream | Enables fact-checking of every statement |
| `src/phase3b/engine.py` | `supporting_evidence` | Multi-source evidence records (`EVD-xxx`, dataset, metric, finding) | **Observed Evidence** | Supporting Evidence Cards | Provides raw empirical proof |
| `src/phase3b/engine.py` | `uncertainties` | Boundary limitations and unobserved factors | **Uncertainty** | Uncertainty Callout Box | Exposes analytical assumptions |

---

### D. Decision Trace, Provenance & Trust (View 3: Decision Trace / Trust)

| Backend Source Module | Backend Source Field | Meaning / Content | Data Classification | UI Component Target | User Decision Enabled |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/analytics/diagnosis.py` | `phase3a.diagnosis.established_driver` | Phase 3A deterministic driver | **Analytical Inference** | Baseline Comparison Tile | Audits deterministic baseline |
| `src/analytics/diagnosis.py` | `phase3a.diagnosis.overall_status` | Phase 3A deterministic status | **Analytical Inference** | Baseline Status Tag | Verifies algorithmic certainty |
| `src/phase3b/engine.py` | `validation_status` | Validation outcome (`PASSED`, `FALLBACK_PRESERVED`) | **Provenance / Governance** | 10-Step Safety Status | Confirms zero hallucinations / valid JSON |
| `src/phase3b/engine.py` | `pipeline_latency_ms` | End-to-end execution latency in ms | **Provenance Metadata** | Latency Telemetry Badge | Monitors runtime responsiveness |
| `src/phase3b/engine.py` | `traceability` | Data lineage links (`evidence_id`, `source_dataset`, `record_id`) | **Observed Evidence** | Audit Lineage Table | Guarantees compliance and auditability |

---

## 3. Backend Contract Gap Analysis

- **Inspection Result:** **ZERO CRITICAL BACKEND GAPS DETECTED**.
- All necessary data fields (KPI metrics, baseline deltas, candidate comparisons, claim types, evidence citations, why-rejected rationales, uncertainty statements, and traceability records) are natively generated by the frozen Phase 3A and Phase 3B Python pipelines.
- To serve this data to the web frontend, a lightweight API adapter (`/api/analyze`) will package `{ phase3a: p3a_payload, phase3b: p3b_payload, metadata: {...} }` in a single unified JSON response.
