import os
import pandas as pd
import json

base_dir = r"c:\Users\rajuk\OneDrive\Desktop(1)\Accenture_Decision_Intelligence"
eval_in_dir = os.path.join(base_dir, "data", "scenarios", "evaluation_inputs")
eval_gt_dir = os.path.join(base_dir, "data", "scenarios", "evaluation_ground_truth")

approved_datasets = [
    "fact_sales_monthly.csv", "fact_inventory_monthly.csv", "fact_marketing_monthly.csv",
    "fact_competitor_pricing_monthly.csv", "fact_support_tickets.csv", "fact_crm_notes.csv",
    "fact_sales_calls.csv", "dim_product.csv", "dim_customer.csv", "dim_market.csv"
]

evaluator_terms = ["true_root_cause", "root_cause", "ground_truth", "ground truth", 
                   "expected_answer", "expected root cause", "evaluator", "evaluation answer",
                   "confidence", "root_cause_status"]

evaluator_files = ["scenario_summary", "phase2b_report", "ground_truth.csv", "_truth.csv"]

def test_phase2b_remediation():
    assert os.path.exists(eval_in_dir)
    assert os.path.exists(eval_gt_dir)
    
    for s_id in [f"S00{i}" for i in range(1, 9)]:
        in_file = os.path.join(eval_in_dir, f"{s_id}_input.csv")
        gt_file = os.path.join(eval_gt_dir, f"{s_id}_truth.csv")
        
        assert os.path.exists(in_file), f"Missing {in_file}"
        assert os.path.exists(gt_file), f"Missing {gt_file}"
        
        in_df = pd.read_csv(in_file)
        gt_df = pd.read_csv(gt_file)
        
        info_cutoff = gt_df['information_cutoff_date'].iloc[0]
        
        # 1. No ground truth columns
        for col in ["true_root_cause", "root_cause_status", "confidence"]:
            assert col not in in_df.columns
            
        # 3. Source dataset approved list
        for source in in_df['source_dataset'].dropna().unique():
            assert source in approved_datasets, f"Invalid source dataset: {source}"
            
        for _, row in in_df.iterrows():
            # 5 & 6. Verify date <= information_cutoff_date
            if pd.notna(row['date']):
                # Simple string comparison works for YYYY-MM-DD
                assert row['date'] <= info_cutoff, f"Temporal leakage: {row['date']} > {info_cutoff}"
                
            # 2 & 8. No evaluator files referenced
            for ev_file in evaluator_files:
                assert ev_file not in str(row['source_dataset'])
                assert ev_file not in str(row['evidence_text'])
                
            # 7. Evaluator fields do not appear in text
            if pd.notna(row['evidence_text']):
                text = str(row['evidence_text']).lower()
                for term in evaluator_terms:
                    # Ignore legitimate words inside ticket texts but fail if it's explicitly a leakage field.
                    # Since we control the text, any evaluator term in "evidence_text" that is calculated should be caught.
                    if term in text and pd.isna(row['record_id']): 
                        # If it's unstructured text from CRM, it might randomly say "confidence". 
                        # But if it's computed by the evaluator, we flag it.
                        assert term not in text, f"Semantic Leakage: {term} found in {text}"
                        
            # 9. Calculated metrics have calculation formula
            if pd.notna(row['change_percent']) or pd.notna(row['metric_value']):
                if pd.isna(row['record_id']): # It's computed
                    assert pd.notna(row['calculation_formula']), f"Missing calculation formula for computed metric {row['metric_name']}"
                    
        # 14 & 15. Rules
        if s_id == "S007":
            assert gt_df['true_root_cause'].iloc[0] == "PRODUCT_MIX / RELATIVE_PERFORMANCE_SHIFT"
        if s_id == "S008":
            assert gt_df['root_cause_status'].iloc[0] == "NOT_ESTABLISHED"
            
    print("Semantic Leakage tests passed.")

if __name__ == "__main__":
    test_phase2b_remediation()
