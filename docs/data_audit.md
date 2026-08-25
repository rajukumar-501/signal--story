# Data Audit Report: Master & Synthetic Datasets

**Project:** Accenture Decision Intelligence Platform  
**Audit Date:** August 2026  
**Scope:** 4 Raw Master Data Tables + 6 Synthetic Prototype Data Tables  
**Profile Location:** `data/validation/data_profile.csv`

---

## 1. Executive Summary

A comprehensive data audit was conducted across all 10 datasets in the project workspace (4 raw master tables and 6 synthetic prototype tables), totaling **1,552,449 records** across **92.2 MB** of source data. 

The master tables establish dimensional hierarchies (`dim_product`, `dim_customer`, `dim_market`) and historical transactional baseline (`fact_sales_monthly`), while the synthetic tables provide multi-signal operational contexts across inventory, marketing campaigns, competitor pricing, customer support tickets, CRM notes, and sales call logs.

| Category | Datasets | Total Records | Storage Size | Referential Integrity | Readiness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Raw Master Data** | 4 tables | 800,472 | 37.45 MB | 100% Valid (0 orphan keys) | **Ready** (encoding/date handling required) |
| **Synthetic Prototype Data** | 6 tables | 751,977 | 54.73 MB | 100% Valid (0 orphan keys) | **Ready** |
| **Total** | **10 tables** | **1,552,449** | **92.18 MB** | **100% Referential Integrity** | **Ready for Phase 2** |

---

## 2. Dataset Inventory & Technical Characteristics

