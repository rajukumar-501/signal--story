# Phase 3B.4 Pre-Implementation Audit — LLM Reasoning Arbitration & Causal Hardening

**Date:** August 30, 2026  
**Status:** COMPLETE / APPROVED FOR IMPLEMENTATION  
**Author:** Principal ML Evaluation & AI Safety Engineer  
**Reference Version:** Phase 3B.3 Baseline

---

## Executive Summary

This pre-implementation audit analyzes the existing Phase 3B reasoning pipeline, its integration with Phase 3A, and why the current reasoning layer preserved Phase 3A ranking decisions without actively arbitrating between competing hypotheses. This document answers the 14 mandatory architectural questions and defines the generalized evidence-arbitration protocol for Phase 3B.4.

---

## Architectural Analysis: 14 Mandatory Questions

### 1. How does Phase 3A produce candidate hypotheses?
Phase 3A uses deterministic analytical routines:
- `event_detector.py` identifies anomalous KPI shifts (>2.0 std dev or significant MoM delta).
- `driver_generator.py` queries 8 specialized driver catalog engines (Inventory, Pricing, Marketing, Returns, Support, Customer, Market, Product Mix) across canonical processed tables.
- `evidence_scorer.py` computes raw evidence scores based on statistical thresholds.
- `contradiction_engine.py` checks for conflicting indicators (e.g. positive marketing ROI while sales drop).
- `driver_ranker.py` sorts candidates in descending order of score, with score ties broken by driver registration order.
- `diagnosis.py` (`DiagnosisGate`) applies 7 deterministic gating rules to establish the top driver or declare `NOT_ESTABLISHED`.

### 2. What information is passed to the LLM?
The LLM receives a sanitized, structured `EvidenceContext` containing:
- **Scenario Request Scope:** `market`, `product_code`, `category`, `channel`, `date`.
- **Anomaly Event Telemetry:** Target `kpi`, `current_value`, `previous_month_value`, `baseline_value`, `mom_change_percent`, `baseline_change_percent`, `baseline_status`.
- **Preliminary Candidate Hypotheses:** Ordered list of screened hypotheses (`driver`, `rank`, `score`, `status`, `confidence`, `temporal_alignment`, `evidence_ids`, `contradictions`).
- **Phase 3A Diagnosis:** Preliminary `established_driver`, `overall_status`, `confidence`.
- **Indexed Evidence Catalog:** Multi-source records assigned sequential IDs (`EVD-001`, `EVD-002`, ...), including `source_dataset`, `metric`, `value`, `date`, `evidence_role` (`SUPPORTING` vs `CONTRADICTORY`), and `temporal_alignment` (`BEFORE`, `DURING`, `AFTER`).
- **Sandboxed Untrusted Text:** Customer notes and support tickets wrapped in `<UNTRUSTED_EVIDENCE_RECORD ... classification="DATA_NOT_INSTRUCTION">`.
- **Data Limitations:** Known data boundaries or unobserved macro fields.

### 3. What information is intentionally NOT passed?
To prevent data contamination and guarantee evaluation integrity, the following are strictly excluded:
- Ground-truth oracle labels (`expected_driver`, `oracle_driver`, `true_root_cause`, `root_cause_status`).
- Files located in `Data/scenarios/evaluation_ground_truth/`.
- Benchmark evaluation criteria or test scenario designations (`S001`–`S008`).
- Internal developer prompts or test fixture assertions.

### 4. How does the LLM currently rank candidates?
In Phase 3B.2/3B.3, the system prompt asked the model to identify the best candidate, but did not require an explicit pairwise comparison matrix or differential scoring mechanism. Consequently, the default fallback and mock implementations mirrored Phase 3A's preliminary candidate ordering, and prompt guidance lacked explicit comparative decision rules.

### 5. How does the LLM currently use evidence?
Evidence items are cited at the claim level (`claims[].evidence_ids`). The model associates evidence with the top driver, itemizes findings in `supporting_evidence`, and verifies that cited `evidence_id`s exist in the Evidence Catalog.

### 6. How does it distinguish supporting vs contradictory evidence?
The `EvidenceContextBuilder` assigns `evidence_role = "SUPPORTING"` or `"CONTRADICTORY"` based on directional alignment with the KPI anomaly. In the current output, contradictory findings are listed in `contradictory_evidence`, but there was no explicit protocol penalizing a candidate's confidence based on contradiction severity.

### 7. How does it reason about temporal alignment?
`EvidenceItem` records carry `temporal_alignment` tags (`BEFORE`, `DURING`, `AFTER`). However, the previous prompt merely instructed the model that "causes must precede or coincide with outcomes," without explicitly penalizing `AFTER` evidence or rewarding preceding lead indicators during candidate comparison.

### 8. How does it reason about scope?
Evidence records carry market, category, product, and channel attributes. Previously, the prompt did not require the model to explicitly evaluate whether evidence was exact-scope (matching target product/market) versus broad-scope (market-wide or category-wide).

