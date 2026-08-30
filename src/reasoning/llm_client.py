"""
LLM Provider Abstraction and Mock Implementation.
Decouples the reasoning engine from specific LLM vendors and provides deterministic test providers.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class LLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generates a text completion given a prompt."""
        pass

class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM Provider for foundation testing.
    Can operate in automatic synthesis mode (producing compliant JSON from the prompt)
    or custom injection mode (returning pre-configured responses for test fixtures).
    """

    def __init__(self, custom_response: Optional[str] = None):
        self.custom_response = custom_response

    def set_custom_response(self, response: Optional[str]) -> None:
        self.custom_response = response

    def generate(self, prompt: str) -> str:
        if self.custom_response is not None:
            return self.custom_response

        # Automatic synthesis mode: parse evidence & diagnosis from prompt sections
        # 1. Extract Event
        event_match = re.search(r"=== SECTION 2: ANOMALY EVENT ===\s*(\{.*?\})\s*===", prompt, re.DOTALL)
        event_data = json.loads(event_match.group(1)) if event_match else {}

        # 2. Extract Phase 3A Diagnosis
        diag_match = re.search(r"=== SECTION 3: DETERMINISTIC PHASE 3A DIAGNOSIS ===\s*(\{.*?\})\s*===", prompt, re.DOTALL)
        diag_data = json.loads(diag_match.group(1)) if diag_match else {}

        # 3. Extract Hypotheses
        hyp_match = re.search(r"=== SECTION 4: CANDIDATE HYPOTHESES ===\s*(\[.*?\])\s*===", prompt, re.DOTALL)
        hyp_list = json.loads(hyp_match.group(1)) if hyp_match else []

        # 4. Extract Evidence Catalog
        ev_match = re.search(r"=== SECTION 5: EVIDENCE CATALOG ===\s*(\[.*?\])\s*===", prompt, re.DOTALL)
        ev_list = json.loads(ev_match.group(1)) if ev_match else []

        established_driver = diag_data.get("established_driver")
        overall_status = diag_data.get("overall_status", "NOT_ESTABLISHED")
        confidence = diag_data.get("confidence", "NONE")
        kpi = event_data.get("kpi", "KPI")
        change_pct = event_data.get("change_percent", 0.0)

        # Build supporting evidence list from actual evidence items
        supporting_evidence = []
        contradictory_evidence = []
        traceability = []
        reasoning_claims = []

        if established_driver and hyp_list:
            top_hyp = next((h for h in hyp_list if h.get("driver") == established_driver), hyp_list[0])
            for eid in top_hyp.get("evidence_ids", []):
                ev_item = next((e for e in ev_list if e.get("evidence_id") == eid), None)
                if ev_item:
                    role = ev_item.get("evidence_role")
                    if role == "SUPPORTING":
                        supporting_evidence.append({
                            "evidence_id": eid,
                            "source_dataset": ev_item.get("source_dataset"),
                            "metric": ev_item.get("metric"),
                            "finding": f"{ev_item.get('metric')} showed significant movement ({ev_item.get('value')}) in {ev_item.get('source_dataset')}."
                        })
                    elif role == "CONTRADICTORY":
                        contradictory_evidence.append({
                            "evidence_id": eid,
                            "source_dataset": ev_item.get("source_dataset"),
                            "metric": ev_item.get("metric"),
                            "finding": f"Conflicting signal {ev_item.get('metric')} observed."
                        })

                    traceability.append({
                        "evidence_id": eid,
                        "source_dataset": ev_item.get("source_dataset"),
                        "record_id": ev_item.get("record_id")
                    })

            # Add primary reasoning claim
            if supporting_evidence:
                reasoning_claims.append({
                    "claim": f"Primary driver established as {established_driver}.",
                    "evidence_ids": [e["evidence_id"] for e in supporting_evidence],
                    "explanation": f"Evaluation of cross-source structured evidence confirms {established_driver} with status {overall_status}."
                })
        else:
            # NOT_ESTABLISHED scenario
            overall_status = "NOT_ESTABLISHED"
            established_driver = None
            confidence = "NONE"
            reasoning_claims.append({
                "claim": "No causal driver could be established with sufficient statistical or temporal confidence.",
                "evidence_ids": [e["evidence_id"] for e in ev_list[:2]] if ev_list else [],
                "explanation": "Signals across candidate drivers were below the required evidence thresholds or lacked conclusive temporal precedence."
            })
            for e in ev_list[:2]:
                traceability.append({
                    "evidence_id": e["evidence_id"],
                    "source_dataset": e.get("source_dataset"),
                    "record_id": e.get("record_id")
                })

        mock_response = {
            "executive_summary": f"Analysis of {kpi} anomaly indicates {overall_status} status for driver {established_driver if established_driver else 'None'}.",
            "what_happened": f"{kpi} experienced a change of {change_pct * 100:.2f}% relative to historical baseline.",
            "diagnosis": {
                "driver": established_driver,
                "status": overall_status,
                "confidence": confidence
            },
            "reasoning": reasoning_claims,
            "supporting_evidence": supporting_evidence,
            "contradictory_evidence": contradictory_evidence,
            "uncertainties": [
                "Unobserved market externalities and macroeconomic shifts are not captured in current telemetry."
            ],
            "recommended_next_steps": [
                f"Conduct operational deep-dive into {established_driver if established_driver else 'cross-functional signals'} and review recent commercial adjustments."
            ],
            "traceability": traceability
        }

        return json.dumps(mock_response, indent=2)
