"""
Accenture Decision Intelligence Platform - Data Preprocessing & Cleaning Pipeline
Standardizes encodings, formats dates to ISO 8601, resolves dimension gaps,
and generates clean, production-ready datasets in data/processed/.
"""

import os
import pandas as pd
import numpy as np

def run_preprocessing():
    print("=" * 60)
    print("Starting Data Preprocessing & Cleaning Pipeline")
    print("=" * 60)

    raw_dir = "Data/raw"
    synthetic_dir = "Data/Synthetic"
    processed_dir = "Data/Processed"
    validation_dir = "Data/validation"
    
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(validation_dir, exist_ok=True)

    # -------------------------------------------------------------
    # 1. Clean and Standardize Master Dimensions
    # -------------------------------------------------------------
    print("\n[1/4] Processing Master Dimension Tables...")

    # 1a. dim_product (Latin1 -> UTF-8, normalize special chars)
    dim_product_path = os.path.join(raw_dir, "dim_product.csv")
    dim_product = pd.read_csv(dim_product_path, encoding="latin1")
    for col in dim_product.columns:
        if dim_product[col].dtype == object or str(dim_product[col].dtype).startswith("str"):
            dim_product[col] = dim_product[col].astype(str).str.replace('\x96', '-').str.replace('–', '-').str.strip()
    
    out_prod_path = os.path.join(processed_dir, "dim_product.csv")
    dim_product.to_csv(out_prod_path, index=False, encoding="utf-8")
    print(f"  [OK] dim_product: {len(dim_product)} rows saved to {out_prod_path} (UTF-8)")

    # 1b. dim_customer (Latin1 -> UTF-8)
    dim_customer_path = os.path.join(raw_dir, "dim_customer.csv")
    dim_customer = pd.read_csv(dim_customer_path, encoding="latin1")
    for col in dim_customer.columns:
        if dim_customer[col].dtype == object or str(dim_customer[col].dtype).startswith("str"):
            dim_customer[col] = dim_customer[col].astype(str).str.replace('\x96', '-').str.replace('–', '-').str.strip()
    
    out_cust_path = os.path.join(processed_dir, "dim_customer.csv")
    dim_customer.to_csv(out_cust_path, index=False, encoding="utf-8")
    print(f"  [OK] dim_customer: {len(dim_customer)} rows saved to {out_cust_path} (UTF-8)")

    # 1c. dim_market (Fix missing sub_zone and region for Canada and USA)
    dim_market_path = os.path.join(raw_dir, "dim_market.csv")
    dim_market = pd.read_csv(dim_market_path, encoding="utf-8", keep_default_na=False)
    # If sub_zone or region are 'nan' or empty or null, fix Canada and USA
    dim_market.loc[dim_market["market"].isin(["Canada", "USA"]), "sub_zone"] = "NA"
    dim_market.loc[dim_market["market"].isin(["Canada", "USA"]), "region"] = "NA"
    
    out_mkt_path = os.path.join(processed_dir, "dim_market.csv")
    dim_market.to_csv(out_mkt_path, index=False, encoding="utf-8")
    print(f"  [OK] dim_market: {len(dim_market)} rows saved to {out_mkt_path} (fixed Canada/USA regions to 'NA')")

    # -------------------------------------------------------------
    # 2. Clean and Standardize Fact Sales Monthly
    # -------------------------------------------------------------
    print("\n[2/4] Processing Master Transaction Table (fact_sales_monthly)...")
    sales_path = os.path.join(raw_dir, "fact_sales_monthly.csv")
    sales_df = pd.read_csv(sales_path, encoding="utf-8")
    
    # Standardize dates from DD-MM-YYYY HH:MM to YYYY-MM-DD
    sales_df["date"] = pd.to_datetime(sales_df["date"], format="%d-%m-%Y %H:%M").dt.strftime("%Y-%m-%d")
    
    # Add analytical helper fields for return modeling
    sales_df["is_return"] = sales_df["Qty"] < 0
    sales_df["gross_qty"] = np.maximum(sales_df["Qty"], 0)
    sales_df["return_qty"] = np.abs(np.minimum(sales_df["Qty"], 0))
    
    # Financial fields: net_sales_amount is positive transaction amount
    sales_df["signed_sales_amount"] = np.where(sales_df["Qty"] < 0, -sales_df["net_sales_amount"], sales_df["net_sales_amount"])
    sales_df["gross_sales_amount"] = np.where(sales_df["Qty"] > 0, sales_df["net_sales_amount"], 0.0)
    sales_df["return_sales_amount"] = np.where(sales_df["Qty"] < 0, sales_df["net_sales_amount"], 0.0)
    
    out_sales_path = os.path.join(processed_dir, "fact_sales_monthly.csv")
    sales_df.to_csv(out_sales_path, index=False, encoding="utf-8")
    print(f"  [OK] fact_sales_monthly: {len(sales_df):,} rows saved to {out_sales_path}")
    print(f"    - Date format standardized to ISO YYYY-MM-DD (min: {sales_df['date'].min()}, max: {sales_df['date'].max()})")
    print(f"    - Added return metrics: {sales_df['is_return'].sum():,} return transactions identified")
    print(f"    - Added signed financial revenue: gross=${sales_df['gross_sales_amount'].sum():,.2f}, return=${sales_df['return_sales_amount'].sum():,.2f}, net=${sales_df['signed_sales_amount'].sum():,.2f}")

    # -------------------------------------------------------------
    # 3. Clean and Standardize Synthetic Fact Tables
    # -------------------------------------------------------------
    print("\n[3/4] Processing Synthetic Tables...")
    synthetic_files = [
        "fact_inventory_monthly.csv",
        "fact_marketing_monthly.csv",
        "fact_competitor_pricing_monthly.csv",
        "fact_support_tickets.csv",
        "fact_crm_notes.csv",
        "fact_sales_calls.csv"
    ]

    for fname in synthetic_files:
        fpath = os.path.join(synthetic_dir, fname)
        df_syn = pd.read_csv(fpath, encoding="utf-8")
        
        # Standardize date if present
        if "date" in df_syn.columns:
            df_syn["date"] = pd.to_datetime(df_syn["date"]).dt.strftime("%Y-%m-%d")
            
        # Clean string columns
        for col in df_syn.columns:
            if df_syn[col].dtype == object or str(df_syn[col].dtype).startswith("str"):
                df_syn[col] = df_syn[col].astype(str).str.strip()
            
        out_path = os.path.join(processed_dir, fname)
        df_syn.to_csv(out_path, index=False, encoding="utf-8")
        print(f"  [OK] {fname}: {len(df_syn):,} rows saved to {out_path}")

    # -------------------------------------------------------------
    # 4. Generate Processed Data Profile
    # -------------------------------------------------------------
    print("\n[4/4] Generating Clean Data Profile...")
    all_processed_files = [
        ("dim_product.csv", "master_dimension"),
        ("dim_customer.csv", "master_dimension"),
        ("dim_market.csv", "master_dimension"),
        ("fact_sales_monthly.csv", "master_fact"),
        ("fact_inventory_monthly.csv", "synthetic_fact"),
        ("fact_marketing_monthly.csv", "synthetic_fact"),
        ("fact_competitor_pricing_monthly.csv", "synthetic_fact"),
        ("fact_support_tickets.csv", "synthetic_fact"),
        ("fact_crm_notes.csv", "synthetic_fact"),
        ("fact_sales_calls.csv", "synthetic_fact")
    ]

    profile_records = []
    for fname, cat in all_processed_files:
        fpath = os.path.join(processed_dir, fname)
        df = pd.read_csv(fpath, encoding="utf-8", keep_default_na=False)
        file_size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 2)
        
        for col in df.columns:
            s = df[col]
            # When keep_default_na=False, empty strings are ''
            empty_count = int((s == '').sum()) if s.dtype == object or str(s.dtype).startswith("str") else int(s.isnull().sum())
            total_rows = len(df)
            null_pct = round((empty_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = int(s.nunique())
            
            min_val = ""
            max_val = ""
            mean_val = ""
            std_val = ""
            
            # Numeric check
            if pd.api.types.is_numeric_dtype(s):
                min_val = str(s.min())
                max_val = str(s.max())
                mean_val = f"{s.mean():.4f}"
                std_val = f"{s.std():.4f}"
            elif 'date' in col.lower():
                min_val = str(s.min())
                max_val = str(s.max())
            else:
                sample_uniques = s[s != ''].unique()
                if unique_count <= 10:
                    min_val = " | ".join(map(str, sample_uniques[:5]))
                else:
                    min_val = f"{unique_count} unique values (e.g. {sample_uniques[0] if len(sample_uniques) > 0 else ''})"

            profile_records.append({
                "dataset": fname,
                "category": cat,
                "file_size_mb": file_size_mb,
                "total_rows": total_rows,
                "total_cols": len(df.columns),
                "column_name": col,
                "data_type": str(s.dtype),
                "null_count": empty_count,
                "null_pct": null_pct,
                "unique_values": unique_count,
                "min_or_summary": min_val,
                "max_val": max_val,
                "mean": mean_val,
                "std": std_val
            })

    profile_df = pd.DataFrame(profile_records)
    prof_out_path = os.path.join(validation_dir, "data_profile_processed.csv")
    profile_df.to_csv(prof_out_path, index=False)
    print(f"  [OK] Processed Data Profile saved to {prof_out_path}")
    print("\nPipeline execution complete! All 10 datasets are fully standardized in data/processed/.")

if __name__ == "__main__":
    run_preprocessing()
