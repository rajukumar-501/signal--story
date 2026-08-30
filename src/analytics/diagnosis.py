from typing import Dict, Any, List, Optional

class DiagnosisGate:
    """
    Deterministic Diagnosis Gate (Phase 3A.3).
    Evaluates whether the highest-ranked hypothesis meets all criteria to become an established driver.
    """
    
    @staticmethod
    def evaluate(event: Dict[str, Any], ranked_hypotheses: List[Dict[str, Any]]) -> Dict[str, Any]:
        # If baseline was invalid, no diagnosis can be established
        if event.get("baseline_status") != "VALID":
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": f"Baseline status is {event.get('baseline_status')}, insufficient historical baseline.",
                "confidence": "NONE"
            }
            
        if not ranked_hypotheses:
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": "No candidate hypotheses were generated.",
                "confidence": "NONE"
            }
            
        top_hyp = ranked_hypotheses[0]
        score = top_hyp.get("final_score", top_hyp.get("score", 0.0))
        status = top_hyp.get("status", "NOT_ESTABLISHED")
        sup_count = top_hyp.get("supporting_evidence_count", 0)
        con_count = top_hyp.get("contradictory_evidence_count", 0)
        temp_align = top_hyp.get("temporal_alignment", "NO_CLEAR_ALIGNMENT")
        
        # Rule 1: Supporting evidence must exist
        if sup_count == 0:
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": "No driver-specific supporting evidence found.",
                "confidence": "NONE"
            }
            
        # Rule 2: Temporal alignment must be BEFORE or DURING (AFTER cannot independently establish causality)
        if temp_align not in ["BEFORE", "DURING"]:
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": f"Temporal alignment '{temp_align}' does not establish causality.",
                "confidence": "NONE"
            }
            
        # Rule 3: Contradictory evidence must not dominate
        if con_count > sup_count or score <= 0.0:
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": "Contradictory evidence dominates or score was negated.",
                "confidence": "NONE"
            }
            
        # Rule 4: Score must meet PLAUSIBLE or STRONGLY_SUPPORTED threshold (>= 4.0)
        if score < 4.0 or status == "NOT_ESTABLISHED":
            return {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": f"Top hypothesis score ({score:.1f}) is insufficient to establish root cause.",
                "confidence": "NONE"
            }
            
        # All gate conditions satisfied: Establish driver
        return {
            "established_driver": top_hyp.get("driver"),
            "overall_status": status,
            "reason": f"Driver {top_hyp.get('driver')} established with status {status} (score: {score:.1f}, sources: {top_hyp.get('evidence_source_count', 1)}).",
            "confidence": top_hyp.get("confidence", "MEDIUM")
        }

class DiagnosisFormatter:
    """
    Formats the structured analytical output (Phase 3A.3 contract).
    """
    
    @staticmethod
    def format_diagnosis(event: Dict[str, Any], ranked_hypotheses: List[Dict[str, Any]], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        formatted_hypotheses = []
        for c in ranked_hypotheses:
            formatted_hypotheses.append({
                "driver": c.get("driver"),
                "rank": c.get("rank"),
                "score": c.get("final_score", c.get("score", 0.0)),
                "status": c.get("status"),
                "confidence": c.get("confidence"),
                "evidence": c.get("evidence", []),
                "contradictions": c.get("contradictions", []),
                "evidence_source_count": c.get("evidence_source_count", 0),
                "supporting_source_count": c.get("evidence_source_count", 0),
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
            "candidate_hypotheses": formatted_hypotheses,
            "candidate_drivers": formatted_hypotheses,
            "diagnosis": diagnosis,
            "overall_status": diagnosis.get("overall_status", "NOT_ESTABLISHED"),
            "limitations": [
                "Analysis relies entirely on available structured datasets.",
                "Causal status is observational, not interventional."
            ]
        }