| Dataset Name | Classification | Rows | Columns | Size (MB) | File Encoding | Grain / Primary Key | Date Range |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`dim_product.csv`** | Raw Master | 298 | 6 | 0.02 MB | `latin1` / `cp1252` | `product_code` | N/A (Static Dim) |
| **`dim_customer.csv`** | Raw Master | 189 | 5 | 0.01 MB | `latin1` / `cp1252` | `customer_code` | N/A (Static Dim) |
| **`dim_market.csv`** | Raw Master | 23 | 3 | < 0.01 MB | `utf-8` | `market` | N/A (Static Dim) |
| **`fact_sales_monthly.csv`** | Raw Master | 799,962 | 5 | 37.42 MB | `utf-8` | `[date, product_code, customer_code]` | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_inventory_monthly.csv`** | Synthetic | 246,744 | 8 | 10.65 MB | `utf-8` | `[date, product_code, market]` | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_marketing_monthly.csv`** | Synthetic | 246,744 | 11 | 22.35 MB | `utf-8` | `campaign_id` (or `[date, market, product_code]`) | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_competitor_pricing_monthly.csv`**| Synthetic | 246,744 | 10 | 15.66 MB | `utf-8` | `[date, product_code, market]` | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_support_tickets.csv`** | Synthetic | 5,000 | 10 | 0.73 MB | `utf-8` | `ticket_id` | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_crm_notes.csv`** | Synthetic | 3,500 | 9 | 0.46 MB | `utf-8` | `note_id` | `2018-09-01` to `2021-08-01` (36 mos) |
| **`fact_sales_calls.csv`** | Synthetic | 3,000 | 9 | 0.79 MB | `utf-8` | `call_id` | `2018-09-01` to `2021-08-01` (36 mos) |

---

## 3. Schema & Column Specifications

### Master Dimension Tables
1. **`dim_product` (298 rows, 6 cols)**
   - `product_code` (string, PK, 298 unique): Distinct SKU identifier.
   - `division` (string, 3 unique: `N & S`, `P & A`, `PC`): Product group division.
   - `segment` (string, 8 unique: `Peripherals`, `Accessories`, `Notebook`, `Desktop`, `Storage`, etc.).
   - `category` (string, 19 unique: `Internal Hard Drive`, `Graphic Card`, `Mouse`, `Keyboard`, etc.).
   - `product` (string, 33 unique): Brand/product model lines.
   - `variant` (string, 12 unique: `Standard`, `Plus`, `Premium`, etc.).

2. **`dim_customer` (189 rows, 5 cols)**
   - `customer_code` (int64, PK, 189 unique): Unique customer ID.
   - `customer` (string, 75 unique): Customer account name (e.g. `Amazon`, `Best Buy`, `Walmart`, `Costco`, `Flipkart`).
   - `platform` (string, 2 unique: `Brick & Mortar`, `E-Commerce`).
   - `channel` (string, 3 unique: `Retailer`, `Direct`, `Distributor`).
   - `market` (string, 23 unique, FK -> `dim_market.market`).

3. **`dim_market` (23 rows, 3 cols)**
   - `market` (string, PK, 23 unique): Geographic country market (e.g., `India`, `USA`, `Germany`, `China`, `United Kingdom`).
   - `sub_zone` (string, 7 unique: `India`, `NA`, `SE`, `NE`, `ANZ`, `EU`, `LATAM`).
   - `region` (string, 4 unique: `APAC`, `EU`, `NA`, `LATAM`).

---

### Fact Tables (Quantitative & Unstructured)
4. **`fact_sales_monthly` (799,962 rows, 5 cols)**
   - `date` (string/datetime): Monthly transaction date (format: `DD-MM-YYYY 00:00`, spanning 36 monthly snapshots).
   - `product_code` (string, FK -> `dim_product.product_code`, 260 distinct active SKUs).
   - `customer_code` (int64, FK -> `dim_customer.customer_code`, 189 distinct customers).
   - `Qty` (int64, min: -390, max: 24,198, mean: 128.51): Order quantity (negative values represent returns/adjustments).
   - `net_sales_amount` (float64, min: 1.06, max: 54,453.02, mean: 1,103.86): Realized net sales revenue in USD.

5. **`fact_inventory_monthly` (246,744 rows, 8 cols)**
   - Full grid: 298 products × 23 markets × 36 months = 246,744 rows.
   - Measures: `opening_stock_units`, `received_units`, `closing_stock_units`, `stockout_flag` (0/1), `stockout_hours`.

6. **`fact_marketing_monthly` (246,744 rows, 11 cols)**
   - Full grid: 298 products × 23 markets × 36 months = 246,744 rows.
   - Measures: `spend` ($500 - $8,832.68), `impressions` (17.5k - 702k), `clicks` (141 - 27.5k), `conversions` (2 - 1,733), `discount_percent` (0% - 25%), `campaign_type` (5 types), `channel` (5 channels).

7. **`fact_competitor_pricing_monthly` (246,744 rows, 10 cols)**
   - Full grid: 298 products × 23 markets × 36 months = 246,744 rows.
   - Measures: `our_price`, `competitor_a_price`, `competitor_b_price`, `average_competitor_price`, `price_gap_percent` (-5.3% to +10.3%), `promotion_flag` (0/1), `discount_percent` (0% - 20%).

8. **`fact_support_tickets` (5,000 rows, 10 cols)**
   - Grain: `ticket_id` (PK).
   - Attributes: `customer_code`, `product_code`, `market`, `issue_category` (`Delivery`, `Positive`, `Pricing`, `Product information`, `Quality`), `sentiment` (`negative`, `neutral`, `positive`), `priority` (`Low`, `Medium`, `High`), `ticket_text`, `resolution_time_hours` (0.1 - 34.6 hrs).

9. **`fact_crm_notes` (3,500 rows, 9 cols)**
   - Grain: `note_id` (PK).
   - Attributes: `customer_code`, `product_code`, `market`, `sales_rep` (30 reps), `note_text`, `deal_stage` (`Negotiation`, `Proposal`, `Prospecting`, `Qualified`, `Renewal`), `competitor_mentioned` (0/1 flag).

10. **`fact_sales_calls` (3,000 rows, 9 cols)**
    - Grain: `call_id` (PK).
    - Attributes: `customer_code`, `product_code`, `market`, `sales_rep`, `duration_minutes` (4 - 30 mins), `transcript` (conversational dialogue), `outcome` (`Follow-up required`, `Price negotiation`).

---

## 4. Entity Relationships & Join Compatibility Matrix

```
       [ dim_market ] (PK: market)
             │
             ├── (market) ──────────────┐
             │                          │
       [ dim_customer ] (PK: customer_code)
             │                          │
             ├── (customer_code) ───────┼──────────────────────────────┐
             │                          │                              │
       [ dim_product ] (PK: product_code)                              │
             │                          │                              │
             ├── (product_code) ────────┼───────────────┐              │
             │                          │               │              │
             ▼                          ▼               ▼              ▼
  [ fact_sales_monthly ]    [ fact_inventory ]    [ fact_mktg ]   [ Text Facts ]
  (date, prod, cust)        (date, prod, mkt)     (date, prod, mkt) (tickets/crm/calls)
