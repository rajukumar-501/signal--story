# Accenture Decision Intelligence Prototype — Master Project Plan

## 1. Project Objective

The Accenture Decision Intelligence Prototype is an AI-powered enterprise decision-support system designed to autonomously diagnose, explain, and recommend actions for complex business anomalies across global markets, products, channels, and operational dimensions.

The system bridges raw enterprise transactional and operational data (sales, inventory, marketing, competitor pricing, customer support tickets, CRM notes, and sales call transcripts) with causal decision intelligence. It does so by combining a deterministic analytical engine (Phase 3A) that performs mathematically rigorous anomaly detection, candidate generation, evidence scoring, and diagnosis gating, with an evidence-grounded Large Language Model (LLM) reasoning layer (Phase 3B) that synthesizes cross-functional evidence, interprets unstructured text, evaluates competing hypotheses, and delivers transparent, hallucination-free business narratives.

---

## 2. Architecture Overview

The end-to-end architecture follows a strictly layered, unidirectional pipeline:

```
[Raw & Synthetic Master Data]
       │
       ▼ (Phase 1: Preprocessing & Cleaning)
[Canonical Datasets (Data/Processed/)]
       │
       ├─────────────────────────────────────────┐
       ▼ (Phase 2A & 2B: Scenarios & Truth)      ▼ (Phase 3A: Deterministic Engine)
[Evaluation Inputs & Isolated Ground Truth]  [Analytical Data Model & Event Detector]
       │                                         │
       │                                         ▼
       │                                     [Candidate Generators & Scope Filter]
       │                                         │
       │                                         ▼
       │                                     [Evidence Scorer & Contradiction Engine]
       │                                         │
       │                                         ▼
       │                                     [Driver Ranker & Diagnosis Gate]
       │                                         │
       │                                         ▼
       │                                     [Phase 3A Structured Output Contract]
       │                                         │
       │                                         ▼ (Phase 3B: Reasoning Layer)
       │                                     [Input Contract & Evidence Indexing]
       │                                         │
       │                                         ▼
       │                                     [Prompt Builder & Context Constructor]
       │                                         │
       │                                         ▼
       │                                     [LLM Provider / Model Arbitration]
       │                                         │
       │                                         ▼
       │                                     [Response Validator & Output Formatter]
       │                                         │
       ▼                                         ▼
[Evaluation Harness (tests/)] ◄────────────── [Final Validated Diagnostic Payload]
                                                 │
                                                 ▼ (Future Prototype Phase)
                                             [Decision Intelligence UI / UX Demo]
```

### Component Implementation Status:
- **Implemented & Frozen**:
  - Phase 1 Data Foundation (`src/data/preprocess.py`, `Data/Processed/`)
  - Phase 2A/2B/2B.1/2B.2 Evaluation Framework (`Data/scenarios/`, `tests/test_phase2b_remediation.py`, `tests/test_evidence_traceability.py`)
  - Phase 3A Deterministic Analytical Backend (`src/analytics/`, `tests/test_phase3a*`)
- **Implemented (Foundation / Scaffolding)**:
  - Phase 3B Foundation & Contracts (`src/reasoning/`, `tests/test_phase3b_foundation.py`, `tests/test_phase3b_isolation.py`)
- **Planned / Next Implementation Tasks**:
  - Phase 3B Live LLM Integration & Prompt Engineering for Unstructured Synthesis (CRM/Calls)
  - Phase 3B Multi-Driver Cross-Hypothesis Arbitration (Resolving S001, S002, S006, S007)
  - Phase 3B Live Evaluation Suite against S001–S008 benchmark
  - Hackathon Demo UI / Interactive Dashboard

---

## 3. Phase Status Dashboard

