from typing import Dict, Any, List

class EvidenceScorer:
    """
    Deterministically scores candidate drivers based on magnitude, 
    evidence depth, and source count.
    """
    
    @staticmethod
    def score_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for cand in candidates:
            evidence_items = cand.get("evidence", [])
            supporting_items = [e for e in evidence_items if e.get("evidence_role") == "SUPPORTING"]
            supporting_sources = set(e.get("source_dataset") for e in supporting_items if e.get("source_dataset"))
            
            # 1. Driver-specific signal magnitude score
            magnitude = abs(cand.get("driver_change_pct", 0.0))
            if len(supporting_items) == 0:
                signal_score = 0.0
            else:
                if magnitude > 0.4:
                    signal_score = 6.0
                elif magnitude > 0.2:
                    signal_score = 4.0
                elif magnitude > 0.1:
                    signal_score = 2.0
                elif magnitude > 0.05:
                    signal_score = 1.0
                else:
                    signal_score = 0.5
                    
            # 2. Independent source corroboration (2 points per additional distinct dataset)
            if len(supporting_sources) > 1:
                corroboration_score = (len(supporting_sources) - 1) * 3.0
            else:
                corroboration_score = 0.0
                
            # 3. Temporal alignment multiplier (causes cannot happen only after the effect)
            temp_align = cand.get("temporal_alignment", "NO_CLEAR_ALIGNMENT")
            if temp_align in ["DURING", "BEFORE"]:
                temporal_multiplier = 1.0
            else:
                temporal_multiplier = 0.0
                
            base_score = (signal_score + corroboration_score) * temporal_multiplier
            
            # Save metadata
            cand["base_score"] = float(base_score)
            cand["evidence_source_count"] = len(supporting_sources)
            cand["supporting_evidence_count"] = len(supporting_items)
            cand["outcome_evidence_count"] = len([e for e in evidence_items if e.get("evidence_role") == "OUTCOME"])
            cand["contradictory_evidence_count"] = len([e for e in evidence_items if e.get("evidence_role") == "CONTRADICTORY"])
            
        return candidates

