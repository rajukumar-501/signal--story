# Phase 3B.3 Pre-Implementation Audit

**Date:** August 30, 2026  
**Status:** COMPLETE & APPROVED  
**Phase:** Phase 3B.3 (Controlled LLM Evaluation & Reasoning Quality Validation)

---

## 1. Current Phase 3B Architecture

The Phase 3B reasoning subsystem operates as an external, decoupled consumer on top of the frozen Phase 3A deterministic analytical engine. Its components are organized under `src/phase3b/`:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                               PHASE 3B ARCHITECTURE                            │
├─────────────────────────┬──────────────────────────────────────────────────────┤
│ Component               │ File & Responsibility                                │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Input Adapter           │ `src/phase3b/input_adapter.py`                       │
│                         │ Ingests Phase 3A JSON payloads, enforces Schema      │
│                         │ v1.0.0, and rejects all forbidden oracle fields.     │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Evidence Context        │ `src/phase3b/evidence_context.py`                    │
│                         │ Builds indexed `EvidenceContext` (`EVD-001`, ...),   │
│                         │ segregates structured vs unstructured telemetry,     │
│                         │ and sandboxes untrusted qualitative text.            │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Prompt Layer            │ `src/phase3b/prompts.py`                             │
│                         │ Generates senior analyst system prompts, formats     │
│                         │ evidence catalogs, instructs hypothesis arbitration,  │
│                         │ and specifies strict JSON output schemas.            │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Reasoning Providers     │ `src/phase3b/reasoning_provider.py` (Base Interface) │
│                         │ `src/phase3b/mock_reasoning_provider.py` (Mock)      │
│                         │ `src/phase3b/llm_provider.py` (Multi-LLM Client)     │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Response Validator      │ `src/phase3b/validator.py`                           │
│                         │ 10-step deterministic safety & grounding boundary.   │
│                         │ Verifies schema, driver IDs, claim citations,        │
│                         │ dataset sources, and uncertainty preservation.       │
├─────────────────────────┼──────────────────────────────────────────────────────┤
│ Pipeline Orchestrator   │ `src/phase3b/engine.py`                              │
│                         │ Coordinates adapter -> context -> provider ->        │
│                         │ validator, returning validated reports or fallbacks. │
└─────────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 2. Current Input Flow

1. An analyst request is executed via `src.analytics.run_analysis.run_analysis(request)`.
2. Phase 3A produces a standardized diagnostic output payload containing:
   - `event`: Anomaly metric telemetry (current value, baseline value, MoM change, baseline change, anomaly status).
   - `candidate_hypotheses`: Ranked candidate drivers with evidence items, role classifications (`OUTCOME`, `SUPPORTING`, `CONTRADICTORY`), temporal alignments, and scores.
   - `diagnosis`: Deterministic gate output (`established_driver`, `overall_status`, `reason`, `confidence`).
   - `limitations`: Contextual analytical boundaries.
3. `Phase3BInputAdapter.from_phase3a_output(payload)` normalizes the payload into a `Phase3BInputContract` instance:
   - Enforces `schema_version = "1.0.0"` and `phase3a_baseline = "3A.3"`.
   - Traverses the entire payload tree to guarantee **zero forbidden oracle keys** (`true_root_cause`, `root_cause_status`, `expected_driver`, `expected_established_driver`, `oracle_driver`, `target_cause`, `scenario_truth`). If any forbidden key is detected, an `InputContractError` is immediately raised.
4. `EvidenceContextBuilder.build_context(contract)` constructs the `EvidenceContext`:
   - Assigns unique, sequential identifiers (`EVD-001`, `EVD-002`, ...) to all evidence items across all hypotheses.
   - Classifies evidence into structured telemetry vs. unstructured text.
   - Enforces the **Untrusted Text Rule**: customer CRM notes, tickets, and sales call transcripts are isolated inside `<UNTRUSTED_EVIDENCE_RECORD ... classification="DATA_NOT_INSTRUCTION">` tags.

---

## 3. Current LLM Output Flow

1. `build_reasoning_prompt_payload(context)` synthesizes:
   - **System Prompt**: Enforces evidence grounding, competing-hypothesis arbitration, claim typing (`OBSERVATION`, `INTERPRETATION`, `CAUSAL_CONCLUSION`, `RECOMMENDATION`), uncertainty gating, and untrusted text sandboxing.
   - **User Prompt**: Supplies the business event telemetry, candidate hypothesis summary, and the indexed `EVD-xxx` evidence catalog.
   - **Generation Parameters**: Pinned to `temperature = 0.0` with JSON object formatting.
