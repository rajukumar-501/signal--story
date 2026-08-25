from typing import Dict, Any, List

class DriverRanker:
    """
    Ranks drivers deterministically and handles uncertainty.
    """
    
    @staticmethod
    def rank_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sort by final_score descending, falling back to base_score if missing
        for cand in candidates:
            if "final_score" not in cand:
                cand["final_score"] = cand.get("base_score", 0.0)
        ranked = sorted(candidates, key=lambda x: x.get("final_score", 0.0), reverse=True)
        
        for idx, cand in enumerate(ranked):
            cand["rank"] = idx + 1
            
            score = cand.get("final_score", 0.0)
            sup_count = cand.get("supporting_evidence_count", 0)
            con_count = cand.get("contradictory_evidence_count", 0)
            
            # Uncertainty checks:
            # 1. No driver-specific supporting evidence
            # 2. Only outcome evidence exists (supporting count is 0)
            # 3. Contradictory evidence dominates supporting evidence
            # 4. Score is 0.0
            if score == 0.0 or sup_count == 0 or con_count > sup_count:
                cand["confidence"] = "NONE"
                cand["status"] = "NOT_ESTABLISHED"
            elif score >= 7.0:
                cand["confidence"] = "HIGH"
                cand["status"] = "STRONGLY_SUPPORTED"
            elif score >= 4.0:
                cand["confidence"] = "MEDIUM"
                cand["status"] = "PLAUSIBLE"
            else:
                cand["confidence"] = "NONE"
                cand["status"] = "NOT_ESTABLISHED"
                
        return ranked
        
    @staticmethod
    def determine_overall_status(ranked_candidates: List[Dict[str, Any]]) -> str:
        if not ranked_candidates:
            return "NOT_ESTABLISHED"
            
        top_cand = ranked_candidates[0]
        if top_cand.get("status") in ["STRONGLY_SUPPORTED", "PLAUSIBLE"]:
            return top_cand["status"]
            
        return "NOT_ESTABLISHED"