| Phase | Status | Evidence | Remaining Work | Frozen? |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1: Data Foundation & Preprocessing** | COMPLETE / FROZEN | `src/data/preprocess.py`, 10 canonical files in `Data/Processed/`, `docs/data_audit.md`, `docs/data_cleaning_spec.md` | None | **YES** |
| **Phase 2A: Scenario Discovery & Selection** | COMPLETE | `Data/scenarios/scenario_candidate_shortlist.csv`, `Data/scenarios/scenario_discovery_review.md` | None | **YES** |
| **Phase 2B: Scenario Ground Truth & Evidence** | COMPLETE | `Data/scenarios/ground_truth.csv`, `Data/scenarios/S001_evidence.csv`–`S008_evidence.csv`, `docs/phase2b_report.md` | Superseded by 2B.1/2B.2 | **YES** |
| **Phase 2B.1: Ground Truth Remediation** | COMPLETE | `Data/scenarios/evaluation_inputs/`, `Data/scenarios/evaluation_ground_truth/`, `docs/phase2b_remediation_report.md` | None | **YES** |
| **Phase 2B.2: Final Evaluation Hardening** | COMPLETE / FROZEN | `tests/test_phase2b_remediation.py` (19 passing assertions), `tests/test_evidence_traceability.py`, `docs/phase2b_final_validation.md` | None | **YES** |
| **Phase 3A.1: Deterministic Engine Baseline** | COMPLETE | `src/analytics/` (initial pipeline), `Data/evaluation/phase3a_baseline_results.csv`, `docs/phase3a_report.md` | Superseded by 3A.2/3A.3 | **YES** |
| **Phase 3A.2: Analytical Correctness Hardening** | COMPLETE | `src/analytics/` (scope filter, peer comparisons, MoM checks), `Data/evaluation/phase3a2_results.csv`, `docs/phase3a2_report.md` | Superseded by 3A.3 | **YES** |
| **Phase 3A.3: Output Contract & Diagnosis Gate** | COMPLETE / FROZEN | `src/analytics/diagnosis.py` (`DiagnosisGate`), `tests/test_phase3a3_diagnosis_contract.py` (12 tests pass), `Data/evaluation/phase3a3_results.csv`, `docs/phase3a3_comparison.md`, `docs/phase3a_final_baseline.md` | None | **YES** |
| **Phase 3B Foundation: Contracts & Isolation** | COMPLETE / FROZEN | `src/phase3b/`, `tests/test_phase3b_foundation.py`, `tests/test_phase3b_isolation.py` | None | **YES** |
| **Phase 3B Live Implementation: LLM Reasoning** | COMPLETE / FROZEN | `src/phase3b/llm_provider.py`, `src/phase3b/engine.py`, S001–S008 Gemini Live Benchmark, `docs/phase3b8c_live_benchmark_report.md` | None | **YES** |
| **Phase 4.1: UI Architecture & Contract** | COMPLETE / APPROVED | 3-view UX architecture, S003 demo flow, `docs/phase4_1_ui_architecture.md` | None | **YES** |
| **Phase 4.2: Decision UI & API Server** | COMPLETE / VERIFIED | `src/server.py`, `app.py`, `static/`, `tests/test_phase4_api.py` (150 tests pass) | None | **YES** |
| **Phase 4.3: Presentation & Final Certification** | COMPLETE / FROZEN | `tests/test_phase4_3_presentation.py` (157 total tests pass), `docs/phase4_3_presentation_report.md` | None | **YES** |

---

## 4. Phase 1 Plan: Data Foundation and Preprocessing

### Objectives
Establish immutable raw data boundaries, clean encodings, synchronize date dimensions across 36 monthly snapshots (`2018-09-01` to `2021-08-01`), accurately model product returns and financial revenue, resolve missing geographic attributes, and publish 10 canonical datasets in `Data/Processed/`.

### Completed Work
- Implemented `src/data/preprocess.py` automated ETL pipeline.
- Handled Windows-1252/Latin-1 encoding in `dim_product.csv` and `dim_customer.csv`, converting byte `\x96` and en-dashes to standard UTF-8 hyphens.
- Normalized date formats from `DD-MM-YYYY HH:MM` in `fact_sales_monthly.csv` to ISO-8601 `YYYY-MM-DD`.
- Modeled return transactions: separated positive transaction values (`Qty < 0`) into `is_return`, `gross_qty`, `return_qty`, `gross_sales_amount`, `return_sales_amount`, and `signed_sales_amount` ($529.87M True Net Revenue vs $883.05M naive sum).
- Imputed missing regional codes for USA and Canada in `dim_market.csv` to `NA`.
- Generated 10 canonical processed datasets in `Data/Processed/` with 100% referential integrity and zero orphaned foreign keys.