```

### Join Validation Summary
- **`product_code` Integrity:** 100% match. 298 distinct products in `dim_product`. Every `product_code` in all 7 referencing fact tables exists in `dim_product` (0 orphans).
- **`customer_code` Integrity:** 100% match. 189 distinct customers in `dim_customer`. Every `customer_code` across `fact_sales_monthly`, `fact_support_tickets`, `fact_crm_notes`, and `fact_sales_calls` exists in `dim_customer` (0 orphans).
- **`market` Integrity:** 100% match. 23 distinct geographic markets across `dim_market`, `dim_customer`, and all synthetic fact tables (0 orphans).
- **Date Grain Alignment:** 100% aligned. All 7 time-series tables share the identical 36-month timeline (`2018-09-01` to `2021-08-01`).

---

## 5. Key Audit Findings & Anomalies

### 1. File Encoding Anomaly (Master Dimensions)
- **Finding:** `dim_product.csv` and `dim_customer.csv` contain non-UTF-8 characters (e.g. Windows-1252 byte `0x96` representing en-dashes `–` in product descriptions/variants).
- **Impact:** Attempting to read these files with default `utf-8` encoding throws `UnicodeDecodeError`.
- **Remediation:** Pipeline loaders must read raw master dimensions with `encoding='latin1'` or `encoding='cp1252'`.

### 2. Date String Format Discrepancy
- **Finding:** `fact_sales_monthly.csv` uses `DD-MM-YYYY 00:00` format (e.g., `01-09-2018 00:00`), whereas synthetic fact tables use `YYYY-MM-DD` (e.g., `2018-09-01`).
- **Impact:** Standard datetime parsers with US-default date format (`MM-DD-YYYY`) erroneously parse `01-09-2018` as January 9th instead of September 1st, collapsing 36 months into 4 bogus months.
- **Remediation:** Explicitly parse `fact_sales_monthly.csv` using format `%d-%m-%Y %H:%M` (or `dayfirst=True`).

### 3. Negative Order Quantities (`Qty` < 0) in Master Sales
- **Finding:** In `fact_sales_monthly.csv`, 160,171 rows (20.02%) have negative `Qty` values (min: -390), yet `net_sales_amount` remains strictly positive.
- **Context:** These reflect product returns, credit adjustments, or inventory reconciliations where net monetary values are booked positively.
- **Remediation:** Aggregation logic must differentiate between gross volume, return volume, and monetary revenue calculations.

### 4. Synthetic Datasets Design
- **Finding:** The three monthly synthetic tables (`inventory`, `marketing`, `competitor_pricing`) are full dense Cartesian products (298 products × 23 markets × 36 months = 246,744 records).
- **Context:** Provides zero-gap coverage across all cross-functional metrics to benchmark multimodal decision intelligence and root-cause analysis models.

---

## 6. Readiness Assessment & Next Steps

### Verdict: **READY FOR PHASE 2**

The datasets are structured, internally consistent, and possess 100% referential integrity across dimensional foreign keys and time grains. All anomalies have documented parsing solutions.

### Phase 2 Implementation Recommendations:
1. **ETL Ingestion Pipeline:** Implement a unified staging loader that handles `cp1252` encoding for master dimensions and applies explicit `%d-%m-%Y %H:%M` date parsing for `fact_sales_monthly`.
2. **Unified Semantic Layer:** Standardize star/snowflake schema with `dim_product`, `dim_customer`, and `dim_market` as central dimensions linked to the fact tables.
3. **Data Profiling Artifact:** Profile reference maintained at `data/validation/data_profile.csv`.
