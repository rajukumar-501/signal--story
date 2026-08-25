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

def test_phase3a_accuracy():
    actual_results = []
    
    for sc in SCENARIOS:
        try:
            # ONLY pass the request. expected_driver is kept strictly isolated.
            result = run_analysis(sc["request"])
            actual_results.append(result)
        except Exception as e:
            print(f"Scenario {sc['scenario_id']} failed to execute: {str(e)}")
            actual_results.append(None)
            
    # Save results to Data/evaluation/phase3a_baseline_results.csv
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
        top_driver = cands[0]["driver"] if cands else "NONE"
        top3_drivers = [c["driver"] for c in cands[:3]]
        
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
            
        evidence_source_count = 0
        if cands:
            sources = set([ev.get("source_dataset") for ev in cands[0].get("evidence", [])])
            evidence_source_count = len(sources)

        results_records.append({
            "scenario_id": sc["scenario_id"],
            "actual_market": sc["request"].get("market"),
            "actual_product": sc["request"].get("product_code"),
            "actual_category": sc["request"].get("category"),
            "actual_date": sc["request"]["date"],
            "kpi": sc["request"]["kpi"],
            "kpi_current": res["event"].get("current_value"),
            "kpi_previous": res["event"].get("previous_month_value"),
            "mom_change_percent": res["event"].get("mom_change_percent"),
            "rolling_baseline": res["event"].get("baseline_value"),
            "baseline_change_percent": res["event"].get("baseline_change_percent"),
            "top_driver": top_driver,
            "top_driver_score": cands[0]["score"] if cands else 0,
            "top_driver_status": cands[0]["status"] if cands else "NONE",
            "top3_drivers": ",".join(top3_drivers),
            "expected_driver": expected_driver,
            "top1_correct": top1_correct,
            "top3_contains_expected": top3_contains,
            "status_correct": status_correct,
            "evidence_source_count": evidence_source_count,
            "contradiction_count": len(cands[0].get("contradictions", [])) if cands else 0
        })
        
    pd.DataFrame(results_records).to_csv(eval_dir / "phase3a_baseline_results.csv", index=False)
    
    total = len(SCENARIOS)
    print("========================================")
    print("PHASE 3A.1 ACCURACY METRICS")
    print("========================================")
    print(f"Top-1 Accuracy:       {top1_correct_count} / {total} = {top1_correct_count/total:.1%}")
    print(f"Top-3 Recall:         {top3_correct_count} / {total} = {top3_correct_count/total:.1%}")
    print(f"Status Accuracy:      {status_correct_count} / {total} = {status_correct_count/total:.1%}")
    print(f"S008 Correct:         {s008_correct}")
    print("========================================")
    print("Baseline evaluation written to Data/evaluation/phase3a_baseline_results.csv")

if __name__ == "__main__":
    test_phase3a_accuracy()