### Validation & Artifacts
- Validation profiles: `Data/validation/data_profile.csv`, `Data/validation/data_profile_processed.csv`.
- Documentation: `docs/data_audit.md`, `docs/data_cleaning_spec.md`.

### Acceptance Criteria Met
- [x] All 10 datasets load without encoding errors.
- [x] All fact tables synchronized to identical 36-month timeline.
- [x] `gross_qty - return_qty == Qty` identity holds across 799,962 sales records.
- [x] `gross_sales_amount - return_sales_amount == signed_sales_amount` holds 100%.
- [x] Zero foreign key orphan records across all joins.

### Remaining Work
- None. Phase 1 is COMPLETE and FROZEN.

---

## 5. Phase 2A Plan: Scenario Discovery and Selection

### Objectives
Identify realistic, multi-dimensional business anomaly scenarios across diverse markets, categories, and channels that represent distinct causal root causes and test the limits of decision intelligence.

### Completed Work
- Scanned canonical sales facts to detect significant MoM and baseline revenue shifts.
- Generated candidate scenarios spanning 8 distinct causal patterns: Returns Spike, Channel Mix Shift, Marketing Inefficiency, Competitive Pricing Pressure, Customer Support Deterioration, Category Demand Shift, Product-Mix Relative Share Shift, and Macroeconomic Shock (Uncertainty).
- Shortlisted 8 official evaluation scenarios (S001 through S008).

### Final Scenario Set
1. **S001**: South Korea | Product `A6519160401` | May 2021 | Gross Sales Collapse (Returns Surge).
2. **S002**: South Korea | All Products | Jan 2021 | Gross Sales Drop (Brick & Mortar Channel Shift).
3. **S003**: China | Product `A2520150501` | Apr 2021 | Gross Sales Drop (Marketing Spend Inefficiency / CVR Collapse).
4. **S004**: China | Product `A0621150308` | Jan 2021 | Gross Sales Drop (Competitor Pricing Premium Gap).
5. **S005**: Indonesia | All Products | Mar 2020 | Gross Sales Drop (Customer Support / Regional Service Outage).
6. **S006**: India | Category `Processors` | Mar 2020 | Gross Sales Drop (Category Demand Shift).
7. **S007**: Portugal | Category `Wi fi extender` | Sep 2019 | Category Share Shift (Product-Mix Relative Performance Shift).
8. **S008**: Germany | All Products | Mar 2020 | Gross Sales Collapse (Macroeconomic Shock / Uncertainty Benchmark).

### Validation & Artifacts
- Shortlist and Review: `Data/scenarios/scenario_candidate_shortlist.csv`, `Data/scenarios/scenario_discovery_review.md`.

### Remaining Work
- None. Phase 2A is COMPLETE.

---

## 6. Phase 2B Plan: Scenario Ground Truth and Evidence Construction

### Objectives
Construct verified evidence packets and baseline ground truth for S001–S008.

### Completed Work
- Implemented `src/analytics/scenario_ground_truth.py`.
- Generated initial evidence CSVs `Data/scenarios/S001_evidence.csv` through `S008_evidence.csv`.
- Generated initial ground truth table `Data/scenarios/ground_truth.csv` and summary `Data/scenarios/scenario_summary.csv`.
- Created AI test specification `tests/scenario_ground_truth.json`.
- Documented in `docs/phase2b_report.md` and `docs/scenario_ground_truth_methodology.md`.

### Remaining Work
- Superseded by Phase 2B.1 and 2B.2 remediation.

---

## 7. Phase 2B.1 Plan: Ground-Truth/Evidence Remediation

### Objectives
Remediate initial limitations identified in Phase 2B: sales-centric evidence, risks of ground-truth leakage into evaluation inputs, lack of atomic unstructured evidence, and invalid interpretations of S007 (mix-shift) and S008 (uncertainty).

