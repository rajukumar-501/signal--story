# Phase 3B Architectural Specification & Interface Design

## 1. Objective
Phase 3B integrates a Large Language Model (LLM) reasoning and orchestration layer on top of the frozen Phase 3A deterministic engine. The purpose of the LLM is to synthesize multi-source structured evidence, interpret unstructured text (CRM notes and sales call transcripts), evaluate competing hypotheses, explain business causality, and provide actionable next steps—without hallucinating evidence or violating data contracts.

---

## 2. System Architecture

```
                                  [User Business Query]
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │   Phase 3A Deterministic Engine   │
                          │        (Feature Extractor)        │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼ Structured Phase 3A Payload:
                                            • Event Definition
                                            • Ranked Hypotheses
                                            • Structured & Text Evidence
                                            • Temporal Alignments
                                            • Contradictions
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │      Phase 3B Reasoning Engine     │
                          │          (LLM Layer)              │
                          ├───────────────────────────────────┤
                          │  1. Unstructured Text Semantic    │
                          │     Interpretation                │
                          │  2. Cross-Hypothesis Arbitration  │
                          │  3. Contradiction Resolution      │
                          │  4. Uncertainty & Causal Bounds   │
                          │  5. Actionable Synthesis          │
                          └─────────────────┬─────────────────┘
                                            │
                                            ▼
                           [Phase 3B Final Diagnostic Output]
```

---

## 3. Strict Operating Guardrails for Phase 3B

1. **Zero Ground-Truth Access**: The LLM prompt and context window will strictly exclude ground truth files, evaluation files, and true root-cause labels.
2. **Zero Canonical Data Modification**: The LLM operates strictly in inference mode as an analytic reader; it cannot write or alter database records in `Data/Processed/`.
3. **Zero Fact Fabrication (Anti-Hallucination)**: Every claim, number, and attributed cause in the LLM output must cite an exact evidence item (`source_dataset`, `record_id`, or `metric`) provided by the Phase 3A payload.
4. **Preservation of Uncertainty**: When Phase 3A outputs `overall_status = "NOT_ESTABLISHED"` (e.g. S008) and no unstructured corroboration exists, the LLM must preserve the uncertain diagnosis rather than forcing a root cause.

---

## 4. Input Payload Interface (From Phase 3A to Phase 3B)

The LLM orchestrator receives a standardized JSON input containing:
```json
{
  "user_query": "Explain the gross sales decline for China product A2520150501 in April 2021.",
  "event": {
    "kpi": "gross_sales",
    "current_value": 994.25,
    "previous_month_value": 7009.60,
    "baseline_value": 3558.03,
    "mom_change_percent": -0.8582,
    "baseline_change_percent": -0.7206,
    "baseline_status": "VALID"
  },
  "candidate_hypotheses": [
    {
      "driver": "DRIVER_03_MARKETING",
      "rank": 1,
      "score": 6.0,
      "status": "PLAUSIBLE",
      "temporal_alignment": "DURING",
      "supporting_evidence_count": 2,
      "evidence": [
        {
          "source_dataset": "fact_marketing_monthly",
          "record_id": null,
          "metric": "spend_change",
          "value": 0.40,
          "evidence_role": "SUPPORTING"
        },
        {
          "source_dataset": "fact_marketing_monthly",
          "record_id": null,
          "metric": "conversion_rate_change",
          "value": -0.42,
          "evidence_role": "SUPPORTING"
        }
      ],
      "contradictions": []
    }
  ],
  "phase_3a_diagnosis": {
    "established_driver": "DRIVER_03_MARKETING",
    "overall_status": "PLAUSIBLE",
    "reason": "Driver DRIVER_03_MARKETING established with status PLAUSIBLE."
  },
  "limitations": [
    "Analysis relies entirely on available structured datasets.",
    "Causal status is observational, not interventional."
  ]
}
```

---

## 5. Output Contract for Phase 3B

```json
{
  "diagnosis": {
    "established_driver": "DRIVER_03_MARKETING",
    "status": "STRONGLY_SUPPORTED"
  },
  "ranked_hypotheses": [
    {
      "driver": "DRIVER_03_MARKETING",
      "rank": 1,
      "confidence": "HIGH",
      "summary": "Marketing spend increased by 40% while conversion rates dropped 42%, driving customer acquisition inefficiency."
    },
    {
      "driver": "DRIVER_04_RETURNS",
      "rank": 2,
      "confidence": "LOW",
      "summary": "Return rates showed a minor uptick of 0.5%, insufficient to explain the 85% revenue decline."
    }
  ],
  "evidence_used": [
    {
      "source_dataset": "fact_marketing_monthly",
      "metric": "spend_change",
      "finding": "Marketing budget increased by 40% in event month."
    }
  ],
  "contradictory_evidence": [],
  "reasoning": "Detailed narrative walking through why marketing inefficiency is the primary driver, citing cross-source metrics and ruling out pricing and inventory stockouts.",
  "uncertainty": [
    "External macro-market competitor campaigns during this window are unobserved."
  ],
  "recommended_next_action": "Audit current ad campaigns on paid channels for product A2520150501 to reallocate underperforming spend."
}
```
