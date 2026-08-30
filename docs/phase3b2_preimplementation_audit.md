# Phase 3B.2 Pre-Implementation Audit: LLM Reasoning Layer

**Date:** August 30, 2026  
**Status:** COMPLETE / APPROVED FOR IMPLEMENTATION  
**Phase:** Phase 3B.2 (LLM Reasoning Layer Implementation)

---

## 1. Executive Summary

This audit assesses the state of the codebase prior to the implementation of **Phase 3B.2 (LLM Reasoning Layer)**. 
Phase 3B.1 successfully established the versioned input boundary, evidence indexing (`EVD-xxx`), untrusted text sandboxing, deterministic response validation, and zero-dependency mock testing.

The objective of Phase 3B.2 is to build a general-purpose, evidence-grounded LLM reasoning layer that consumes Phase 3B evidence context, constructs structured reasoning requests, executes LLM inference (with full fallback capability), and passes the output through the Phase 3B.1 deterministic safety validator.

---

## 2. Existing Phase 3B.1 Architecture Review

Phase 3B.1 established the following authoritative components under `src/phase3b/`:

```text
                  PHASE 3A — FROZEN DETERMINISTIC BASELINE
                     │ (run_analysis() payload)
                     ▼
             Phase3BInputAdapter (input_adapter.py)
                     │ Enforces Schema v1.0.0 & Rejects Oracle Keys
                     ▼
            EvidenceContextBuilder (evidence_context.py)
                     │ Indexes EVD-001... & Sandboxes Untrusted Text
                     ▼
              ReasoningProvider (reasoning_provider.py)
                     ├── MockReasoningProvider (mock_reasoning_provider.py)
                     └── [New] LLMReasoningProvider (Phase 3B.2)
                     │ Generates Structured Diagnostic JSON
                     ▼
         Phase3BResponseValidator (validator.py)
                     │ 10-Step Deterministic Safety Boundary
                     ├───────────────────────────┐
                     ▼                           ▼
            [ VALID OUTPUT ]            [ INVALID OUTPUT ]
           Grounded Diagnosis          Phase 3A Safe Fallback
```

### Authoritative Phase 3B Directory
* **Authoritative Path:** `src/phase3b/`
* Any legacy prototypes in `src/reasoning/` are historical references; all active, production-grade contracts, adapters, providers, validators, and tests reside strictly in `src/phase3b/`.

---

## 3. Interfaces & Contracts

### A. Phase 3A Input Boundary (`src/phase3b/input_adapter.py`)
* Ingests the dictionary payload returned by Phase 3A `run_analysis()`.
* Schema Version: `1.0.0`, Baseline: `3A.3`.
* Strictly checks for and rejects forbidden oracle keys (`true_root_cause`, `expected_driver`, `ground_truth`, `oracle`) with `InputContractError`.
* Normalizes into `Phase3BInputContract` with typed dataclasses: `ScenarioRequest`, `AnomalyEvent`, `CandidateHypothesis`, `Phase3ADiagnosis`.

### B. Evidence Context (`src/phase3b/evidence_context.py`)
* Standardizes all structured telemetry and qualitative text into discrete `EvidenceItem` records with sequential identifiers (`EVD-001`, `EVD-002`, ...).
* Separates trusted quantitative data from untrusted customer/ticket text via the Untrusted Text Rule (`<UNTRUSTED_EVIDENCE_RECORD ... classification="DATA_NOT_INSTRUCTION">`).

### C. Validator Interface (`src/phase3b/validator.py`)
* `Phase3BResponseValidator.validate(raw_output, context) -> ValidationResult`
* Enforces 10 deterministic checks:
  1. Valid JSON syntax
  2. Required top-level keys (`executive_summary`, `what_happened`, `diagnosis`, `supporting_evidence`, `contradictory_evidence`, `uncertainties`, `recommended_next_steps`, `traceability`)
  3. Approved driver catalog membership (8 drivers or `None`)
  4. Enum validation for `status` and `confidence`
  5. Uncertainty gating (strict enforcement of `NOT_ESTABLISHED` if Phase 3A returned null driver)
  6. Claim-level grounding (every observation/causal conclusion must cite valid `evidence_ids`)
  7. Evidence ID existence
  8. Source dataset lineage match
  9. Contradiction integrity
  10. Deterministic safe fallback generation via `get_safe_fallback(context, reason)`.

### D. Provider Interface (`src/phase3b/reasoning_provider.py`)
* Abstract Base Class: `ReasoningProvider`
* Method: `generate_diagnosis(context: EvidenceContext) -> Union[Dict[str, Any], str]`
* Existing Implementation: `MockReasoningProvider` in `src/phase3b/mock_reasoning_provider.py`.

---

## 4. Proposed Phase 3B.2 Components

