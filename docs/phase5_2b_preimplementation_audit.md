# Phase 5.2B — Pre-Implementation Audit: Data Quality, Freshness & Trust Control Layer

## 1. Executive Summary
This audit inspects the data foundation, schemas, temporal boundaries, quality indicators, and UI trust mechanisms of **Signal Story (Accenture Decision Intelligence Platform)**.
It establishes the technical specification for implementing a lightweight, deterministic **Data Quality, Freshness & Trust Control Layer** without altering the frozen analytical core (`src/analytics/`, `src/phase3b/`, `Data/Processed/`).

---

## 2. Comprehensive Codebase & Dataset Audit (Items A–L)

### A. Existing Data Sources
The canonical repository data warehouse contains **10 processed CSV datasets** in `Data/Processed/`:
* **Dimension Tables (3)**: `dim_customer.csv`, `dim_market.csv`, `dim_product.csv`.
* **Quantitative Fact Tables (4)**: `fact_sales_monthly.csv`, `fact_inventory_monthly.csv`, `fact_marketing_monthly.csv`, `fact_competitor_pricing_monthly.csv`.
* **Qualitative / Support Fact Tables (3)**: `fact_support_tickets.csv`, `fact_crm_notes.csv`, `fact_sales_calls.csv`.

### B. Dataset Schemas & Record Counts
| Dataset Name | Record Count | Primary / Natural Key | Required Columns |
| :--- | :--- | :--- | :--- |
| `dim_customer.csv` | 189 | `customer_code` | `customer_code`, `customer`, `market`, `platform`, `channel` |
| `dim_market.csv` | 23 | `market` | `market`, `sub_zone`, `region` |
| `dim_product.csv` | 298 | `product_code` | `product_code`, `division`, `segment`, `category`, `product`, `variant` |
| `fact_sales_monthly.csv` | 799,962 | `['date', 'product_code', 'customer_code']` | `date`, `product_code`, `customer_code`, `Qty`, `signed_sales_amount`, `gross_sales_amount`, `return_sales_amount` |
| `fact_inventory_monthly.csv` | 246,744 | `['date', 'product_code', 'market']` | `date`, `product_code`, `market`, `opening_stock_units`, `closing_stock_units`, `stockout_flag`, `stockout_hours` |
| `fact_marketing_monthly.csv` | 246,744 | `campaign_id` | `campaign_id`, `date`, `product_code`, `market`, `spend`, `impressions`, `clicks`, `conversions` |
| `fact_competitor_pricing_monthly.csv`| 246,744 | `['date', 'product_code', 'market']` | `date`, `product_code`, `market`, `our_price`, `average_competitor_price`, `price_gap_percent` |
| `fact_support_tickets.csv` | 5,000 | `ticket_id` | `ticket_id`, `date`, `customer_code`, `product_code`, `market`, `sentiment`, `issue_category` |
| `fact_crm_notes.csv` | 3,500 | `note_id` | `note_id`, `date`, `customer_code`, `product_code`, `market`, `note_text` |
| `fact_sales_calls.csv` | 3,000 | `call_id` | `call_id`, `date`, `customer_code`, `product_code`, `market`, `transcript` |

### C. Available Date Fields & Temporal Horizon
* All 7 fact tables include a canonical ISO-8601 `'date'` field (`YYYY-MM-01`).
* **Temporal Horizon**: `2018-09-01` to `2021-08-01` (36 consecutive monthly accounting periods).
* **Coverage Quality**: 100% continuous monthly intervals across all fact tables.

### D. Available Grain Information
* Sales, Inventory, Pricing, Marketing: **Monthly aggregation** at entity scopes (Market, Product, Customer, Channel).
* Support, CRM, Sales Calls: **Individual interaction event records** timestamped to monthly accounting partitions.

### E. Null / Missing-Value Handling Already Present
* `dim_market.csv`: 2 records contain null `sub_zone` / `region` (international non-standard territories).
* Fact tables: 0 null values in mandatory financial, volume, inventory, and marketing numerical telemetry.

### F. Existing Duplicate Handling
* Fact tables enforce unique natural keys per accounting period and entity scope. Zero duplicate primary key rows.

### G. Existing Dataset Metadata
* Described in Phase 1 ETL documentation (`data_profile_processed.csv`) and `AnalyticalDataModel` (`src/analytics/data_model.py`).

### H. Existing Lineage Information
* Documented in `kpi_contract.json` and tracked in Phase 3B traceability packets (`p3b.traceability` mapping `evidence_id` $\rightarrow$ `source_dataset` $\rightarrow$ `record_id`).

### I. Existing KPI Contract Information
* Phase 5.2A created `Data/semantic/kpi_contract.json` specifying 15 governance dimensions across all supported KPIs.

### J. Existing API Structure
* `GET /api/health` — Platform status.
* `GET /api/scenarios` — Scenario catalog.
* `GET /api/kpi-contract` — Semantic contract catalog.
* `POST /api/analyze` — Executes analytical pipeline.

### K. Existing UI Trust Mechanisms
* View 3 currently renders Grounding Integrity (100%), Safety Validation (10/10 PASS), Fallback Protection, and Warehouse Lineage Table.

### L. Exact Remaining Governance Gap
1. **Lack of Automated Data Quality Verification**: No module currently validates schema integrity, null rates, and key uniqueness on-demand.
2. **Lack of Temporal Freshness & Coverage Model**: No explicit check comparing the requested scenario period (e.g. `2021-04-01`) against dataset max coverage dates (`2021-08-01`).
3. **No Dedicated Read-Only Endpoint**: Missing `GET /api/data-trust`.
4. **Header Trust Indicator**: The UI does not display an immediate, compact Data Trust status (e.g., `Data Trust: Trusted 99.8%`).
5. **View 1 & View 3 Governance Integration**: View 1 lacks a compact data quality summary and View 3 lacks an expandable data quality check breakdown.

---

## 3. Planned Implementation Map (Phase 5.2B)

### New Files to Create:
1. `Data/semantic/data_trust_contract.json` — Machine-readable dataset quality specifications.
2. `src/governance/data_quality.py` — Deterministic data quality, freshness, and coverage evaluation engine.
3. `tests/test_phase5_2b_data_quality.py` — Test suite with negative fixtures (missing columns, nulls, duplicates, invalid dates).
4. `docs/phase5_2b_implementation_report.md` — Final implementation report.

### Files to Modify:
1. `src/server.py` — Add `GET /api/data-trust` endpoint and inject `data_trust` into `POST /api/analyze`.
2. `static/index.html` — Add header Data Trust badge, View 1 Data Quality & Coverage card, and View 3 Data Trust audit panel.
3. `static/styles.css` — Enterprise styling for trust badges and audit cards.
4. `static/app.js` — Bind Data Trust rendering and modal/drawer inspection.
5. `PROJECT_PROGRESS.md` — Update milestone log.

### Immutability Guarantee:
`src/analytics/`, `src/phase3b/`, `Data/Processed/`, and `Data/scenarios/` remain **100% FROZEN & UNMODIFIED**.
