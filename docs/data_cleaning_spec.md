# Data Cleaning & Anomaly Remediation Specification

**Project:** Accenture Decision Intelligence Platform  
**Pipeline Script:** `src/data/preprocess.py`  
**Output Directory:** `data/processed/`  
**Profile Location:** `data/validation/data_profile_processed.csv`

---

## 1. Overview & Strategy

To adhere to data engineering best practices and maintain data provenance:
- **`data/raw/` is treated as immutable master data** and left completely unchanged.
- **`src/data/preprocess.py` provides an automated, reproducible pipeline** that ingests raw master and synthetic prototype datasets, cleans encodings, aligns date dimensions, imputes missing geographic attributes, models return transactions, and outputs standardized datasets to `data/processed/`.

---

## 2. Remediation Rules & Transformations

### Remediation 1: Encoding Standardization to UTF-8
- **Issue:** Master dimensions (`dim_product.csv`, `dim_customer.csv`) contained Windows-1252/Latin-1 bytes (such as byte `0x96` for en-dashes `–`).
- **Transformation:**
  - Files are ingested with `cp1252` encoding.
  - Byte `\x96` and unicode en-dashes `–` are converted to standard UTF-8 hyphens `-`.
  - Leading/trailing whitespace is stripped across all string attributes.
  - Clean CSVs are saved with standard `utf-8` encoding.
- **Verification:** All 10 files in `data/processed/` load in Python without `UnicodeDecodeError`.

---

### Remediation 2: Date Formatting Synchronization
- **Issue:** `fact_sales_monthly.csv` formatted dates as `DD-MM-YYYY HH:MM` (e.g. `01-09-2018 00:00`), causing standard US parsers to corrupt dates.
- **Transformation:**
  - `fact_sales_monthly.csv` date strings are parsed explicitly with format `%d-%m-%Y %H:%M`.
  - Date strings are normalized to standard ISO 8601 `YYYY-MM-DD` (e.g. `2018-09-01`).
- **Verification:** All time-series tables (`fact_sales_monthly`, `fact_inventory_monthly`, `fact_marketing_monthly`, `fact_competitor_pricing_monthly`, `fact_support_tickets`, `fact_crm_notes`, `fact_sales_calls`) now share the identical 36-month timeline:
  - **Start Date:** `2018-09-01`
  - **End Date:** `2021-08-01`
  - **Total Months:** Exactly 36 unique monthly buckets.

---

### Remediation 3: Sales Returns & Financial Quantity/Revenue Modeling
- **Investigation & Finding:**
  - `net_sales_amount` in the raw data is the **positive transaction dollar value of that specific row**, *not* pre-netted revenue.
  - When `Qty > 0`, `net_sales_amount / Qty = unit_price`.
  - When `Qty < 0` (160,171 rows / 20.02%), `net_sales_amount / |Qty| = unit_price` (the positive refund/credit value of returned items).
  - A naive `SUM(net_sales_amount)` yields **$883.05M**, mistakenly adding returns to gross sales.
- **Transformation Applied:**
  - `is_return`: Boolean flag (`True` if `Qty < 0`, else `False`).
  - `gross_qty`: `max(Qty, 0)` (Gross shipment volume).
  - `return_qty`: `abs(min(Qty, 0))` (Return volume).
  - `gross_sales_amount`: `net_sales_amount` if `Qty > 0` else `0.0` (Total: **$706.46M**).
  - `return_sales_amount`: `net_sales_amount` if `Qty < 0` else `0.0` (Total: **$176.59M**, representing a 25.0% return rate).
  - `signed_sales_amount`: Signed dollar amount (`-net_sales_amount` if `Qty < 0`, else `+net_sales_amount`), enabling simple `SUM(signed_sales_amount)` to produce the **True Net Revenue: $529.87M**.
- **Verification:**
  - Identity `gross_qty - return_qty == Qty` holds 100%.
  - Identity `gross_sales_amount - return_sales_amount == signed_sales_amount` holds 100%.

---

### Remediation 4: Market Dimension Zone & Region Imputation
- **Issue:** In `dim_market.csv`, `Canada` and `USA` contained `nan` strings for `sub_zone` and `region`.
- **Transformation:**
  - `Canada` `sub_zone` and `region` imputed to `'NA'` (North America).
  - `USA` `sub_zone` and `region` imputed to `'NA'` (North America).
- **Verification:** 
  - 0 empty strings or null values across all 23 market entries.
  - Regional groupings now encompass `APAC`, `EU`, and `NA`.

---

## 3. Processed Datasets Schema Summary

| Table Name | Category | Rows | Columns | Key Columns |
| :--- | :--- | :--- | :--- | :--- |
| **`dim_product.csv`** | Master Dim | 298 | 6 | `product_code` (PK), `division`, `segment`, `category`, `product`, `variant` |
| **`dim_customer.csv`** | Master Dim | 189 | 5 | `customer_code` (PK), `customer`, `platform`, `channel`, `market` |
| **`dim_market.csv`** | Master Dim | 23 | 3 | `market` (PK), `sub_zone`, `region` |
| **`fact_sales_monthly.csv`** | Master Fact | 799,962 | 8 | `date`, `product_code`, `customer_code`, `Qty`, `net_sales_amount`, `is_return`, `gross_qty`, `return_qty` |
| **`fact_inventory_monthly.csv`** | Synthetic Fact | 246,744 | 8 | `date`, `product_code`, `market`, `opening_stock_units`, `received_units`, `closing_stock_units`, `stockout_flag`, `stockout_hours` |
| **`fact_marketing_monthly.csv`** | Synthetic Fact | 246,744 | 11 | `campaign_id` (PK), `date`, `product_code`, `market`, `campaign_type`, `channel`, `spend`, `impressions`, `clicks`, `conversions`, `discount_percent` |
| **`fact_competitor_pricing_monthly.csv`**| Synthetic Fact | 246,744 | 10 | `date`, `product_code`, `market`, `our_price`, `competitor_a_price`, `competitor_b_price`, `average_competitor_price`, `price_gap_percent`, `promotion_flag`, `discount_percent` |
| **`fact_support_tickets.csv`** | Synthetic Fact | 5,000 | 10 | `ticket_id` (PK), `date`, `customer_code`, `product_code`, `market`, `issue_category`, `sentiment`, `priority`, `ticket_text`, `resolution_time_hours` |
| **`fact_crm_notes.csv`** | Synthetic Fact | 3,500 | 9 | `note_id` (PK), `date`, `customer_code`, `product_code`, `market`, `sales_rep`, `note_text`, `deal_stage`, `competitor_mentioned` |
| **`fact_sales_calls.csv`** | Synthetic Fact | 3,000 | 9 | `call_id` (PK), `date`, `customer_code`, `product_code`, `market`, `sales_rep`, `duration_minutes`, `transcript`, `outcome` |

---

## 4. Referential Integrity Matrix

- **`product_code` Foreign Key:** 0 orphan records across all 7 referencing fact tables.
- **`customer_code` Foreign Key:** 0 orphan records across `fact_sales_monthly`, `fact_support_tickets`, `fact_crm_notes`, and `fact_sales_calls`.
- **`market` Foreign Key:** 0 orphan records across `dim_customer`, `dim_market`, and all operational fact tables.
- **Timeline Alignment:** 100% of fact tables span `2018-09-01` to `2021-08-01` (36 months).
