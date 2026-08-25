import os
import pandas as pd
import json

base_dir = r"c:\Users\rajuk\OneDrive\Desktop(1)\Accenture_Decision_Intelligence"
eval_in_dir = os.path.join(base_dir, "data", "scenarios", "evaluation_inputs")
data_dir = os.path.join(base_dir, "data", "processed")

def test_evidence_traceability():
    # Pre-load datasets to check record existence
    datasets = {}
    for f in os.listdir(data_dir):
        if f.endswith('.csv'):
            datasets[f] = pd.read_csv(os.path.join(data_dir, f))
            
    for s_id in [f"S00{i}" for i in range(1, 9)]:
        in_file = os.path.join(eval_in_dir, f"{s_id}_input.csv")
        in_df = pd.read_csv(in_file)
        
        for _, row in in_df.iterrows():
            source = row['source_dataset']
            assert pd.notna(source), "Missing source dataset"
            assert source in datasets, f"Source {source} not loaded"
            
            # If it's a raw unstructured record, check record_id
            if pd.notna(row['record_id']):
                # Find the ID column
                df = datasets[source]
                id_cols = [c for c in df.columns if c.endswith('_id')]
                
                # fact_support_tickets has ticket_id, fact_crm_notes has note_id, fact_sales_calls has call_id
                found = False
                for id_col in id_cols:
                    if row['record_id'] in df[id_col].values:
                        found = True
                        break
                assert found, f"Record ID {row['record_id']} not found in {source}"
                
            # Date must be valid
            assert pd.notna(row['date']), f"Missing date in {row}"
            
    print("Evidence Traceability tests passed.")

if __name__ == "__main__":
    test_evidence_traceability()
