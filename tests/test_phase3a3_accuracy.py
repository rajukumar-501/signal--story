import os
import json
import pandas as pd
from pathlib import Path

from src.analytics.run_analysis import run_analysis

SCENARIOS = [
    {
        "scenario_id": "S001",
        "request": {"market": "South Korea", "product_code": "A6519160401", "date": "2021-05-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_04_RETURNS",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S002",
        "request": {"market": "South Korea", "date": "2021-01-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_06_CUSTOMER",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S003",
        "request": {"market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_03_MARKETING",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S004",
        "request": {"market": "China", "product_code": "A0621150308", "date": "2021-01-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_02_PRICING",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S005",
        "request": {"market": "Indonesia", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_05_SUPPORT",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S006",
        "request": {"market": "India", "category": "Processors", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_established_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S007",
        "request": {"market": "Portugal", "category": "Wi fi extender", "date": "2019-09-01", "kpi": "category_share"},
        "expected_established_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S008",
        "request": {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"},
        "expected_established_driver": None,
        "expected_status": "NOT_ESTABLISHED"
    }
]

def test_phase3a3_accuracy():
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
    top1_hyp_correct_count = 0
    top3_hyp_correct_count = 0
    established_driver_correct_count = 0
    status_correct_count = 0
    uncertainty_correct_count = 0
    uncertainty_total = 0
    rr_list = []
    
    for sc, res in zip(SCENARIOS, actual_results):
        if res is None:
            continue
            
        hyps = res.get("candidate_hypotheses", res.get("candidate_drivers", []))
        top_hyp = hyps[0] if hyps else {}
        top_driver = top_hyp.get("driver", "NONE")
        top3_drivers = [h.get("driver") for h in hyps[:3]]
        
        diag = res.get("diagnosis", {})
        established_driver = diag.get("established_driver")
        overall_status = diag.get("overall_status", res.get("overall_status", "NOT_ESTABLISHED"))
        
        expected_established_driver = sc["expected_established_driver"]
        expected_status = sc["expected_status"]
        
        # Hypothesis evaluation
        if expected_established_driver is not None:
            top1_hyp_correct = (top_driver == expected_established_driver)
            top3_hyp_contains = (expected_established_driver in top3_drivers)
            
            # Reciprocal rank in candidate hypotheses list
            driver_ranks = [h.get("driver") for h in hyps]
            if expected_established_driver in driver_ranks:
                rank = driver_ranks.index(expected_established_driver) + 1
                rr = 1.0 / rank
            else:
                rr = 0.0
            rr_list.append(rr)
        else:
            # S008 / Uncertainty case: No expected driver, excluded from driver-ranking MRR denominator
            uncertainty_total += 1
            is_uncertain_correct = (established_driver is None and overall_status == "NOT_ESTABLISHED")
            top1_hyp_correct = is_uncertain_correct
            top3_hyp_contains = is_uncertain_correct
            rr = None
            if is_uncertain_correct:
                uncertainty_correct_count += 1
                
        # Diagnosis evaluation
        established_driver_correct = (established_driver == expected_established_driver)
        status_correct = (overall_status == expected_status)
        
        if top1_hyp_correct: top1_hyp_correct_count += 1
        if top3_hyp_contains: top3_hyp_correct_count += 1
        if established_driver_correct: established_driver_correct_count += 1
        if status_correct: status_correct_count += 1
        
        supporting_source_count = top_hyp.get("supporting_source_count", top_hyp.get("evidence_source_count", 0)) if hyps else 0
        outcome_evidence_count = top_hyp.get("outcome_evidence_count", 0) if hyps else 0
        supporting_evidence_count = top_hyp.get("supporting_evidence_count", 0) if hyps else 0
        contradictory_evidence_count = top_hyp.get("contradictory_evidence_count", 0) if hyps else 0
        temporal_alignment = top_hyp.get("temporal_alignment", "NO_CLEAR_ALIGNMENT") if hyps else "NO_CLEAR_ALIGNMENT"

        results_records.append({
            "scenario_id": sc["scenario_id"],
            "kpi": sc["request"]["kpi"],
            "current_value": res["event"].get("current_value"),
            "previous_value": res["event"].get("previous_month_value"),
            "baseline_value": res["event"].get("baseline_value"),
            "top_driver": top_driver,
            "top_driver_score": top_hyp.get("score") if hyps else 0.0,
            "top_driver_status": top_hyp.get("status") if hyps else "NONE",
            "top3_drivers": ",".join([d for d in top3_drivers if d]),
            "established_driver": established_driver,
            "overall_status": overall_status,
            "supporting_source_count": supporting_source_count,
            "outcome_evidence_count": outcome_evidence_count,
            "supporting_evidence_count": supporting_evidence_count,
            "contradictory_evidence_count": contradictory_evidence_count,
            "temporal_alignment": temporal_alignment,
            "expected_established_driver": expected_established_driver,
            "expected_status": expected_status,
            "top1_hypothesis_correct": top1_hyp_correct,
            "top3_hypothesis_contains_expected": top3_hyp_contains,
            "established_driver_correct": established_driver_correct,
            "status_correct": status_correct,
            "reciprocal_rank": round(rr, 4) if rr is not None else None
        })
        
    df_results = pd.DataFrame(results_records)
    csv_path = eval_dir / "phase3a3_results.csv"
    df_results.to_csv(csv_path, index=False)
    
    total = len(SCENARIOS)
    mrr_denominator = len(rr_list)
    mrr = sum(rr_list) / mrr_denominator if mrr_denominator > 0 else 0.0
    unc_acc = (uncertainty_correct_count / uncertainty_total) if uncertainty_total > 0 else 1.0
    
    print("========================================")
    print("PHASE 3A.3 ACCURACY & DIAGNOSIS METRICS")
    print("========================================")
    print(f"Top-1 Hypothesis Accuracy:   {top1_hyp_correct_count} / {total} = {top1_hyp_correct_count/total:.1%}")
    print(f"Top-3 Hypothesis Recall:     {top3_hyp_correct_count} / {total} = {top3_hyp_correct_count/total:.1%}")
    print(f"Mean Reciprocal Rank (MRR):  {mrr:.4f} (denominator: {mrr_denominator})")
    print(f"Established Driver Accuracy: {established_driver_correct_count} / {total} = {established_driver_correct_count/total:.1%}")
    print(f"Status Accuracy:             {status_correct_count} / {total} = {status_correct_count/total:.1%}")
    print(f"Uncertainty Accuracy (S008): {uncertainty_correct_count} / {uncertainty_total} = {unc_acc:.1%}")
    print("========================================")
    print(f"Results written to {csv_path}")

if __name__ == "__main__":
    test_phase3a3_accuracy()
