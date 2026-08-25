import os
import json
import pandas as pd
from pathlib import Path

from src.analytics.run_analysis import run_analysis

SCENARIOS = [
    {
        "scenario_id": "S001",
        "request": {"market": "South Korea", "product_code": "A6519160401", "date": "2021-05-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_04_RETURNS",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S002",
        "request": {"market": "South Korea", "date": "2021-01-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_06_CUSTOMER",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S003",
        "request": {"market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_03_MARKETING",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S004",
        "request": {"market": "China", "product_code": "A0621150308", "date": "2021-01-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_02_PRICING",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S005",
        "request": {"market": "Indonesia", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_05_SUPPORT",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S006",
        "request": {"market": "India", "category": "Processors", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S007",
        "request": {"market": "Portugal", "category": "Wi fi extender", "date": "2019-09-01", "kpi": "category_share"},
        "expected_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S008",
        "request": {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_driver": "NOT_ESTABLISHED",
        "expected_status": "NOT_ESTABLISHED"
    }
]

def test_phase3a2_accuracy():
    actual_results = []
    
    for sc in SCENARIOS:
        try:
            result = run_analysis(sc["request"])
            actual_results.append(result)
        except Exception as e:
            print(f"Scenario {sc['scenario_id']} failed to execute: {str(e)}")
            actual_results.append(None)
            
    project_root = Path(__file__).resolve().parent.parent
    eval_dir = project_root / "Data" / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    results_records = []
    top1_correct_count = 0
    top3_correct_count = 0
    status_correct_count = 0
    s008_correct = False
    
    for sc, res in zip(SCENARIOS, actual_results):
        if res is None:
            continue
            
        cands = res.get("candidate_drivers", [])
        top_cand = cands[0] if cands else {}
        top_driver = top_cand.get("driver", "NOT_ESTABLISHED")
        top3_drivers = [c.get("driver") for c in cands[:3]]
        
        expected_driver = sc["expected_driver"]
        expected_status = sc["expected_status"]
        
        top1_correct = (top_driver == expected_driver)
        top3_contains = (expected_driver in top3_drivers) or (expected_driver == "NOT_ESTABLISHED" and not cands)
        status_correct = (res.get("overall_status") == expected_status)
        
        if top1_correct: top1_correct_count += 1
        if top3_contains: top3_correct_count += 1
        if status_correct: status_correct_count += 1
        
        if sc["scenario_id"] == "S008" and res.get("overall_status") == "NOT_ESTABLISHED":
            s008_correct = True
            
        # Extract evidence metrics
        supporting_source_count = top_cand.get("evidence_source_count", 0) if cands else 0
        outcome_evidence_count = top_cand.get("outcome_evidence_count", 0) if cands else 0
        supporting_evidence_count = top_cand.get("supporting_evidence_count", 0) if cands else 0
        contradictory_evidence_count = top_cand.get("contradictory_evidence_count", 0) if cands else 0
        temporal_alignment = top_cand.get("temporal_alignment", "NO_CLEAR_ALIGNMENT") if cands else "NO_CLEAR_ALIGNMENT"

        results_records.append({
            "scenario_id": sc["scenario_id"],
            "kpi": sc["request"]["kpi"],
            "current_value": res["event"].get("current_value"),
            "previous_value": res["event"].get("previous_month_value"),
            "baseline_value": res["event"].get("baseline_value"),
            "top_driver": top_driver,
            "top_driver_score": top_cand.get("score") if cands else 0.0,
            "top_driver_status": top_cand.get("status") if cands else "NONE",
            "top3_drivers": ",".join(top3_drivers),
            "supporting_source_count": supporting_source_count,
            "outcome_evidence_count": outcome_evidence_count,
            "supporting_evidence_count": supporting_evidence_count,
            "contradictory_evidence_count": contradictory_evidence_count,
            "temporal_alignment": temporal_alignment,
            "expected_driver": expected_driver,
            "top1_correct": top1_correct,
            "top3_contains_expected": top3_contains,
            "status_correct": status_correct
        })
        
    pd.DataFrame(results_records).to_csv(eval_dir / "phase3a2_results.csv", index=False)
    
    total = len(SCENARIOS)
    print("========================================")
    print("PHASE 3A.2 ACCURACY METRICS")
    print("========================================")
    print(f"Top-1 Accuracy:       {top1_correct_count} / {total} = {top1_correct_count/total:.1%}")
    print(f"Top-3 Recall:         {top3_correct_count} / {total} = {top3_correct_count/total:.1%}")
    print(f"Status Accuracy:      {status_correct_count} / {total} = {status_correct_count/total:.1%}")
    print(f"S008 Correct:         {s008_correct}")
    print("========================================")
    print("Phase 3A.2 evaluation written to Data/evaluation/phase3a2_results.csv")

if __name__ == "__main__":
    test_phase3a2_accuracy()