1. **`src/phase3b/prompts.py` (Prompt Engineering Layer)**:
   - System prompt defining senior analyst persona, evidence-grounding constraints, and anti-hallucination rules.
   - User prompt builder formatting `EvidenceContext` into structured sections:
     - Event details
     - Candidate hypotheses with metrics & contradictions
     - Indexed evidence catalog with explicit `EVD-xxx` identifiers
     - Sandboxed untrusted text blocks
     - Competing-hypothesis arbitration instructions
     - Strict JSON output schema specification.
   - **Zero Scenario Hardcoding**: Absolute prohibition of S001–S008 answer mappings, scenario IDs, or benchmark-specific rules.

2. **`src/phase3b/llm_provider.py` (Live LLM Reasoning Provider)**:
   - Implements `LLMReasoningProvider(ReasoningProvider)`.
   - Environment-based configuration: `LLM_PROVIDER` (e.g., `gemini`, `openai`, `anthropic`, `generic_http`, `mock`), `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_TEMPERATURE` (default 0.0), `LLM_TIMEOUT` (default 30s).
   - Zero hardcoded secrets; graceful missing-key handling.
   - Clean HTTP / API invocation with JSON extraction and retry handling.
   - Fallback on API timeout/failure to safe baseline payload.

3. **`src/phase3b/engine.py` (Phase 3B Reasoning Orchestrator)**:
   - Provides end-to-end orchestration: `analyze_and_reason(scenario_dict, provider=None) -> Dict[str, Any]`.
   - Pipeline: `Phase3BInputAdapter.from_phase3a_output()` -> `EvidenceContextBuilder.build_context()` -> `provider.generate_diagnosis()` -> `Phase3BResponseValidator.validate()` -> Output or Fallback.

4. **Phase 3B.2 Test Suites under `tests/`**:
   - `tests/test_phase3b2_provider.py`: Provider abstraction, configuration, mock fallback, error handling.
   - `tests/test_phase3b2_prompts.py`: Prompt structure, evidence grounding rules, anti-leakage audit (no S001–S008 answers).
   - `tests/test_phase3b2_engine.py`: End-to-end pipeline execution with Mock & LLM providers.
   - `tests/test_phase3b2_security_isolation.py`: AST scans for ground-truth isolation, injection protection, and credential security.

---

## 5. Protected Assets (Strictly Frozen)

| Asset Category | Paths / Components | Freeze Policy |
| :--- | :--- | :--- |
| **Phase 3A Analytics Engine** | `src/analytics/*` (`data_model.py`, `kpi_engine.py`, `diagnosis.py`, etc.) | **STRICTLY FROZEN** — Do not modify. |
| **Raw & Processed Data** | `Data/raw/*`, `Data/Processed/*` | **STRICTLY FROZEN** — Do not modify. |
| **Evaluation Ground Truth** | `Data/scenarios/evaluation_ground_truth/*`, `ground_truth.csv` | **STRICTLY FROZEN** — Phase 3B must NEVER access. |
| **Evaluation Inputs** | `Data/scenarios/evaluation_inputs/*` | **STRICTLY FROZEN** — Immutable benchmark. |
| **Phase 3A Baseline Results** | `Data/evaluation/phase3a3_results.csv` | **STRICTLY FROZEN** — Historical baseline record. |

---

## 6. Identified Risks & Mitigations

| Risk | Severity | Mitigation Strategy |
| :--- | :---: | :--- |
| **LLM Output Non-Determinism / Flakiness** | Medium | Default temperature to 0.0, use JSON schema enforcement, and rely on `Phase3BResponseValidator` to catch invalid schemas. |
| **Missing API Key in CI / Offline Env** | Low | Provider safely detects missing API key and falls back cleanly or raises informative `ConfigurationError`; tests run with `MockReasoningProvider` by default. |
| **Prompt Injection via CRM/Ticket Text** | High | Untrusted Text Rule ensures raw text is wrapped in `<UNTRUSTED_EVIDENCE_RECORD ... classification="DATA_NOT_INSTRUCTION">` and system instructions explicitly warn against instruction following inside data tags. |
| **Accidental Ground-Truth Leakage** | High | Automated AST and string inspection tests verify zero references to ground-truth files in `src/phase3b/`. |
| **Scenario-Specific Prompt Overfitting** | High | Prompt builder is generic across any enterprise metric/event; unit tests assert zero occurrence of scenario-specific answer keys. |

---

## 7. Approval & Implementation Plan

The pre-implementation audit confirms that all architectural prerequisites from Phase 3B.1 are in place and working. We proceed directly to implementing `src/phase3b/prompts.py`, `src/phase3b/llm_provider.py`, `src/phase3b/engine.py`, and the accompanying Phase 3B.2 test suites.