### Completed Work
- Implemented `src/analytics/remediate_ground_truth.py`.
- Created strict physical segregation:
  - Input directory: `Data/scenarios/evaluation_inputs/` (`S001_input.csv`–`S008_input.csv`), sanitized of oracle fields.
  - Ground truth directory: `Data/scenarios/evaluation_ground_truth/` (`S001_truth.csv`–`S008_truth.csv`).
- Classified evidence records into explicit roles: `OUTCOME`, `DRIVER`, `SUPPORTING`, `CONTRADICTORY`, `CONTEXT`.
- Overhauled S007 to evaluate `category_share` as a relative performance mix-shift.
- Overhauled S008 to formally define `root_cause_status = NOT_ESTABLISHED` to test AI uncertainty handling.
- Published `Data/scenarios/evaluation_input_audit.csv` and `Data/scenarios/evidence_quality_audit.csv`.
- Documented in `docs/phase2b_remediation_report.md`.

### Remaining Work
- None. Complete.

---

## 8. Phase 2B.2 Plan: Final Evaluation Hardening

### Objectives
Establish strict automated validation suites preventing temporal leakage, semantic leakage, data contamination, and ensuring 100% evidence lineage traceability.

### Completed Work
- Implemented `tests/test_phase2b_remediation.py` covering 19 assertions:
  - Validates zero oracle columns (`true_root_cause`, `confidence`, `root_cause_status`) in evaluation inputs.
  - Validates source datasets belong strictly to approved canonical datasets.
  - Enforces temporal cutoff: all evidence timestamped $\le$ `information_cutoff_date`.
  - Scans for semantic leakage and evaluator terms.
  - Enforces explicit mathematical formulas for all computed metrics.
- Implemented `tests/test_evidence_traceability.py`:
  - Verified 100% deterministic links back to canonical datasets and `record_id` attributes.
- Revised causal language hierarchy: `PROVEN` reserved solely for deterministic/interventional logic; observational evidence restricted to `STRONGLY_SUPPORTED`, `PLAUSIBLE`, `NOT_ESTABLISHED`.
- Documented in `docs/phase2b_final_validation.md`.

### Acceptance Criteria Met
- [x] Zero ground truth fields in evaluation inputs.
- [x] Zero temporal leakage beyond event cutoff dates.
- [x] 100% evidence traceability to canonical datasets.
- [x] Both test suites pass with 0 failures.

### Remaining Work
- None. Phase 2B.2 is COMPLETE and FROZEN.

---

## 9. Phase 3A Plan: Deterministic Analytical Engine

### Architecture & Pipeline
Phase 3A is a standalone, deterministic Python analytical backend that operates exclusively on canonical `Data/Processed/` data without access to ground truth.

```
[run_analysis(request)]
         │
         ▼
[AnalyticalDataModel] ── (Loads canonical data, applies dynamic scope join)
         │
         ▼
  [EventDetector] ────── (Computes MoM and 3-month rolling baseline)
         │
         ▼
 [DriverGenerator] ───── (Evaluates 8 candidate generators with role tagging)
         │
         ▼
  [EvidenceScorer] ───── (Calculates composite multi-factor evidence score)
         │
         ▼
[ContradictionEngine] ── (Detects clashing indicators, applies -15 penalty)
         │
         ▼
  [DriverRanker] ─────── (Ranks candidate hypotheses, maps statuses)
         │
         ▼
  [DiagnosisGate] ────── (Applies 7 deterministic gating rules)
         │
         ▼
[DiagnosisFormatter] ─── (Packages frozen JSON output payload)
```

