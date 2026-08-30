"""
Deterministic Mock Reasoning Provider for Phase 3B.
Synthesizes valid contract-compliant JSON responses using real indexed evidence IDs
from the EvidenceContext, or returns custom injected responses for test fixtures.
"""

import json
from typing import Dict, Any, Optional, Union, List
from .reasoning_provider import ReasoningProvider
from .evidence_context import EvidenceContext

class MockReasoningProvider(ReasoningProvider):
    """
    Deterministic Mock Provider for testing Phase 3B validation and pipelines
    without calling live external LLM APIs.
    """

    def __init__(self, custom_response: Optional[Union[Dict[str, Any], str]] = None):
        self.custom_response = custom_response

    def set_custom_response(self, response: Optional[Union[Dict[str, Any], str]]) -> None:
        self.custom_response = response

    def generate_diagnosis(self, context: EvidenceContext) -> Dict[str, Any]:
        """
        Synthesizes a contract-compliant response from the EvidenceContext
        using the generalized 6-Step Evidence-Arbitration Protocol.
        """
        if self.custom_response is not None:
            if isinstance(self.custom_response, str):
                try:
                    return json.loads(self.custom_response)
                except Exception:
                    # Return raw string wrapped or malformed dict for validator testing
                    return {"raw_invalid_payload": self.custom_response} # type: ignore
            return self.custom_response

        kpi = context.event.kpi
        change_pct = context.event.change_percent
        req = context.request

        # 1. Uncertainty Gating Preservation (e.g., S008 or inconclusive macro anomalies)
        if context.diagnosis.overall_status == "NOT_ESTABLISHED" or not context.hypotheses:
            overall_status = "NOT_ESTABLISHED"
            established_driver = None
            confidence = "NONE"
            
            sample_ids = [e.evidence_id for e in context.all_evidence[:2]]
            traceability = []
            for eid in sample_ids:
                ev_item = context.get_evidence_by_id(eid)
                if ev_item:
                    traceability.append({
                        "evidence_id": eid,
                        "source_dataset": ev_item.source_dataset,
                        "record_id": ev_item.record_id
                    })

            if sample_ids:
                claims = [
                    {
                        "claim": f"{kpi} experienced a change of {change_pct * 100:.2f}% relative to historical baseline.",
                        "claim_type": "OBSERVATION",
                        "evidence_ids": sample_ids
                    },
                    {
                        "claim": "Available telemetry is inconclusive or confounded by broader macro-market dynamics without specific internal operational causes.",
                        "claim_type": "INTERPRETATION",
                        "evidence_ids": sample_ids
                    },
                    {
                        "claim": "No single internal operational causal driver meets statistical and evidentiary thresholds for establishment.",
                        "claim_type": "CAUSAL_CONCLUSION",
                        "evidence_ids": sample_ids
                    },
                    {
                        "claim": "Maintain monitoring and investigate broader market macroeconomic trends.",
                        "claim_type": "RECOMMENDATION",
                        "evidence_ids": sample_ids
                    }
                ]
            else:
                claims = [
                    {
                        "claim": "Available telemetry is inconclusive or absent for establishing an internal driver.",
                        "claim_type": "INTERPRETATION",
                        "evidence_ids": []
                    },
                    {
                        "claim": "Maintain monitoring and investigate broader market trends.",
                        "claim_type": "RECOMMENDATION",
                        "evidence_ids": []
                    }
                ]


            return {
                "executive_summary": f"Diagnostic evaluation of {kpi} concludes NOT_ESTABLISHED: telemetry reflects broad market movements without an established internal driver.",
                "what_happened": f"{kpi} shifted by {change_pct * 100:.2f}% compared to baseline in {req.market or 'the target market'}.",
                "diagnosis": {
                    "driver": None,
                    "status": "NOT_ESTABLISHED",
                    "confidence": "NONE"
                },
                "candidate_comparisons": [],
                "why_selected": "No candidate hypothesis possessed sufficient causal evidence or distinct lead indicators to outrank macro uncertainty.",
                "why_alternatives_rejected": [
                    "Investigated candidates lacked localized or preceding evidence distinct from peer market movements."
                ],
                "claims": claims,
                "supporting_evidence": [],
                "contradictory_evidence": [],
                "uncertainties": [
                    "Macroeconomic variables, competitor actions, and cross-category market trends are not directly instrumented."
                ],
                "recommended_next_steps": [
                    "Monitor peer market movements and conduct cross-functional macro review."
                ],
                "traceability": traceability,
                "validation_status": "PASSED"
            }

        # 2. General Cross-Candidate Multi-Factor Arbitration
        arbitrated_candidates = []
        candidate_comparisons = []

        for hyp in context.hypotheses:
            ev_items = [context.get_evidence_by_id(eid) for eid in hyp.evidence_ids if context.get_evidence_by_id(eid)]
            supporting_items = [e for e in ev_items if e.evidence_role == "SUPPORTING"]
            contradictory_items = [e for e in ev_items if e.evidence_role == "CONTRADICTORY"]

            # A. Scope Alignment Evaluation
            scope_alignment = "MARKET"
            scope_score = 1.0
            if req.product_code and any(e.product_code and e.product_code == req.product_code for e in supporting_items):
                scope_alignment = "EXACT"
                scope_score = 3.0
            elif req.product_code and any(e.product_code and e.product_code != req.product_code for e in supporting_items):
                scope_alignment = "OUT_OF_SCOPE"
                scope_score = -4.0
            elif req.category and any(e.category and e.category == req.category for e in supporting_items):
                scope_alignment = "CATEGORY"
                scope_score = 2.0
            elif req.market and any(e.market == req.market for e in supporting_items):
                scope_alignment = "MARKET"
                scope_score = 1.0
            elif any(e.market and req.market and e.market != req.market for e in supporting_items):
                scope_alignment = "OUT_OF_SCOPE"
                scope_score = -4.0

            # B. Temporal Precedence Evaluation
            temporal_alignment = "DURING"
            temporal_score = 1.0
            if any(e.temporal_alignment == "BEFORE" for e in supporting_items):
                temporal_alignment = "BEFORE"
                temporal_score = 2.0
            elif any(e.temporal_alignment == "DURING" for e in supporting_items):
                temporal_alignment = "DURING"
                temporal_score = 1.0
            elif any(e.temporal_alignment == "AFTER" for e in supporting_items):
                temporal_alignment = "AFTER"
                temporal_score = -2.0
            else:
                temporal_alignment = "NO_CLEAR_ALIGNMENT"
                temporal_score = 0.0

            # C. Independent Dataset Corroboration
            distinct_datasets = len({e.source_dataset for e in supporting_items})
            corroboration_score = max(0, distinct_datasets - 1) * 2.0

            # D. Contradiction Penalty
            contradiction_count = len(contradictory_items) + len(hyp.contradictions)
            contradiction_penalty = contradiction_count * 4.0

            # E. Total Generalized Arbitration Score
            arbitrated_score = (
                hyp.score +
                scope_score +
                temporal_score +
                corroboration_score -
                contradiction_penalty
            )

            comp_summary = (
                f"{hyp.driver}: Scope={scope_alignment} (score +{scope_score:.1f}), "
                f"Temporal={temporal_alignment} (+{temporal_score:.1f}), "
                f"Independent Sources={distinct_datasets} (+{corroboration_score:.1f}), "
                f"Contradictions={contradiction_count} (-{contradiction_penalty:.1f})."
            )

            candidate_comparisons.append({
                "driver": hyp.driver,
                "scope_alignment": scope_alignment,
                "temporal_alignment": temporal_alignment,
                "independent_source_count": distinct_datasets,
                "contradiction_count": contradiction_count,
                "comparison_summary": comp_summary
            })

            arbitrated_candidates.append({
                "hyp": hyp,
                "arbitrated_score": arbitrated_score,
                "supporting_items": supporting_items,
                "contradictory_items": contradictory_items,
                "scope_alignment": scope_alignment,
                "temporal_alignment": temporal_alignment,
                "distinct_datasets": distinct_datasets,
                "contradiction_count": contradiction_count
            })

        # 3. Sort candidates by generalized arbitrated score
        arbitrated_candidates.sort(key=lambda x: x["arbitrated_score"], reverse=True)
        winner = arbitrated_candidates[0]
        top_hyp = winner["hyp"]
        established_driver = top_hyp.driver

        # 4. Calibrate Status & Confidence
        if (
            (winner["distinct_datasets"] >= 2 or top_hyp.status == "STRONGLY_SUPPORTED" or context.diagnosis.overall_status == "STRONGLY_SUPPORTED") and
            winner["contradiction_count"] == 0 and
            winner["temporal_alignment"] in {"BEFORE", "DURING"} and
            winner["scope_alignment"] != "OUT_OF_SCOPE"
        ):
            overall_status = "STRONGLY_SUPPORTED"
            confidence = "HIGH"
        elif (
            winner["arbitrated_score"] > 0 and
            winner["contradiction_count"] == 0 and
            winner["scope_alignment"] != "OUT_OF_SCOPE"
        ):
            overall_status = "PLAUSIBLE"
            confidence = "MEDIUM"
        else:
            overall_status = "PLAUSIBLE"
            confidence = "MEDIUM"


        # 5. Extract Supporting, Contradictory & Traceability Evidence
        supporting_evidence = []
        contradictory_evidence = []
        traceability = []

        for ev_item in winner["supporting_items"]:
            supporting_evidence.append({
                "evidence_id": ev_item.evidence_id,
                "source_dataset": ev_item.source_dataset,
                "metric": ev_item.metric,
                "finding": f"{ev_item.metric} exhibited anomalous telemetry ({ev_item.value}) in {ev_item.source_dataset} ({ev_item.temporal_alignment})."
            })
            traceability.append({
                "evidence_id": ev_item.evidence_id,
                "source_dataset": ev_item.source_dataset,
                "record_id": ev_item.record_id
            })

        for ev_item in winner["contradictory_items"]:
            contradictory_evidence.append({
                "evidence_id": ev_item.evidence_id,
                "source_dataset": ev_item.source_dataset,
                "metric": ev_item.metric,
                "finding": f"Conflicting signal {ev_item.metric} observed in {ev_item.source_dataset}."
            })
            traceability.append({
                "evidence_id": ev_item.evidence_id,
                "source_dataset": ev_item.source_dataset,
                "record_id": ev_item.record_id
            })

        if not supporting_evidence and context.all_evidence:
            first_ev = context.all_evidence[0]
            supporting_evidence.append({
                "evidence_id": first_ev.evidence_id,
                "source_dataset": first_ev.source_dataset,
                "metric": first_ev.metric,
                "finding": f"Baseline signal in {first_ev.source_dataset}."
            })
            traceability.append({
                "evidence_id": first_ev.evidence_id,
                "source_dataset": first_ev.source_dataset,
                "record_id": first_ev.record_id
            })

        # 6. Formulate Structured Claims
        primary_eid = supporting_evidence[0]["evidence_id"]
        all_eids = [e["evidence_id"] for e in supporting_evidence]

        claims = [
            {
                "claim": f"{kpi} experienced a significant movement of {change_pct * 100:.2f}% relative to baseline.",
                "claim_type": "OBSERVATION",
                "evidence_ids": [primary_eid]
            },
            {
                "claim": f"Evidence across {winner['distinct_datasets']} source dataset(s) indicates focused deterioration in {established_driver}.",
                "claim_type": "INTERPRETATION",
                "evidence_ids": all_eids
            },
            {
                "claim": f"Multi-factor arbitration establishes {established_driver} as the primary root cause with {overall_status} status.",
                "claim_type": "CAUSAL_CONCLUSION",
                "evidence_ids": all_eids
            },
            {
                "claim": f"Initiate operational remediation and parameter tuning for {established_driver}.",
                "claim_type": "RECOMMENDATION",
                "evidence_ids": [primary_eid]
            }
        ]

        # 7. Formulate Why Selected & Why Alternatives Rejected
        why_selected = (
            f"{established_driver} was selected because it demonstrates superior {winner['scope_alignment'].lower()} scope match, "
            f"{winner['temporal_alignment'].lower()} temporal alignment, {winner['distinct_datasets']} independent corroborating source(s), "
            f"and zero dominant contradictory indicators."
        )

        why_alternatives_rejected = []
        for alt in arbitrated_candidates[1:]:
            alt_driver = alt["hyp"].driver
            why_alternatives_rejected.append(
                f"{alt_driver} was ranked lower (score {alt['arbitrated_score']:.1f} vs {winner['arbitrated_score']:.1f}) "
                f"due to {alt['scope_alignment'].lower()} scope match, {alt['temporal_alignment'].lower()} timing, or "
                f"{alt['contradiction_count']} contradiction(s)."
            )

        return {
            "executive_summary": f"Diagnostic arbitration establishes {established_driver} ({overall_status}) as the primary driver of the {kpi} anomaly.",
            "what_happened": f"{kpi} shifted by {change_pct * 100:.2f}% compared to historical baseline.",
            "diagnosis": {
                "driver": established_driver,
                "status": overall_status,
                "confidence": confidence
            },
            "candidate_comparisons": candidate_comparisons,
            "why_selected": why_selected,
            "why_alternatives_rejected": why_alternatives_rejected,
            "claims": claims,
            "supporting_evidence": supporting_evidence,
            "contradictory_evidence": contradictory_evidence,
            "uncertainties": [
                "External market confounding variables and unobserved competitor promotional tactics."
            ],
            "recommended_next_steps": [
                f"Review cross-functional telemetry for {established_driver} and implement targeted remediation."
            ],
            "traceability": traceability,
            "validation_status": "PASSED"
        }

