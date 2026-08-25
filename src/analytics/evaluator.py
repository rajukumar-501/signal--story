from typing import Dict, Any, List

class Phase3AEvaluator:
    """
    Evaluates the performance of the Phase 3A analytical engine against expected outcomes.
    """
    
    @staticmethod
    def evaluate(expected_scenarios: List[Dict[str, Any]], actual_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = {
            "total_scenarios": len(expected_scenarios),
            "top_1_accuracy": 0,
            "top_3_recall": 0,
            "uncertainty_accuracy": 0,
            "ground_truth_leakage": 0, # Should always be 0
            "scenarios_evaluated": []
        }
        
        for expected, actual in zip(expected_scenarios, actual_results):
            scenario_id = expected["scenario_id"]
            true_cause = expected["true_root_cause"]
            
            top_1 = actual["candidate_drivers"][0]["driver"] if actual["candidate_drivers"] else "NONE"
            top_3 = [c["driver"] for c in actual["candidate_drivers"][:3]]
            
            if true_cause == "NOT_ESTABLISHED":
                if actual["overall_status"] == "NOT_ESTABLISHED":
                    metrics["uncertainty_accuracy"] += 1
            else:
                if top_1 == true_cause:
                    metrics["top_1_accuracy"] += 1
                if true_cause in top_3:
                    metrics["top_3_recall"] += 1
                    
            # Check for leakage
            if "true_root_cause" in str(actual) or "ground_truth" in str(actual):
                metrics["ground_truth_leakage"] += 1
                
            metrics["scenarios_evaluated"].append({
                "scenario_id": scenario_id,
                "expected": true_cause,
                "top_1": top_1,
                "status": actual["overall_status"]
            })
            
        return metrics