### Key Modules & Capabilities (FROZEN)
1. **`data_model.py` (`AnalyticalDataModel`)**: Single source of truth data loader; provides `apply_scope()` to dynamically join fact tables with `dim_product` and `dim_customer` on demand.
2. **`kpi_engine.py` (`KPIEngine`)**: Computes Gross Sales, True Net Revenue (`SUM(signed_sales_amount)`), Return Rates, Margins, and Category Share.
3. **`event_detector.py` (`EventDetector`)**: Computes MoM changes and 3-month rolling baseline (`mean(prev_1m, prev_2m, prev_3m)`).
4. **`driver_catalog.py`**: Defines standard schemas and requirements for 8 business drivers (`DRIVER_01_INVENTORY` through `DRIVER_08_PRODUCT_MIX`).
5. **`driver_generator.py` (`DriverGenerator`)**: Implements 8 candidate hypothesis generators with peer-comparison checks (e.g. comparing target market decline vs Rest-of-Company peer decline for `DRIVER_07_MARKET`).
6. **`evidence_scorer.py` (`EvidenceScorer`)**: Multi-factor scoring formula:
   $$\text{FinalScore} = (\text{SignalScore} + \text{CorroborationScore}) \times \text{TemporalMultiplier} - \text{ContradictionPenalty}$$
   - Signal Score: $0.0$ to $6.0$ based on magnitude (capped at $0.0$ if no supporting evidence).
   - Corroboration Score: $+3.0$ per additional distinct supporting dataset.
   - Temporal Multiplier: $1.0$ if `BEFORE` or `DURING`; $0.0$ if `AFTER` or `NO_CLEAR_ALIGNMENT`.
   - Contradiction Penalty: $-15.0$ per clashing evidence item.
7. **`contradiction_engine.py` (`ContradictionEngine`)**: Evaluates factual clashes (e.g. marketing spend increase during zero-spend period, or stockout claims when inventory is positive).
8. **`driver_ranker.py` (`DriverRanker`)**: Sorts hypotheses by final score; maps scores to statuses ($\ge 7.0 \rightarrow \text{STRONGLY\_SUPPORTED}$, $\ge 4.0 \rightarrow \text{PLAUSIBLE}$, $< 4.0 \rightarrow \text{NOT\_ESTABLISHED}$).
9. **`diagnosis.py` (`DiagnosisGate`, `DiagnosisFormatter`)**:
   - Gating rules: verifies supporting evidence exists, is driver-specific, temporally aligned, uncontradicted, above score threshold ($\ge 4.0$), and not purely an outcome metric.
   - Decouples `candidate_hypotheses` (preserving all investigated candidates for downstream LLM reasoning) from `diagnosis` (`established_driver`, `overall_status`, `reason`, `confidence`).
10. **`run_analysis.py`**: Clean, zero-leakage production entrypoint.

### Evaluation Progression & Benchmark Results

| Metric | Phase 3A.1 Baseline | Phase 3A.2 Hardened | Phase 3A.3 Final Baseline (FROZEN) |
| :--- | :---: | :---: | :---: |
| **Top-1 Hypothesis Accuracy** | 12.5% (1/8) | 50.0% (4/8) | **50.0% (4/8)** |
| **Top-3 Hypothesis Recall** | 75.0% (6/8) | 87.5% (7/8) | **100.0% (8/8)** |
| **Mean Reciprocal Rank (MRR)** | N/A | N/A | **0.7143** (denominator: 7) |
| **Established Driver Accuracy** | 12.5% (1/8) | 50.0% (4/8) | **50.0% (4/8)** |
| **Status Accuracy** | 50.0% (4/8) | 37.5% (3/8) | **37.5% (3/8)** |
| **Uncertainty Accuracy (S008)** | 0.0% (0/1) | 100.0% (1/1) | **100.0% (1/1)** |

### Frozen Status
> [!IMPORTANT]
> **Phase 3A is 100% FROZEN.** No modifications to analytical logic, KPI formulas, candidate generators, evidence scoring, contradiction rules, or diagnosis gates are permitted without formal authorization.

---

## 10. Phase 3B Plan: Evidence-Grounded LLM Reasoning Layer

Phase 3B is the NEXT major implementation phase. It introduces an LLM reasoning and orchestration layer that sits on top of the frozen Phase 3A deterministic engine.