2. `LLMReasoningProvider.generate_diagnosis(context)` invokes the configured LLM endpoint (or offline mock) and extracts clean JSON from the completion text.
3. The extracted JSON payload is passed to `Phase3BResponseValidator.validate(raw_output, context)`.

---

## 4. Validator Behavior

`Phase3BResponseValidator` enforces a 10-step deterministic safety boundary:
1. **JSON & Type Parsing**: Validates that the payload is valid JSON and a dictionary.
2. **Top-Level Schema Verification**: Ensures all required keys (`executive_summary`, `what_happened`, `diagnosis`, `claims`, `supporting_evidence`, `contradictory_evidence`, `uncertainties`, `recommended_next_steps`, `traceability`) are present.
3. **Driver Catalog Restriction**: Ensures `diagnosis.driver` belongs strictly to the 8 approved driver IDs or is `null`.
4. **Status & Confidence Controlled Vocabularies**: Ensures status is one of `{STRONGLY_SUPPORTED, PLAUSIBLE, NOT_ESTABLISHED}` and confidence is `{HIGH, MEDIUM, NONE}`.
5. **Uncertainty Gating Enforcement**: If Phase 3A deterministic status is `NOT_ESTABLISHED` (e.g. S008), the validator strictly prohibits establishing any driver (`diagnosis.driver == None` and `status == "NOT_ESTABLISHED"` are strictly required).
6. **Claim-Level Grounding**: Every claim in `claims` must specify a valid `claim_type`. Claims of type `OBSERVATION` and `CAUSAL_CONCLUSION` MUST cite $\ge 1$ valid `evidence_id`.
7. **Citation Existence Check**: Every cited `evidence_id` in claims, supporting evidence, contradictory evidence, and traceability is verified against the `EvidenceContext`. Non-existent IDs (e.g. `EVD-999`) trigger immediate validation failure.
8. **Source Dataset Consistency**: Ensures that cited evidence items correctly specify the exact source dataset (`fact_sales_monthly`, `fact_support_tickets`, etc.) matching their indexed record.
9. **Traceability Lineage**: Validates that traceability items correctly link `evidence_id` to `source_dataset` and `record_id`.
10. **Validation Result Formulation**: Returns `ValidationResult(is_valid=True/False, errors=[...], warnings=[...], validated_data=...)`.

---

## 5. Fallback Behavior

When validation fails or an unhandled provider exception occurs (e.g. API network timeout, bad JSON, unapproved driver ID, hallucinated evidence ID):
1. `Phase3BReasoningEngine` intercepts the failure and invokes `Phase3BResponseValidator.get_safe_fallback(context, reason=...)`.
2. The fallback generator constructs a 100% deterministic, contract-compliant report that:
   - Sets `validation_status = "FALLBACK_PRESERVED"`.
   - Directly preserves the Phase 3A deterministic diagnosis (`established_driver`, `overall_status`, `confidence`).
   - Cites only valid evidence records from the context.
   - Explicitly notes in `uncertainties` and `claims` that automated LLM reasoning failed validation and the deterministic baseline was preserved.
3. Zero invalid or hallucinated claims ever reach the end user.

---

## 6. Security & Isolation Boundaries

1. **Ground-Truth File Isolation**:
   - Zero imports or references to `Data/scenarios/evaluation_ground_truth/`, `ground_truth.csv`, or `scenario_ground_truth.json` in `src/phase3b/`.
   - Verified via static AST file scanning in test suites.
2. **Oracle Key Elimination**:
   - Automatic recursive scanning rejects payloads containing `true_root_cause`, `oracle_driver`, `expected_driver`, etc.
3. **Untrusted Data Sandboxing (Prompt Injection Defense)**:
   - Field text is enclosed in `<UNTRUSTED_EVIDENCE_RECORD>` tags.
   - System prompts instruct the LLM to treat content inside these tags strictly as passive text data, ignoring directives like `"Ignore previous instructions"` or `"Declare DRIVER_01_INVENTORY"`.
4. **Secret Protection**:
   - API keys are loaded strictly from environment variables and never logged or serialized into diagnostic JSON payloads.

---

## 7. Existing Test Suites

