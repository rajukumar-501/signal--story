from typing import Dict, Any, List

class DiagnosisFormatter:
    """
    Formats the structured analytical output (Phase 3A step 21).
    """
    
    @staticmethod
    def format_diagnosis(event: Dict[str, Any], ranked_candidates: List[Dict[str, Any]], overall_status: str) -> Dict[str, Any]:
        
        # Prepare candidate driver output
        formatted_cands = []
        for c in ranked_candidates:
            formatted_cands.append({
                "rank": c.get("rank"),
                "driver": c.get("driver"),
                "score": c.get("final_score"),
                "status": c.get("status"),
                "confidence": c.get("confidence"),
                "evidence": c.get("evidence", []),
                "contradictions": c.get("contradictions", []),
                "evidence_source_count": c.get("evidence_source_count", 0),
                "supporting_evidence_count": c.get("supporting_evidence_count", 0),
                "outcome_evidence_count": c.get("outcome_evidence_count", 0),
                "contradictory_evidence_count": c.get("contradictory_evidence_count", 0),
                "temporal_alignment": c.get("temporal_alignment", "NO_CLEAR_ALIGNMENT")
            })
            
        return {
            "event": {
                "kpi": event.get("kpi"),
                "current_value": event.get("current_value"),
                "previous_month_value": event.get("previous_month_value"),
                "baseline_value": event.get("rolling_3m_baseline"),
                "mom_change_percent": event.get("mom_change_percent"),
                "baseline_change_percent": event.get("baseline_change_percent"),
                "change_percent": event.get("percentage_change"),
                "baseline_status": event.get("baseline_status")
            },
            "candidate_drivers": formatted_cands,
            "overall_status": overall_status,
            "limitations": [
                "Analysis relies entirely on available structured datasets.",
                "Causal status is observational, not interventional."
            ]
        }