```
                            ┌─────────────────────────────────────────┐
                            │      Phase 3A Deterministic Engine      │
                            │                (FROZEN)                 │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼ Standard Phase 3A Payload
                            ┌─────────────────────────────────────────┐
                            │    Phase 3B.1: Interface & Isolation    │
                            │    (src/reasoning/input_contract.py)    │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │ Phase 3B.2: Context & Evidence Indexing │
                            │   (src/reasoning/reasoning_context.py)  │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │   Phase 3B.3: LLM Reasoning & Prompts   │
                            │   (prompt_builder.py, llm_client.py)    │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │    Phase 3B.4: Structured Output        │
                            │  Phase 3B.5: Validation & Anti-Halluc.  │
                            │  (response_validator, output_formatter) │
                            └────────────────────┬────────────────────┘
                                                 │
                                                 ▼
                            ┌─────────────────────────────────────────┐
                            │   Phase 3B.6: S001–S008 Benchmarking    │
                            │   Phase 3B.7: UI / UX Demo Integration  │
                            └─────────────────────────────────────────┘
```

### Detailed Subphase Breakdown:

### Phase 3B.1 — Interface and Isolation
- **Objective**: Establish the strict input boundary that ingests Phase 3A output payloads while guaranteeing zero leakage from ground truth.
- **Inputs**: JSON dictionary output from `run_analysis()`.
- **Outputs**: Validated input payload or `InputContractError`.
- **Dependencies**: Frozen Phase 3A engine (`src/analytics/run_analysis.py`).
- **Acceptance Criteria**: Rejects any payload containing forbidden oracle fields (`true_root_cause`, `expected_driver`, etc.); zero imports of ground truth modules.
- **Risks**: Accidental passing of test-fixture keys.
- **Must Remain Unchanged**: All Phase 3A production files in `src/analytics/`.

### Phase 3B.2 — Evidence-Grounded Context Construction
- **Objective**: Index all structured and unstructured evidence items across hypotheses into unique traceable IDs (`EVD-001`, `EVD-002`, ...), format dimensional context, and extract text snippets from CRM notes and call transcripts.
- **Inputs**: Validated Phase 3A dictionary.
- **Outputs**: Typed `ReasoningContext` dataclass.
- **Dependencies**: Phase 3B.1 input validator.
- **Acceptance Criteria**: 100% of candidate evidence items indexed without loss; de-duplicated by dataset + record_id + metric.
- **Risks**: Dropping relevant unstructured context or truncating long text notes.
- **Must Remain Unchanged**: Phase 3A data models.

### Phase 3B.3 — LLM Reasoning Layer & Provider Integration
- **Objective**: Implement prompt construction and pluggable LLM provider client (OpenAI, Anthropic, Gemini, or local models) to perform cross-hypothesis arbitration, unstructured text synthesis, and contradiction resolution.
- **Inputs**: `ReasoningContext` object + user business query.
- **Outputs**: Raw LLM response string conforming to reasoning contract.
- **Dependencies**: Phase 3B.2 context builder.
- **Acceptance Criteria**: Model successfully synthesizes text signals (e.g. S005 service outage, S002 retailer dispute) and arbitrates close hypotheses (S001 Returns vs Marketing, S007 Mix Shift).
- **Risks**: API rate limits, non-deterministic completions, prompt injection.
- **Must Remain Unchanged**: Ground truth isolation rules.

### Phase 3B.4 — Structured Output Contract
- **Objective**: Define and enforce the final output schema: `executive_summary`, `what_happened`, `diagnosis` (`driver`, `status`, `confidence`), `reasoning` (claims + evidence IDs), `supporting_evidence`, `contradictory_evidence`, `uncertainties`, `recommended_next_steps`, and `traceability`.
- **Inputs**: Raw model output.
- **Outputs**: Clean JSON and formatted Markdown report.
- **Dependencies**: Phase 3B.3.
- **Acceptance Criteria**: Conforms 100% to schema; all fields present and correctly typed.
- **Risks**: Partial JSON completions from LLM.
- **Must Remain Unchanged**: Core schema definitions.