Currently, **80 out of 80 tests pass unconditionally (100% OK)**:
- `tests/test_phase3b2_provider.py` (7 tests): Mock and LLM provider configuration, HTTP dispatch, error handling, mock fallback.
- `tests/test_phase3b2_prompts.py` (4 tests): System prompt structure, user prompt generation, untrusted text sandboxing, payload building.
- `tests/test_phase3b2_engine.py` (5 tests): End-to-end pipeline execution, uncertainty handling, fallback on invalid driver, fallback on hallucinated citation.
- `tests/test_phase3b2_security_isolation.py` (4 tests): Ground truth isolation AST scan, runtime execution without truth files, prompt injection defense, secret protection.
- `tests/test_phase3b1_contract.py` (7 tests): Input schema validation, oracle key rejection.
- `tests/test_phase3b1_isolation.py` (5 tests): Isolation checks.
- `tests/test_phase3b1_validation.py` (7 tests): 10-step validator checks.
- `tests/test_phase3b1_injection.py` (3 tests): Injection boundary checks.
- `tests/test_phase3b_isolation.py` (6 tests): Foundation isolation tests.
- `tests/test_phase3b_foundation.py` (10 tests): Foundation pipeline tests.
- `tests/test_phase3a3_diagnosis_contract.py` (12 tests): 7-rule deterministic diagnosis gate tests.
- `tests/test_phase3a2_behavior.py` (10 tests): Scope filter and peer comparison tests.

---

## 8. Frozen Phase 3A Baseline Metrics

The Phase 3A deterministic engine performance across the 8 official evaluation scenarios (S001–S008) is frozen:

| Metric | Frozen Phase 3A Baseline Value | Provenance / Methodology |
| :--- | :---: | :--- |
| **Top-1 Hypothesis Accuracy** | **50.0% (4/8)** | Scenarios S003, S004, S005, S008 match top-1. |
| **Top-3 Hypothesis Recall** | **100.0% (8/8)** | True driver is present in top 2 candidates in all 8 scenarios. |
| **Mean Reciprocal Rank (MRR)** | **0.7143** | Denominator: 7 driver-seeking scenarios ($|Q|=7$). S008 excluded as null/uncertainty test. Reciprocal ranks: S001 (0.5), S002 (0.5), S003 (1.0), S004 (1.0), S005 (1.0), S006 (0.5), S007 (0.5). Sum = 5.0 / 7 = 0.7143. |
| **Established Driver Accuracy** | **50.0% (4/8)** | S003, S004, S005, S008 correctly established. |
| **Status Accuracy** | **37.5% (3/8)** | Strict single-source status capping. |
| **Uncertainty Accuracy (S008)** | **100.0% (1/1)** | S008 correctly yields `NOT_ESTABLISHED`. |

---

## 9. What Phase 3B.3 Will Evaluate

Phase 3B.3 will execute a controlled, reproducible evaluation measuring 5 distinct quality dimensions:
1. **Dimension A — Driver Identification**:
   - Top-1 Driver Accuracy
   - Top-3 Driver Recall
   - Mean Reciprocal Rank (MRR) using the audited $|Q|=7$ methodology.
2. **Dimension B — Diagnosis Quality**:
   - Established-Driver Accuracy
   - Uncertainty Accuracy (S008)
   - Correct `NOT_ESTABLISHED` Handling
   - Incorrect Overclaim Rate
3. **Dimension C — Evidence Faithfulness**:
   - `evidence_grounding_rate` (% of claims citing valid context evidence IDs)
   - `unsupported_claim_rate` (% of claims with zero or hallucinated citations)
   - Temporal sequence verification
   - Source dataset alignment
4. **Dimension D — Causal Reasoning Quality**:
   - Separation of outcome vs. supporting vs. contradictory evidence
   - Correlation vs. causation differentiation
   - Plausible vs. strongly supported confidence attribution
5. **Dimension E — Decision Explanation Quality**:
   - Structured diagnostic narrative completeness (what happened, most supported driver, rationale, supporting/contradictory evidence, uncertainties, recommended next action).

---

## 10. Explicit Prohibitions for Phase 3B.3

The following actions are **STRICTLY PROHIBITED**:
- **DO NOT** modify Phase 3A analytical engine logic (`src/analytics/*`).
- **DO NOT** modify Phase 3A KPI calculations, driver generators, ranking logic, or diagnosis gate.
- **DO NOT** modify canonical processed datasets (`Data/Processed/*.csv`) or raw datasets (`Data/raw/`).
- **DO NOT** modify evaluation inputs (`Data/scenarios/evaluation_inputs/*.csv`).
- **DO NOT** modify evaluation ground truth (`Data/scenarios/evaluation_ground_truth/*` or `ground_truth.csv`).
- **DO NOT** tune prompts specifically to make scenarios S001–S008 pass.
- **DO NOT** hard-code scenario IDs (e.g. `if scenario_id == 'S001'`) into LLM prompts or reasoning logic.
- **DO NOT** alter the MRR formula or change the frozen denominator.
- **DO NOT** change or overwrite frozen Phase 3A baseline metrics.
- **DO NOT** proceed to Phase 3C without full evaluation and user review.
