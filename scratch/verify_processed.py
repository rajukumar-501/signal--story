"""
Comprehensive verification test suite for data in Data/Processed/
"""

import os
import glob
import pandas as pd
import numpy as np

def run_tests():
    print("=" * 60)
    print("RUNNING POST-CLEANING VALIDATION TESTS")
    print("=" * 60)

    processed_dir = "Data/Processed"
    files = [
        "dim_product.csv",
        "dim_customer.csv",
        "dim_market.csv",
        "fact_sales_monthly.csv",
        "fact_inventory_monthly.csv",
        "fact_marketing_monthly.csv",
        "fact_competitor_pricing_monthly.csv",
        "fact_support_tickets.csv",
        "fact_crm_notes.csv",
        "fact_sales_calls.csv"
    ]

    # Test 1: UTF-8 Readability Test
    print("\n--- Test 1: UTF-8 Readability & Loading ---")
    dfs = {}
    for fname in files:
        fpath = os.path.join(processed_dir, fname)
        try:
            df = pd.read_csv(fpath, encoding="utf-8", keep_default_na=False)
            dfs[fname] = df
            print(f"  PASS: {fname} loaded seamlessly with UTF-8 (Shape: {df.shape})")
        except Exception as e:
            print(f"  FAIL: {fname} failed UTF-8 read: {e}")
            raise

    # Test 2: Market Zone & Region Imputation Test
    print("\n--- Test 2: Market Dimension Imputation ---")
    mkt_df = dfs["dim_market.csv"]
    ca_row = mkt_df[mkt_df["market"] == "Canada"].iloc[0]
    us_row = mkt_df[mkt_df["market"] == "USA"].iloc[0]
    assert ca_row["sub_zone"] == "NA" and ca_row["region"] == "NA", "Canada region mismatch"
    assert us_row["sub_zone"] == "NA" and us_row["region"] == "NA", "USA region mismatch"
    assert not (mkt_df["sub_zone"] == "").any(), "Empty sub_zones found"
    assert not (mkt_df["region"] == "").any(), "Empty regions found"
    print(f"  PASS: Canada -> sub_zone='{ca_row['sub_zone']}', region='{ca_row['region']}'")
    print(f"  PASS: USA -> sub_zone='{us_row['sub_zone']}', region='{us_row['region']}'")
    print(f"  PASS: Zero nulls/empty strings in dim_market ({len(mkt_df)} total markets)")

    # Test 3: Date Standardization & Alignment
    print("\n--- Test 3: Date Format & Timeline Alignment ---")
    timeline_tables = [
        "fact_sales_monthly.csv",
        "fact_inventory_monthly.csv",
        "fact_marketing_monthly.csv",
        "fact_competitor_pricing_monthly.csv",
        "fact_support_tickets.csv",
        "fact_crm_notes.csv",
        "fact_sales_calls.csv"
    ]
    for tname in timeline_tables:
        df = dfs[tname]
        dt_s = pd.to_datetime(df["date"], format="%Y-%m-%d")
        min_d, max_d = dt_s.min().strftime("%Y-%m-%d"), dt_s.max().strftime("%Y-%m-%d")
        months = dt_s.dt.to_period("M").nunique()
        assert min_d == "2018-09-01", f"{tname} min date mismatch: {min_d}"
        assert max_d == "2021-08-01", f"{tname} max date mismatch: {max_d}"
        assert months == 36, f"{tname} month count mismatch: {months}"
        print(f"  PASS: {tname} date range {min_d} -> {max_d} ({months} months)")

    # Test 4: Sales Returns & Measures Consistency
    print("\n--- Test 4: Sales Returns & Quantity Normalization ---")
    sales_df = dfs["fact_sales_monthly.csv"]
    sales_df["Qty"] = pd.to_numeric(sales_df["Qty"])
    sales_df["gross_qty"] = pd.to_numeric(sales_df["gross_qty"])
    sales_df["return_qty"] = pd.to_numeric(sales_df["return_qty"])
    sales_df["net_sales_amount"] = pd.to_numeric(sales_df["net_sales_amount"])
    
    # Assert return consistency
    assert (sales_df["gross_qty"] >= 0).all(), "Negative gross_qty found"
    assert (sales_df["return_qty"] >= 0).all(), "Negative return_qty found"
    assert ((sales_df["gross_qty"] - sales_df["return_qty"]) == sales_df["Qty"]).all(), "Qty math mismatch"
    assert (sales_df["net_sales_amount"] > 0).all(), "Non-positive net_sales_amount"
    return_count = (sales_df["is_return"].astype(str) == "True").sum()
    print(f"  PASS: {return_count:,} return rows cleanly flagged out of {len(sales_df):,} ({return_count/len(sales_df)*100:.2f}%)")
    print(f"  PASS: Mathematical identity verified (gross_qty - return_qty == Qty)")
    print(f"  PASS: net_sales_amount strictly positive (min: ${sales_df['net_sales_amount'].min():.2f}, max: ${sales_df['net_sales_amount'].max():,.2f})")

    # Test 5: Referential Integrity across all processed tables
    print("\n--- Test 5: Referential Integrity (0 Orphan Keys) ---")
    prod_set = set(dfs["dim_product.csv"]["product_code"])
    cust_set = set(dfs["dim_customer.csv"]["customer_code"].astype(str))
    mkt_set = set(dfs["dim_market.csv"]["market"])

    for fname, df in dfs.items():
        if fname.startswith("dim_"): continue
        if "product_code" in df.columns:
            orphans = set(df["product_code"]) - prod_set
            assert len(orphans) == 0, f"{fname} has product_code orphans: {orphans}"
        if "customer_code" in df.columns:
            orphans = set(df["customer_code"].astype(str)) - cust_set
            assert len(orphans) == 0, f"{fname} has customer_code orphans: {orphans}"
        if "market" in df.columns:
            orphans = set(df["market"]) - mkt_set
            assert len(orphans) == 0, f"{fname} has market orphans: {orphans}"
        print(f"  PASS: {fname} foreign key validation (0 orphans)")

    print("\n" + "=" * 60)
    print("ALL POST-CLEANING TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