### 9. How does it reason about magnitude?
The prompt provided numeric values and percentage changes, but did not provide a comparative rule asking whether the observed driver anomaly was of sufficient economic magnitude to explain the target KPI drop.

### 10. How does it compare candidates against each other?
Currently, candidates were evaluated largely in isolation: the model explained the winning candidate's evidence, but did not systematically document *why Candidate A was preferred over Candidate B* or *why Candidate B was rejected*.

### 11. How does it handle uncertainty?
`Phase3BResponseValidator` enforces that if Phase 3A determined `NOT_ESTABLISHED`, the LLM cannot establish a driver (`driver = null`, `status = NOT_ESTABLISHED`). In ambiguous cases where Phase 3A established a driver, the LLM had the freedom to downgrade status to `PLAUSIBLE` or `NOT_ESTABLISHED` if evidence was weak.

### 12. How does the validator constrain the output?
`Phase3BResponseValidator` applies 10 deterministic checks:
1. Valid JSON schema.
2. Top-level keys present.
3. Driver in approved 8-driver catalog or null.
4. Status in `STRONGLY_SUPPORTED`, `PLAUSIBLE`, `NOT_ESTABLISHED`.
5. Confidence in `HIGH`, `MEDIUM`, `NONE`.
6. Uncertainty gating invariant (if Phase 3A is `NOT_ESTABLISHED`, driver must be null).
7. Claim structure valid with allowed `claim_type`.
8. Observation and causal claims must have $\ge 1$ cited `evidence_id`.
9. All cited `evidence_id`s must exist in the context.
10. All cited source datasets must match the actual dataset of the indexed evidence item.

### 13. Why can the current architecture preserve a Phase 3A mistake?
When Phase 3A ranks a suboptimal candidate at Rank 1 (e.g. because of a tie-breaking rule or slightly higher statistical anomaly in a secondary metric), the LLM prompt did not force a structured cross-candidate arbitration. Without a comparative deduction protocol, the reasoning layer simply rationalized the Rank 1 candidate.

### 14. Which reasoning weakness is generalizable rather than scenario-specific?
The generalizable weakness is the **absence of a structured pairwise arbitration protocol**. In complex real-world analytics, multiple drivers show anomalies simultaneously. To determine true causality, an analyst must systematically evaluate:
1. **Scope Exactness:** Direct product/market match > broad aggregate match.
2. **Temporal Precedence:** Preceding/coinciding events > lagging indicators.
3. **Independent Corroboration:** Multi-dataset triangulation > single-source volume.
4. **Contradiction Discounting:** Penalizing candidates with clashing operational data.
5. **Direct Comparative Justification:** Explicitly articulating why the winner outranks the closest alternative.

---

## General Evidence-Arbitration Protocol Design

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        6-STEP GENERAL ARBITRATION PROTOCOL                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 1: DEFINE THE OUTCOME                                                             │
│   • Identify target metric, period, market, scope, and baseline delta.                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 2: INSPECT EVERY CANDIDATE HYPOTHESIS                                             │
│   • A. Scope Match (Exact vs Broad vs Out-of-Scope)                                    │
│   • B. Temporal Alignment (BEFORE / DURING > AFTER / NO_ALIGNMENT)                     │
│   • C. Magnitude & Explanatory Power (Plausible economic explanation)                  │
│   • D. Directional Consistency (Mechanistically explains the drop)                    │
│   • E. Independent Corroboration (Multi-dataset support: Sales + Support, etc.)        │
│   • F. Contradictory Evidence (Disqualifying or discounting factors)                   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 3: FORCE DIRECT CANDIDATE COMPARISON                                              │
│   • Compare top candidates pairwise across the 6 dimensions.                           │
│   • Explicitly articulate "Why Selected" and "Why Alternatives Rejected".              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 4: CALIBRATED CAUSAL LANGUAGE                                                     │
│   • Distinguish STRONGLY_SUPPORTED vs PLAUSIBLE vs NOT_ESTABLISHED.                    │
│   • Do not confuse correlation with causation.                                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 5: PRESERVE UNCERTAINTY GATING                                                    │
│   • If evidence is insufficient, broad, or confounded, return NOT_ESTABLISHED.         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ STEP 6: STRUCTURED AUDITABLE OUTPUT                                                    │
│   • Return backward-compatible candidate comparison fields with 100% citation lineage. │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Anti-Overfitting Safeguards

1. **No Scenario IDs:** The prompt and arbitration engine will not inspect `scenario_id` or test labels.
2. **No Hardcoded Geographies or SKUs:** No conditional branches for specific countries (`South Korea`, `China`, `Germany`) or product codes (`A6519160401`, etc.).
3. **Generalized Heuristics:** All comparison rules operate on domain-agnostic properties: scope match level (`EXACT`, `CATEGORY`, `MARKET`, `GLOBAL`), temporal alignment category, dataset count, and contradiction count.
4. **Generalization Holdouts:** Tested on synthetic non-official evidence configurations to confirm universal applicability.
