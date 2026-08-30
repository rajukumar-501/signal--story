# Phase 3B Controlled Foundation Report

## 1. Executive Summary & Architecture
Phase 3B introduces the **Evidence-Grounded Reasoning Layer** for the Accenture Decision Intelligence platform. Its role is to synthesize structured Phase 3A analytics output, explain business causality, resolve cross-hypothesis trade-offs, and produce transparent, validated diagnostic narratives without modifying Phase 3A deterministic logic, accessing ground truth, or hallucinating evidence.

```
                           ┌─────────────────────────────────────────┐
                           │      Phase 3A Deterministic Engine      │
                           │                (FROZEN)                 │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼ Standard Phase 3A Payload
                           ┌─────────────────────────────────────────┐
                           │       src/reasoning/input_contract      │
                           │   • Ground-Truth Rejection Boundary     │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │      src/reasoning/reasoning_context    │
                           │   • Evidence ID Indexing (EVD-001)      │
                           │   • Typed ReasoningContext Dataclasses  │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │       src/reasoning/prompt_builder      │
                           │   • System Anti-Hallucination Rules     │
                           │   • Structured Evidence Catalog         │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │        src/reasoning/llm_client         │
                           │   • LLMProvider / MockLLMProvider       │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼ Raw Model Output
                           ┌─────────────────────────────────────────┐
                           │     src/reasoning/response_validator    │
                           │   • Evidence ID & Schema Verification   │
                           │   • Uncertainty & Gating Integrity      │
                           └────────────────────┬────────────────────┘
                                                │
                                                ▼ Validated Diagnostic Object
                           ┌─────────────────────────────────────────┐
                           │      src/reasoning/output_formatter     │
                           │   • JSON & Markdown Report Formats      │
                           └─────────────────────────────────────────┘
```

---

## 2. Phase 3A $\rightarrow$ Phase 3B Interface

Phase 3B ingests the exact frozen JSON structure emitted by `run_analysis()`:
- `event`: Anomaly description, KPI name, current value, previous month value, baseline value, MoM change %, baseline change %, and `baseline_status` (`"VALID"` / `"INVALID"`).
- `candidate_hypotheses`: Ordered list of driver hypotheses containing `driver`, `rank`, `score`, `status`, `confidence`, `evidence`, `contradictions`, `temporal_alignment`, and source counts.
- `diagnosis`: Gated result containing `established_driver`, `overall_status`, `reason`, and `confidence`.
- `limitations`: Contextual limitations of the observational telemetry.

---

## 3. Allowed vs. Forbidden Inputs Boundary

### A. Allowed Inputs
- Phase 3A deterministic output payloads (`event`, `candidate_hypotheses`, `diagnosis`, `limitations`).
- Structured and textual evidence items extracted by Phase 3A (`metric`, `value`, `source_dataset`, `date`, `record_id`, `evidence_role`, `temporal_alignment`).
- User business query string.

### B. Forbidden Inputs (Strictly Prohibited & Validated)
- Evaluation ground truth directory: `Data/scenarios/evaluation_ground_truth/`.
- Master evaluation files: `Data/scenarios/ground_truth.csv`, `tests/scenario_ground_truth.json`.
- Oracle / Evaluator fields: `true_root_cause`, `root_cause_status`, `expected_driver`, `expected_established_driver`, `scenario_truth`, `target_cause`.
- Direct invocation / prompt embedding of scenario expected answers.

---

## 4. Reasoning Contract & Task Definition

The reasoning layer is explicitly constrained to address seven core analytical questions:
1. **What happened?** (Factual anomaly description and baseline delta).
2. **What is the strongest supported explanation?** (Top-ranked causal driver or uncertainty statement).
3. **What evidence supports it?** (Cross-dataset metrics and citations).
4. **What evidence contradicts it?** (Conflicting signals, stockout clashes, or price inversions).
5. **How strong is the evidence?** (Adherence to `STRONGLY_SUPPORTED`, `PLAUSIBLE`, `NOT_ESTABLISHED`).
6. **What remains uncertain?** (Unobserved variables, macroeconomic factors, or data gaps).
7. **What should the analyst investigate next?** (Actionable operational next steps).

---

## 5. Output Contract Schema

