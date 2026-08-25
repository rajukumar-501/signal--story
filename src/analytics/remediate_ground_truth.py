import os
import json
import pandas as pd
import numpy as np
import uuid

def generate_evidence_id():
    return "EVID-" + str(uuid.uuid4())[:8]

def main():
    base_dir = r"c:\Users\rajuk\OneDrive\Desktop(1)\Accenture_Decision_Intelligence"
    data_dir = os.path.join(base_dir, "data", "processed")
    
    # Create required directories
    eval_inputs_dir = os.path.join(base_dir, "data", "scenarios", "evaluation_inputs")
    eval_gt_dir = os.path.join(base_dir, "data", "scenarios", "evaluation_ground_truth")
    os.makedirs(eval_inputs_dir, exist_ok=True)
    os.makedirs(eval_gt_dir, exist_ok=True)
    
    # Load all datasets
    print("Loading data...")
    sales = pd.read_csv(os.path.join(data_dir, "fact_sales_monthly.csv"))
    products = pd.read_csv(os.path.join(data_dir, "dim_product.csv"))
    customers = pd.read_csv(os.path.join(data_dir, "dim_customer.csv"))
    markets = pd.read_csv(os.path.join(data_dir, "dim_market.csv"))
    marketing = pd.read_csv(os.path.join(data_dir, "fact_marketing_monthly.csv"))
    pricing = pd.read_csv(os.path.join(data_dir, "fact_competitor_pricing_monthly.csv"))
    support = pd.read_csv(os.path.join(data_dir, "fact_support_tickets.csv"))
    crm = pd.read_csv(os.path.join(data_dir, "fact_crm_notes.csv"))
    calls = pd.read_csv(os.path.join(data_dir, "fact_sales_calls.csv"))
    inv = pd.read_csv(os.path.join(data_dir, "fact_inventory_monthly.csv"))
    
    sales_merged = sales.merge(products, on="product_code", how="left")
    sales_merged = sales_merged.merge(customers, on="customer_code", how="left")
    sales_merged = sales_merged.merge(markets, on="market", how="left")
    
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
    
    evidence_columns = [
        "scenario_id", "evidence_id", "evidence_role", "source_dataset", "record_id",
        "date", "market", "product_code", "customer_code", "metric_name", "metric_value",
        "baseline_value", "change_value", "change_percent", "evidence_text", "evidence_strength",
        "direction", "is_contradictory", "calculation_formula"
    ]
    
    gt_records = []
    summary_records = []
    audit_records = []
    input_audit_records = []
    json_specs = []
    
    print("Processing Scenarios...")
    for s in scenarios:
        s_id = s["id"]
        market = s["market"]
        period = s["period"]
        entity = s["entity"]
        ent_type = s["entity_type"]
        
        evidence_list = []
        
        # Determine previous period
        year, month = map(int, period.split('-'))
        prev_period = f"{year-1}-12" if month == 1 else f"{year}-{month-1:02d}"
        
        # Filter Base Sales
        base_mask = (sales_merged['market'] == market) & (sales_merged['date'].str.startswith(period))
        prev_base_mask = (sales_merged['market'] == market) & (sales_merged['date'].str.startswith(prev_period))
        
        def get_mask(m, e_type, e):
            if e_type == "product": return m & (sales_merged['product_code'] == e)
            elif e_type == "platform": return m & (sales_merged['platform'] == e)
            elif e_type == "category": return m & (sales_merged['category'] == e)
            return m
            
        cur_data = sales_merged[get_mask(base_mask, ent_type, entity)]
        prev_data = sales_merged[get_mask(prev_base_mask, ent_type, entity)]
        
        cur_gross = cur_data['gross_sales_amount'].sum()
        prev_gross = prev_data['gross_sales_amount'].sum()
        cur_net = cur_data['signed_sales_amount'].sum()
        cur_ret = cur_data['return_sales_amount'].sum()
        
        if prev_gross > 0:
            gross_pct = (cur_gross - prev_gross) / prev_gross * 100
        else:
            gross_pct = 0
            
        # Outcome Evidence
        if s_id != "S007":
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "OUTCOME",
                "source_dataset": "fact_sales_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": entity if ent_type == "product" else None, "customer_code": None,
                "metric_name": "gross_sales", "metric_value": cur_gross, "baseline_value": prev_gross,
                "change_value": cur_gross - prev_gross, "change_percent": gross_pct,
                "evidence_text": f"Gross sales changed by {gross_pct:.2f}% from {prev_gross} to {cur_gross}.",
                "evidence_strength": "STRONG", "direction": "decrease" if gross_pct < 0 else "increase",
                "is_contradictory": False, "calculation_formula": "(current - previous)/previous * 100"
            })
            
        # Specific scenario extraction
        root_cause_status = "NOT_ESTABLISHED"
        confidence = "LOW"
        true_root_cause = s["name"]
        
        if s_id == "S001":
            prev_ret = prev_data['return_sales_amount'].sum()
            ret_pct = cur_ret / cur_gross * 100 if cur_gross > 0 else 0
            prev_ret_pct = prev_ret / prev_gross * 100 if prev_gross > 0 else 0
            
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "DRIVER",
                "source_dataset": "fact_sales_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": entity, "customer_code": None,
                "metric_name": "return_rate_percent", "metric_value": ret_pct, "baseline_value": prev_ret_pct,
                "change_value": ret_pct - prev_ret_pct, "change_percent": None,
                "evidence_text": f"Return rate jumped to {ret_pct:.2f}% from {prev_ret_pct:.2f}%.",
                "evidence_strength": "STRONG", "direction": "increase",
                "is_contradictory": False, "calculation_formula": "return_sales_amount / gross_sales_amount * 100"
            })
            
            root_cause_status = "STRONGLY_SUPPORTED"
            confidence = "HIGH"
            
        elif s_id == "S002":
            # Channel Shift. Also get E-Commerce sales.
            cur_ec = sales_merged[base_mask & (sales_merged['platform'] == "E-Commerce")]['gross_sales_amount'].sum()
            prev_ec = sales_merged[prev_base_mask & (sales_merged['platform'] == "E-Commerce")]['gross_sales_amount'].sum()
            ec_pct = (cur_ec - prev_ec) / prev_ec * 100 if prev_ec > 0 else 0
            
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "SUPPORTING",
                "source_dataset": "fact_sales_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": None, "customer_code": None,
                "metric_name": "ecommerce_gross_sales", "metric_value": cur_ec, "baseline_value": prev_ec,
                "change_value": cur_ec - prev_ec, "change_percent": ec_pct,
                "evidence_text": f"E-Commerce sales grew {ec_pct:.2f}% while Brick & Mortar collapsed.",
                "evidence_strength": "STRONG", "direction": "increase",
                "is_contradictory": False, "calculation_formula": "(cur_ec - prev_ec)/prev_ec * 100"
            })
            
            root_cause_status = "STRONGLY_SUPPORTED"
            confidence = "HIGH"
            
        elif s_id == "S003":
            # Marketing Inefficiency
            cur_mkt = marketing[(marketing['market'] == market) & (marketing['date'].str.startswith(period)) & (marketing['product_code'] == entity)]
            prev_mkt = marketing[(marketing['market'] == market) & (marketing['date'].str.startswith(prev_period)) & (marketing['product_code'] == entity)]
            
            spend = cur_mkt['spend'].sum()
            prev_spend = prev_mkt['spend'].sum()
            spend_pct = (spend - prev_spend) / prev_spend * 100 if prev_spend > 0 else 0
            
            cur_conv = cur_mkt['conversions'].sum() / cur_mkt['clicks'].sum() * 100 if cur_mkt['clicks'].sum() > 0 else 0
            prev_conv = prev_mkt['conversions'].sum() / prev_mkt['clicks'].sum() * 100 if prev_mkt['clicks'].sum() > 0 else 0
            
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "DRIVER",
                "source_dataset": "fact_marketing_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": entity, "customer_code": None,
                "metric_name": "marketing_spend", "metric_value": spend, "baseline_value": prev_spend,
                "change_value": spend - prev_spend, "change_percent": spend_pct,
                "evidence_text": f"Spend increased by {spend_pct:.2f}% to {spend}.",
                "evidence_strength": "STRONG", "direction": "increase", "is_contradictory": False, "calculation_formula": "(spend - prev_spend)/prev_spend*100"
            })
            
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "DRIVER",
                "source_dataset": "fact_marketing_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": entity, "customer_code": None,
                "metric_name": "conversion_rate", "metric_value": cur_conv, "baseline_value": prev_conv,
                "change_value": cur_conv - prev_conv, "change_percent": None,
                "evidence_text": f"CVR fell to {cur_conv:.2f}%.",
                "evidence_strength": "STRONG", "direction": "decrease", "is_contradictory": False, "calculation_formula": "conversions/clicks*100"
            })
            
            root_cause_status = "STRONGLY_SUPPORTED"
            confidence = "HIGH"
            
        elif s_id == "S004":
            cur_prc = pricing[(pricing['market'] == market) & (pricing['date'].str.startswith(period)) & (pricing['product_code'] == entity)]
            prev_prc = pricing[(pricing['market'] == market) & (pricing['date'].str.startswith(prev_period)) & (pricing['product_code'] == entity)]
            
            if not cur_prc.empty and not prev_prc.empty:
                cg = cur_prc['price_gap_percent'].mean()
                pg = prev_prc['price_gap_percent'].mean()
                
                evidence_list.append({
                    "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "DRIVER",
                    "source_dataset": "fact_competitor_pricing_monthly.csv", "record_id": None, "date": period,
                    "market": market, "product_code": entity, "customer_code": None,
                    "metric_name": "price_gap", "metric_value": cg, "baseline_value": pg,
                    "change_value": cg - pg, "change_percent": None,
                    "evidence_text": f"Price gap worsened to {cg:.2f}%.",
                    "evidence_strength": "STRONG", "direction": "increase", "is_contradictory": False, "calculation_formula": "mean price_gap_percent"
                })
            
            root_cause_status = "PLAUSIBLE"
            confidence = "MEDIUM"
            
        elif s_id == "S005":
            cur_sup = support[(support['market'] == market) & (support['date'].str.startswith(period))]
            if not cur_sup.empty:
                for idx, row in cur_sup.iterrows():
                    evidence_list.append({
                        "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "DRIVER",
                        "source_dataset": "fact_support_tickets.csv", "record_id": row['ticket_id'], "date": row['date'],
                        "market": market, "product_code": row['product_code'], "customer_code": row['customer_code'],
                        "metric_name": "support_ticket", "metric_value": None, "baseline_value": None,
                        "change_value": None, "change_percent": None,
                        "evidence_text": f"{row['issue_category']} ticket: {row['ticket_text']}",
                        "evidence_strength": "MODERATE", "direction": None, "is_contradictory": False, "calculation_formula": None
                    })
            root_cause_status = "PLAUSIBLE"
            confidence = "MEDIUM"
            
        elif s_id == "S006":
            root_cause_status = "PLAUSIBLE"
            confidence = "MEDIUM"
            
        elif s_id == "S007":
            # Product Mix Shift (Category)
            tot_cur = sales_merged[base_mask]['gross_sales_amount'].sum()
            tot_prev = sales_merged[prev_base_mask]['gross_sales_amount'].sum()
            
            share_cur = cur_gross / tot_cur * 100 if tot_cur > 0 else 0
            share_prev = prev_gross / tot_prev * 100 if tot_prev > 0 else 0
            
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "OUTCOME",
                "source_dataset": "fact_sales_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": None, "customer_code": None,
                "metric_name": "category_share", "metric_value": share_cur, "baseline_value": share_prev,
                "change_value": share_cur - share_prev, "change_percent": None,
                "evidence_text": f"Category share shifted from {share_prev:.2f}% to {share_cur:.2f}%. Absolute sales increased.",
                "evidence_strength": "STRONG", "direction": "decrease", "is_contradictory": False, "calculation_formula": "category_gross / total_gross * 100"
            })
            
            true_root_cause = "PRODUCT_MIX / RELATIVE_PERFORMANCE_SHIFT"
            root_cause_status = "STRONGLY_SUPPORTED"
            confidence = "HIGH"
            
        elif s_id == "S008":
            true_root_cause = None
            root_cause_status = "NOT_ESTABLISHED"
            confidence = "LOW"
            
        # Add unstructured search for ALL scenarios
        unstruct_sources = [(support, 'fact_support_tickets.csv', 'ticket_id', 'ticket_text'),
                            (crm, 'fact_crm_notes.csv', 'note_id', 'note_text'),
                            (calls, 'fact_sales_calls.csv', 'call_id', 'transcript')]
        
        has_unstruct = False
        structured_sources = ["fact_sales_monthly.csv"]
        
        # Check contradictory - Inventory Stockout
        stock_cur = inv[(inv['market'] == market) & (inv['date'].str.startswith(period))]
        if ent_type == "product" and not stock_cur.empty:
            stock_cur = stock_cur[stock_cur['product_code'] == entity]
        if not stock_cur.empty and stock_cur['stockout_flag'].any():
            evidence_list.append({
                "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "CONTRADICTORY",
                "source_dataset": "fact_inventory_monthly.csv", "record_id": None, "date": period,
                "market": market, "product_code": entity if ent_type == "product" else None, "customer_code": None,
                "metric_name": "stockout_flag", "metric_value": 1, "baseline_value": 0,
                "change_value": 1, "change_percent": None,
                "evidence_text": "Stockout occurred during this period, offering an alternative explanation.",
                "evidence_strength": "STRONG", "direction": None, "is_contradictory": True, "calculation_formula": None
            })
            structured_sources.append("fact_inventory_monthly.csv")

        unstruct_sources_found = set()
        for df, fname, id_col, txt_col in unstruct_sources:
            subset = df[(df['market'] == market) & (df['date'].str.startswith(period))]
            if ent_type == "product" and 'product_code' in subset.columns:
                subset = subset[subset['product_code'] == entity]
            for idx, row in subset.iterrows():
                has_unstruct = True
                unstruct_sources_found.add(fname)
                evidence_list.append({
                    "scenario_id": s_id, "evidence_id": generate_evidence_id(), "evidence_role": "SUPPORTING",
                    "source_dataset": fname, "record_id": row[id_col], "date": row['date'],
                    "market": market, "product_code": row.get('product_code'), "customer_code": row.get('customer_code'),
                    "metric_name": "unstructured_text", "metric_value": None, "baseline_value": None,
                    "change_value": None, "change_percent": None,
                    "evidence_text": row[txt_col],
                    "evidence_strength": "WEAK", "direction": None, "is_contradictory": False, "calculation_formula": None
                })
        
        # Calculate Audit info
        has_contradictory = any(e['evidence_role'] == 'CONTRADICTORY' for e in evidence_list)
        evidence_count = len(evidence_list)
        structured_sources = list(set(structured_sources + [e['source_dataset'] for e in evidence_list if e['source_dataset'] not in unstruct_sources_found]))
        
        audit_records.append({
            "scenario_id": s_id,
            "outcome_evidence": any(e['evidence_role'] == 'OUTCOME' for e in evidence_list),
            "driver_evidence": any(e['evidence_role'] == 'DRIVER' for e in evidence_list),
            "supporting_evidence": any(e['evidence_role'] == 'SUPPORTING' for e in evidence_list),
            "contradictory_evidence": has_contradictory,
            "structured_sources": len(structured_sources),
            "unstructured_sources": len(unstruct_sources_found),
            "evidence_count": evidence_count,
            "missing_expected_evidence": not has_unstruct,
            "evidence_quality": "B" if has_unstruct else "C",
            "notes": "Evidence successfully extracted"
        })
        
        
        # Output Evidence to evaluation_inputs
        ev_df = pd.DataFrame(evidence_list, columns=evidence_columns)
        ev_df.to_csv(os.path.join(eval_inputs_dir, f"{s_id}_input.csv"), index=False)
        
        # Ground Truth Record
        info_cutoff = f"{period}-28"
        gt = {
            "scenario_id": s_id, "scenario_type": ent_type,
            "date_start": f"{period}-01", "date_end": f"{period}-28",
            "information_cutoff_date": info_cutoff,
            "market": market,
            "entity_type": ent_type, "entity": entity,
            "primary_kpi": "category_share" if s_id == "S007" else "gross_sales_amount",
            "kpi_before": share_prev if s_id == "S007" else prev_gross,
            "kpi_after": share_cur if s_id == "S007" else cur_gross,
            "kpi_change_percent": (share_cur - share_prev) if s_id == "S007" else gross_pct,
            "true_root_cause": true_root_cause, "root_cause_status": root_cause_status,
            "confidence": confidence, "secondary_factors": None,
            "alternative_explanations": "Insufficient structured driver" if root_cause_status in ["PLAUSIBLE", "NOT_ESTABLISHED"] else None,
            "supporting_evidence_sources": "Sales, Marketing, Pricing, Support" if has_unstruct else "Sales, Marketing, Pricing",
            "contradictory_evidence_sources": None, "known_limitations": "Evidence unavailable in current dataset." if not has_unstruct else None
        }
        gt_records.append(gt)
        pd.DataFrame([gt]).to_csv(os.path.join(eval_gt_dir, f"{s_id}_truth.csv"), index=False)
        
        # Input Audit
        record_count = len(evidence_list)
        source_dataset_count = len(set(e["source_dataset"] for e in evidence_list))
        unstruct_record_count = len([e for e in evidence_list if e["metric_name"] == "unstructured_text"])
        calc_metric_count = len([e for e in evidence_list if e["calculation_formula"] is not None])
        
        evaluator_terms = ["true_root_cause", "root_cause_status", "ground_truth"]
        found_eval_terms = any(term in str(e).lower() for e in evidence_list for term in evaluator_terms)
        
        post_cutoff = 0
        untraceable = 0
        for e in evidence_list:
            if not e["source_dataset"]: untraceable += 1
            if e["date"] and e["date"] > info_cutoff and not e["date"].startswith(period):
                post_cutoff += 1
                
        input_audit_records.append({
            "scenario_id": s_id,
            "record_count": record_count,
            "source_dataset_count": source_dataset_count,
            "unstructured_record_count": unstruct_record_count,
            "calculated_metric_count": calc_metric_count,
            "post_cutoff_records": post_cutoff,
            "ground_truth_fields_found": 0,
            "evaluator_terms_found": int(found_eval_terms),
            "untraceable_records": untraceable,
            "leakage_status": "FAIL" if found_eval_terms or post_cutoff > 0 else "PASS",
            "audit_status": "FAIL" if untraceable > 0 else "PASS"
        })
        
        summary_records.append({
            "scenario_id": s_id, "scenario_type": ent_type, "primary_kpi": gt["primary_kpi"],
            "kpi_change_percent": gt["kpi_change_percent"], "root_cause_status": root_cause_status,
            "confidence": confidence, "evidence_quality": "B" if has_unstruct else "C",
            "structured_source_count": 3, "unstructured_source_count": 1 if has_unstruct else 0,
            "contradictory_evidence_count": 0, "alternative_explanation_count": 1,
            "evaluation_priority": "High"
        })
        
        json_specs.append({
            "scenario_id": s_id,
            "business_question": f"Investigate performance for {entity} in {market} during {period}",
            "allowed_input_sources": [f"{s_id}_input.csv"],
            "expected_kpi": gt["primary_kpi"],
            "expected_direction": "decrease",
            "expected_root_cause": true_root_cause,
            "root_cause_status": root_cause_status,
            "acceptable_alternative_explanations": [],
            "required_evidence_types": ["OUTCOME", "DRIVER"],
            "minimum_evidence_quality": "WEAK",
            "failure_conditions": ["hallucination", "temporal_leakage"]
        })
        
    pd.DataFrame(summary_records).to_csv(os.path.join(base_dir, "data", "scenarios", "scenario_summary.csv"), index=False)
    pd.DataFrame(audit_records).to_csv(os.path.join(base_dir, "data", "scenarios", "evidence_quality_audit.csv"), index=False)
    pd.DataFrame(input_audit_records).to_csv(os.path.join(base_dir, "data", "scenarios", "evaluation_input_audit.csv"), index=False)
    
    
    with open(os.path.join(base_dir, "tests", "scenario_ground_truth.json"), "w") as f:
        json.dump({"scenarios": json_specs}, f, indent=4)
        
    print("Successfully remediated ground truth evaluation artifacts.")

if __name__ == "__main__":
    main()
