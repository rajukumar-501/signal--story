import os
import json
import pandas as pd
import numpy as np

def main():
    base_dir = r"c:\Users\rajuk\OneDrive\Desktop(1)\Accenture_Decision_Intelligence"
    data_dir = os.path.join(base_dir, "data", "processed")
    scenarios_dir = os.path.join(base_dir, "data", "scenarios")
    tests_dir = os.path.join(base_dir, "tests")
    docs_dir = os.path.join(base_dir, "docs")

    os.makedirs(scenarios_dir, exist_ok=True)
    os.makedirs(tests_dir, exist_ok=True)
    
    # Load data
    print("Loading datasets...")
    sales = pd.read_csv(os.path.join(data_dir, "fact_sales_monthly.csv"))
    products = pd.read_csv(os.path.join(data_dir, "dim_product.csv"))
    customers = pd.read_csv(os.path.join(data_dir, "dim_customer.csv"))
    markets = pd.read_csv(os.path.join(data_dir, "dim_market.csv"))
    marketing = pd.read_csv(os.path.join(data_dir, "fact_marketing_monthly.csv"))
    pricing = pd.read_csv(os.path.join(data_dir, "fact_competitor_pricing_monthly.csv"))
    support = pd.read_csv(os.path.join(data_dir, "fact_support_tickets.csv"))
    
    # Merge Sales
    sales_merged = sales.merge(products, on="product_code", how="left")
    sales_merged = sales_merged.merge(customers, on="customer_code", how="left")
    sales_merged = sales_merged.merge(markets, on="market", how="left")
    
    # Scenarios config
    scenarios = [
        {"id": "S001", "name": "Returns spike", "market": "South Korea", "entity": "A6519160401", "period": "2021-05", "entity_type": "product"},
        {"id": "S002", "name": "Channel shift", "market": "South Korea", "entity": "Brick & Mortar", "period": "2021-01", "entity_type": "platform"},
        {"id": "S003", "name": "Marketing inefficiency", "market": "China", "entity": "A2520150501", "period": "2021-04", "entity_type": "product"},
        {"id": "S004", "name": "Competitive pricing pressure", "market": "China", "entity": "A0621150308", "period": "2021-01", "entity_type": "product"},
        {"id": "S005", "name": "Customer service / delivery deterioration", "market": "Indonesia", "entity": "Market", "period": "2020-03", "entity_type": "market"},
        {"id": "S006", "name": "Category demand collapse", "market": "India", "entity": "Processors", "period": "2020-03", "entity_type": "category"},
        {"id": "S007", "name": "Product-mix shift", "market": "Portugal", "entity": "Wi fi extender", "period": "2019-09", "entity_type": "category"},
        {"id": "S008", "name": "Market-wide unexplained shock", "market": "Germany", "entity": "Market", "period": "2020-03", "entity_type": "market"}
    ]
    
    # Evaluate each scenario
    verification_results = []
    ground_truth_records = []
    scenario_summary_records = []
    json_specs = []
    
    for s in scenarios:
        s_id = s["id"]
        market = s["market"]
        period = s["period"]
        entity = s["entity"]
        ent_type = s["entity_type"]
        name = s["name"]
        
        # 1. Verification Logic
        base_mask = (sales_merged['market'] == market) & (sales_merged['date'].str.startswith(period))
        if ent_type == "product":
            mask = base_mask & (sales_merged['product_code'] == entity)
            entity_label = f"product_code: {entity}"
        elif ent_type == "channel":
            mask = base_mask & (sales_merged['channel'] == entity)
            entity_label = f"channel: {entity}"
        elif ent_type == "platform":
            mask = base_mask & (sales_merged['platform'] == entity)
            entity_label = f"platform: {entity}"
        elif ent_type == "market":
            mask = base_mask
            entity_label = f"market: {market}"
        elif ent_type == "category":
            mask = base_mask & (sales_merged['category'] == entity)
            entity_label = f"category: {entity}"
        elif ent_type == "segment":
            mask = base_mask & (sales_merged['segment'] == entity)
            entity_label = f"segment: {entity}"
        else:
            mask = base_mask
            entity_label = entity
            
        cur_data = sales_merged[mask]
        cur_gross = cur_data['gross_sales_amount'].sum()
        cur_net = cur_data['signed_sales_amount'].sum()
        cur_return = cur_data['return_sales_amount'].sum()
        
        # previous month logic
        year, month = map(int, period.split('-'))
        if month == 1:
            prev_period = f"{year-1}-12"
        else:
            prev_period = f"{year}-{month-1:02d}"
            
        prev_base_mask = (sales_merged['market'] == market) & (sales_merged['date'].str.startswith(prev_period))
        if ent_type == "product":
            prev_mask = prev_base_mask & (sales_merged['product_code'] == entity)
        elif ent_type == "channel":
            prev_mask = prev_base_mask & (sales_merged['channel'] == entity)
        elif ent_type == "platform":
            prev_mask = prev_base_mask & (sales_merged['platform'] == entity)
        elif ent_type == "category":
            prev_mask = prev_base_mask & (sales_merged['category'] == entity)
        elif ent_type == "segment":
            prev_mask = prev_base_mask & (sales_merged['segment'] == entity)
        else:
            prev_mask = prev_base_mask
            
        prev_data = sales_merged[prev_mask]
        prev_gross = prev_data['gross_sales_amount'].sum()
        
        if prev_gross > 0:
            gross_change = (cur_gross - prev_gross) / prev_gross * 100
        else:
            gross_change = None
            
        # Cross-source evidence extraction
        marketing_spend = 0
        cvr = 0
        if ent_type == "product":
            cur_mkt = marketing[(marketing['market'] == market) & (marketing['date'].str.startswith(period)) & (marketing['product_code'] == entity)]
            if not cur_mkt.empty:
                marketing_spend = cur_mkt['spend'].sum()
                clicks = cur_mkt['clicks'].sum()
                convs = cur_mkt['conversions'].sum()
                cvr = convs / clicks if clicks > 0 else 0
                
        price_gap = 0
        if ent_type == "product":
            cur_prc = pricing[(pricing['market'] == market) & (pricing['date'].str.startswith(period)) & (pricing['product_code'] == entity)]
            if not cur_prc.empty:
                price_gap = cur_prc['price_gap_percent'].mean()
                
        support_tickets = 0
        if ent_type == "market":
            cur_sup = support[(support['market'] == market) & (support['date'].str.startswith(period))]
            if not cur_sup.empty:
                support_tickets = len(cur_sup)
            
        verification_results.append({
            "scenario_id": s_id,
            "scenario_name": name,
            "period": period,
            "market": market,
            "entity": entity,
            "cur_gross_sales": cur_gross,
            "cur_return_sales": cur_return,
            "prev_gross_sales": prev_gross,
            "gross_change_pct": gross_change,
            "marketing_spend": marketing_spend,
            "cvr": cvr,
            "price_gap": price_gap,
            "support_tickets": support_tickets
        })
        
        # Compile evidence CSVs
        evidence_cols = ['date', 'market', 'customer_code', 'product_code', 'channel', 'gross_sales_amount', 'return_sales_amount', 'signed_sales_amount']
        evidence_data = pd.concat([prev_data, cur_data])[evidence_cols]
        evidence_file = os.path.join(scenarios_dir, f"{s_id}_evidence.csv")
        evidence_data.to_csv(evidence_file, index=False)
        
        # Ground Truth Records
        ground_truth_records.append({
            "scenario_id": s_id,
            "market": market,
            "entity_type": ent_type,
            "entity": entity,
            "date": period,
            "true_root_cause": name
        })
        
        # Summary Records
        scenario_summary_records.append({
            "scenario_id": s_id,
            "name": name,
            "market": market,
            "entity": entity,
            "date": period,
            "evidence_file": f"{s_id}_evidence.csv"
        })
        
        # JSON Specs (Without Root Cause Hints!)
        json_specs.append({
            "scenario_id": s_id,
            "description": f"Investigate revenue anomaly for {entity_label} in {market} during {period}",
            "market": market,
            "date": period,
            "entity": entity,
            "entity_type": ent_type
        })
        
    pd.DataFrame(verification_results).to_csv(os.path.join(scenarios_dir, "scenario_verification.csv"), index=False)
    pd.DataFrame(ground_truth_records).to_csv(os.path.join(scenarios_dir, "ground_truth.csv"), index=False)
    pd.DataFrame(scenario_summary_records).to_csv(os.path.join(scenarios_dir, "scenario_summary.csv"), index=False)
    
    with open(os.path.join(tests_dir, "scenario_ground_truth.json"), "w") as f:
        json.dump({"scenarios": json_specs}, f, indent=4)
        
    print("Generated CSVs and JSONs.")

if __name__ == "__main__":
    main()