```json
{
  "executive_summary": "High-level 2-3 sentence executive synthesis.",
  "what_happened": "Factual description of the anomaly magnitude and baseline comparison.",
  "diagnosis": {
    "driver": "DRIVER_03_MARKETING",
    "status": "PLAUSIBLE",
    "confidence": "MEDIUM"
  },
  "reasoning": [
    {
      "claim": "Marketing spend increased by 35% without proportional sales yield.",
      "evidence_ids": ["EVD-001"],
      "explanation": "Paid marketing telemetry in fact_marketing_monthly demonstrates spend expansion during a period of conversion decline."
    }
  ],
  "supporting_evidence": [
    {
      "evidence_id": "EVD-001",
      "source_dataset": "fact_marketing_monthly",
      "metric": "spend_change",
      "finding": "Marketing spend rose 35% in event month."
    }
  ],
  "contradictory_evidence": [],
  "uncertainties": [
    "Unobserved macro competitor promotions are not present in telemetry."
  ],
  "recommended_next_steps": [
    "Audit marketing channel efficiency on paid campaigns."
  ],
  "traceability": [
    {
      "evidence_id": "EVD-001",
      "source_dataset": "fact_marketing_monthly",
      "record_id": null
    }
  ],
  "validation_status": "PASSED"
}
```

---

## 6. Evidence Traceability & Anti-Hallucination Controls

1. **Global Evidence Indexing**: `ReasoningContextBuilder` extracts all evidence items across hypotheses, de-duplicates by unique signature, and assigns unique IDs (`EVD-001`, `EVD-002`, ...).
2. **Citation Validation**: `ResponseValidator` verifies that every `evidence_id` cited in `reasoning`, `supporting_evidence`, `contradictory_evidence`, or `traceability` belongs to `context.all_evidence`.
3. **Dataset Verification**: Validates that cited dataset names match the underlying indexed evidence item.
4. **Driver Gating Enforcement**: If `context.deterministic_diagnosis.overall_status` is `NOT_ESTABLISHED` due to invalid baseline or insufficient scores, the validator strictly rejects any attempt to fabricate driver certainty.
5. **No Hallucinated Drivers**: Driver IDs must match the approved 8 business drivers or `None`.

---

## 7. Mock LLM Architecture

- `LLMProvider`: Abstract base class declaring `generate(prompt: str) -> str`.
- `MockLLMProvider`: Deterministic provider that parses prompt sections and synthesizes contract-compliant JSON using real indexed evidence IDs. Supports `custom_response` injection for unit test validation of error states.
- Modular foundation ready for pluggable API clients (`OpenAIProvider`, `AnthropicProvider`, etc.).

---

## 8. Test Execution & Results

### A. Phase 3B Foundation Unit & Isolation Tests (`tests/test_phase3b_foundation.py`)
- **TEST 1 (`test_01_consume_phase3a_output`)**: **PASS** (Consumes real Phase 3A payload and produces validated output).
- **TEST 2 (`test_02_no_ground_truth_imports`)**: **PASS** (Zero imports of ground-truth files across `src/reasoning/`).
- **TEST 3 (`test_03_no_ground_truth_file_access`)**: **PASS** (Zero file path references to `evaluation_ground_truth/`).
- **TEST 4 (`test_04_reasoning_context_no_ground_truth_fields`)**: **PASS** (Payloads with oracle keys rejected by `InputContractValidator`).
- **TEST 5 (`test_05_prompt_no_ground_truth_labels`)**: **PASS** (Prompts verified free of oracle labels).
- **TEST 6 (`test_06_reject_unsupported_evidence_id`)**: **PASS** (Hallucinated evidence ID `EVD-999` caught and rejected).
- **TEST 7 (`test_07_reject_invalid_llm_output`)**: **PASS** (Malformed JSON, missing fields, and bad driver IDs rejected).
- **TEST 8 (`test_08_not_established_uncertainty_preserved`)**: **PASS** (Preserves `NOT_ESTABLISHED` and null driver on synthetic inconclusive cases).
- **TEST 9 (`test_09_contradictory_evidence_and_mock_injection`)**: **PASS** (Handles contradictory evidence items correctly).
- **TEST 10 (`test_10_phase3a_integrity_and_outputs_unmodified`)**: **PASS** (Phase 3A deterministic outputs remain 100% identical).

### B. Full Suite Regression Testing
- Ran all 38 tests across the entire codebase (`tests/`).
- **Result**: **38 passed, 0 failed (100% OK)**.

---

## 9. Known Limitations
- The current implementation uses `MockLLMProvider` for deterministic verification. Step 2 will integrate actual LLM vendor APIs and temperature/token configurations.
- Unstructured text snippets from CRM notes and sales calls are indexed as evidence items; semantic disambiguation of complex multi-paragraph transcripts will be evaluated in the reasoning benchmark.

---

## 10. Conclusion & Recommendation for Phase 3B Step 2

The controlled foundation for Phase 3B is fully implemented, verified, isolated, and tested with zero regressions on Phase 3A.

**Recommendation for Step 2**:
1. Connect production LLM provider adapter with prompt caching and token cost tracking.
2. Implement cross-hypothesis arbitration prompts to resolve multi-driver competitive scenarios (e.g. S001 Returns vs Marketing, S002 Channel Shift vs Support).
3. Execute isolated evaluation harness against scenario inputs.