### Phase 3B.5 — Evidence and Hallucination Validation
- **Objective**: Validate model output against evidence context before presenting to user.
- **Inputs**: Raw LLM output + `ReasoningContext`.
- **Outputs**: `ValidationResult` (`is_valid`, `errors`, `warnings`, `validated_data`).
- **Dependencies**: Phase 3B.2, 3B.4.
- **Acceptance Criteria**:
  - Rejects any cited `evidence_id` not present in the indexed context.
  - Rejects invalid driver identifiers.
  - Rejects driver establishment if `overall_status == "NOT_ESTABLISHED"`.
  - Verifies that claimed datasets match underlying evidence items.
- **Risks**: Overly aggressive validation rejecting valid phrasing.
- **Must Remain Unchanged**: Phase 3A output values.

### Phase 3B.6 — Evaluation against S001–S008 Benchmark
- **Objective**: Execute the official end-to-end evaluation harness comparing Phase 3A baseline vs Phase 3B LLM-enhanced engine across S001–S008.
- **Inputs**: Evaluation scenarios `S001` through `S008` (from `Data/scenarios/evaluation_inputs/`).
- **Outputs**: Comparative evaluation metrics table and `phase3b_benchmark_results.csv`.
- **Target Metrics (Aspirational Performance Goals)**:
  - Established Driver Accuracy: Aspirational Target $\ge 75.0\%$ (vs 50.0% in 3A.3 frozen baseline).
    > [!IMPORTANT]
    > $\ge 75.0\%$ Established Driver Accuracy is an aspirational performance target. It must be evaluated using the frozen evaluation contract and must not be achieved through scenario-specific tuning, hard-coded answers, ground-truth access, or modifications to Phase 3A heuristics or evaluation inputs.
  - Top-3 Recall: $100.0\%$ (Preserve 3A.3 perfect candidate recall).
  - Uncertainty Accuracy: $100.0\%$ (S008 preserved as `NOT_ESTABLISHED`).
  - Unsupported Claim Rate: $0.0\%$ (Strict zero-hallucination requirement).
  - Evidence Grounding Rate: $100.0\%$ (All claims cite valid indexed evidence).
- **Dependencies**: Phase 3B.1 through 3B.5.
- **Acceptance Criteria**: Evaluator reads ground truth strictly *after* generation; zero leakage during execution.
- **Risks**: LLM regression on already-solved scenarios (S003, S004, S005, S008).
- **Must Remain Unchanged**: Evaluation ground truth datasets.

### Phase 3B.7 — Decision Intelligence UX / Demo Integration
- **Objective**: Provide an interactive decision-support interface (CLI / Web Dashboard / Streamlit) for business analysts to query anomalies, explore evidence graphs, view contradiction alerts, and inspect traceability links.
- **Inputs**: Phase 3B engine endpoints.
- **Outputs**: Interactive user interface.
- **Dependencies**: Phase 3B.6.
- **Acceptance Criteria**: Intuitive navigation, transparent evidence citations, responsive performance.

---

## 11. Final Prototype Plan (Post-Phase 3B)

To deliver the completed hackathon prototype, remaining activities are divided strictly into required correctness work vs optional polish:

### Required for Correctness (P0)
1. **Phase 3B Live LLM Adapter**: Integrate actual LLM API client with temperature=0 and robust error/retry handling.
2. **Unstructured Signal Extraction**: Ensure prompt builders format CRM notes and call transcripts so the LLM disambiguates subtle drivers (e.g. S002, S005).
3. **End-to-End Benchmark Execution**: Run official evaluation across S001–S008 and log results to `Data/evaluation/phase3b_results.csv`.
4. **Hallucination Verification Suite**: Automated verification that no generated claim lacks an evidence citation.

### Optional Polish (P1 / P2)
1. **Interactive Web UI**: Streamlit or Next.js/Vite dashboard featuring interactive KPI drill-down, evidence lineage explorer, and scenario selectors.
2. **Exportable PDF / Markdown Briefings**: Formatted executive decision briefs ready for enterprise leadership.
3. **Token / Cost Optimization**: Prompt compression and token usage tracking.
4. **Latency Caching**: Cache deterministic Phase 3A payloads for instant re-querying during live demonstrations.
