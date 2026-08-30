"""
Prompt Builder for Phase 3B LLM Reasoning Engine.
Constructs strictly structured, evidence-grounded prompts without ground-truth contamination.
"""

import json
from typing import Dict, Any
from .reasoning_context import ReasoningContext

class PromptBuilder:
    """
    Builds system instructions and analytical prompts for the LLM reasoning layer.
    """

    @classmethod
    def build_system_instruction(cls) -> str:
        return """You are the Accenture Decision Intelligence Reasoning Engine.
Your role is to evaluate multi-source analytical evidence, explain business anomalies, synthesize candidate causal hypotheses, and provide rigorous, evidence-grounded explanations.

STRICT OPERATING RULES:
1. EVIDENCE TRACEABILITY: Every factual claim about metrics, dates, or business events MUST cite exact evidence IDs (e.g., 'EVD-001') provided in the evidence catalog.
2. ZERO HALLUCINATION: Do NOT invent metrics, numbers, percentages, events, datasets, products, markets, or customers.
3. OBSERVATION VS CAUSATION: Clearly distinguish observational correlation from proven causality. Do not use hyperbolic or speculative claims.
4. UNCERTAINTY PRESERVATION: If evidence is insufficient, contradictory, or if Phase 3A deterministic diagnosis is NOT_ESTABLISHED, explicitly retain 'NOT_ESTABLISHED' status. Never force an unproven root cause.
5. CONTRADICTION TRANSPARENCY: All contradictory or conflicting signals must be explicitly highlighted and evaluated.
6. TEMPORAL BOUNDS: Evidence that occurred after the event must NOT be claimed as the cause of the event.
7. STRICT JSON OUTPUT: Return ONLY a valid JSON object matching the required schema. Do not enclose in markdown ticks if raw JSON is requested."""

    @classmethod
    def build_prompt(cls, context: ReasoningContext) -> str:
        # 1. Format Event Summary
        event_dict = context.event.to_dict()
        event_str = json.dumps(event_dict, indent=2)

        # 2. Format Deterministic Diagnosis
        diag_dict = context.deterministic_diagnosis.to_dict()
        diag_str = json.dumps(diag_dict, indent=2)

        # 3. Format Candidate Hypotheses
        hypotheses_summary = []
        for h in context.candidate_hypotheses:
            hypotheses_summary.append({
                "driver": h.driver,
                "rank": h.rank,
                "score": h.score,
                "status": h.status,
                "confidence": h.confidence,
                "evidence_ids": h.evidence_ids,
                "contradictions": h.contradictions,
                "temporal_alignment": h.temporal_alignment,
                "supporting_evidence_count": h.supporting_evidence_count,
                "contradictory_evidence_count": h.contradictory_evidence_count
            })
        hyp_str = json.dumps(hypotheses_summary, indent=2)

        # 4. Format Evidence Catalog
        evidence_catalog = []
        for eid, item in context.all_evidence.items():
            evidence_catalog.append(item.to_dict())
        ev_str = json.dumps(evidence_catalog, indent=2)

        # 5. Format Limitations
        limitations_str = json.dumps(context.limitations, indent=2)

        # Assemble full prompt
        prompt = f"""=== SECTION 1: BUSINESS QUESTION ===
{context.user_query}

=== SECTION 2: ANOMALY EVENT ===
{event_str}

=== SECTION 3: DETERMINISTIC PHASE 3A DIAGNOSIS ===
{diag_str}

=== SECTION 4: CANDIDATE HYPOTHESES ===
{hyp_str}

=== SECTION 5: EVIDENCE CATALOG ===
{ev_str}

=== SECTION 6: ANALYTICAL LIMITATIONS ===
{limitations_str}

=== SECTION 7: REQUIRED JSON RESPONSE SCHEMA ===
You must respond with a JSON object strictly adhering to this schema:
{{
  "executive_summary": "High-level 2-3 sentence executive synthesis.",
  "what_happened": "Clear factual description of the anomaly, magnitude, baseline comparison, and affected scope.",
  "diagnosis": {{
    "driver": "DRIVER_XX or null",
    "status": "STRONGLY_SUPPORTED | PLAUSIBLE | NOT_ESTABLISHED",
    "confidence": "HIGH | MEDIUM | NONE"
  }},
  "reasoning": [
    {{
      "claim": "Specific factual claim or finding",
      "evidence_ids": ["EVD-001", "EVD-002"],
      "explanation": "Detailed causal or contextual explanation grounded in the cited evidence."
    }}
  ],
  "supporting_evidence": [
    {{
      "evidence_id": "EVD-001",
      "source_dataset": "dataset_name",
      "metric": "metric_name",
      "finding": "Summary of what this evidence shows"
    }}
  ],
  "contradictory_evidence": [
    {{
      "evidence_id": "EVD-003",
      "source_dataset": "dataset_name",
      "metric": "metric_name",
      "finding": "Summary of contradictory or conflicting signal"
    }}
  ],
  "uncertainties": [
    "Specific unobserved factors, data limitations, or alternative explanations"
  ],
  "recommended_next_steps": [
    "Actionable, concrete business investigation or operational next step"
  ],
  "traceability": [
    {{
      "evidence_id": "EVD-001",
      "source_dataset": "dataset_name",
      "record_id": null
    }}
  ]
}}
"""
        return prompt
