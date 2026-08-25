from typing import Dict, Any, List
import pandas as pd
from dateutil.relativedelta import relativedelta

from .data_model import AnalyticalDataModel
from .kpi_engine import KPIEngine

class ContradictionEngine:
    """
    Challenges hypotheses by looking for contradictory evidence.
    """
    def __init__(self, data_model: AnalyticalDataModel):
        self.dm = data_model

    def evaluate_contradictions(self, candidates: List[Dict[str, Any]], event: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_date = pd.to_datetime(event['request']['date'])
        
        for cand in candidates:
            evidence_items = cand.get("evidence", [])
            
            # Get contradiction metrics already appended by generator
            contradictions = [e.get("metric") for e in evidence_items if e.get("evidence_role") == "CONTRADICTORY"]
            
            driver_id = cand.get("driver")
            
            # Marketing Inefficiency contradiction: Inventory stockout occurred during event month
            if driver_id == "DRIVER_03_MARKETING":
                inv_df = self.dm.get_inventory()
                if not inv_df.empty:
                    inv_scoped = self.dm.apply_scope(inv_df, event['request'])
                    inv_during = inv_scoped[inv_scoped['date'] == target_date]
                    if not inv_during.empty and inv_during['stockout_flag'].max() > 0:
                        contradictions.append("inventory_stockout_clash")
                        evidence_items.append({
                            "source_dataset": "fact_inventory_monthly",
                            "record_id": None,
                            "lineage": "AGGREGATED",
                            "date": target_date.strftime("%Y-%m-%d"),
                            "market": event['request'].get("market"),
                            "product_code": event['request'].get("product_code"),
                            "category": event['request'].get("category"),
                            "channel": event['request'].get("channel"),
                            "metric": "inventory_stockout_clash",
                            "value": 1.0,
                            "evidence_role": "CONTRADICTORY"
                        })
                        
            # Apply 15.0 points penalty per contradiction
            c_score = len(contradictions) * 15.0
            
            cand["contradictions"] = contradictions
            cand["contradiction_score"] = float(c_score)
            cand["contradictory_evidence_count"] = len([e for e in evidence_items if e.get("evidence_role") == "CONTRADICTORY"])
            
            # Final score calculation
            cand["final_score"] = float(max(0.0, cand.get("base_score", 0.0) - c_score))
            
        return candidates
