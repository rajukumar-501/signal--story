# Phase 3A Data Contract

**Project:** Accenture Decision Intelligence Prototype  
**Phase:** 3A (Deterministic Cross-Source Analytical Engine)

This document formalizes the canonical data inputs that the Phase 3A analytical engine will consume. The engine operates *only* on processed datasets and never accesses the ground-truth evaluation files.

## 1. Timeline & Baselines
The analytical engine expects all time-series (fact) tables to share a synchronized 36-month timeline:
- **Start Date:** `2018-09-01`
- **End Date:** `2021-08-01`
- **Grain:** Monthly (`YYYY-MM-DD` where DD is always 01).

**Rolling Baseline Formula:**
All anomaly detection compares the current month's value to a 3-month rolling baseline defined exactly as:
`mean(previous_month, two_months_prior, three_months_prior)`

## 2. Master Dimensions

### 2.1. `dim_product.csv`
- **Primary Key:** `product_code`
- **Attributes:** `division`, `segment`, `category`, `product`, `variant`

### 2.2. `dim_customer.csv`
- **Primary Key:** `customer_code`
- **Attributes:** `customer`, `platform`, `channel`, `market`

### 2.3. `dim_market.csv`
- **Primary Key:** `market`
- **Attributes:** `sub_zone`, `region`

## 3. Fact Tables (Analytical Inputs)

### 3.1. `fact_sales_monthly.csv`
- **Primary Keys:** `date`, `product_code`, `customer_code`
- **Important Columns:** 
  - `Qty` (Net units)
  - `net_sales_amount` (Absolute positive transaction value)
  - `is_return` (Boolean)
  - `gross_qty` (Positive shipments)
  - `return_qty` (Positive returns)
  - `signed_sales_amount` (Correctly signed financial value, used for True Net Revenue)
  - `gross_sales_amount`, `return_sales_amount`
- **KPI Rule:** True Net Revenue = `SUM(signed_sales_amount)`. NEVER `SUM(net_sales_amount)`.

### 3.2. `fact_inventory_monthly.csv`
- **Primary Keys:** `date`, `product_code`, `market`
- **Important Columns:** `opening_stock_units`, `received_units`, `closing_stock_units`, `stockout_flag`, `stockout_hours`

### 3.3. `fact_marketing_monthly.csv`
- **Primary Keys:** `campaign_id` (also joinable on `date`, `product_code`, `market`)
- **Important Columns:** `campaign_type`, `channel`, `spend`, `impressions`, `clicks`, `conversions`, `discount_percent`

### 3.4. `fact_competitor_pricing_monthly.csv`
- **Primary Keys:** `date`, `product_code`, `market`
- **Important Columns:** `our_price`, `competitor_a_price`, `competitor_b_price`, `average_competitor_price`, `price_gap_percent`, `promotion_flag`, `discount_percent`

### 3.5. `fact_support_tickets.csv`
- **Primary Keys:** `ticket_id` (also joinable on `date`, `customer_code`, `product_code`, `market`)
- **Important Columns:** `issue_category`, `sentiment`, `priority`, `ticket_text`, `resolution_time_hours`

### 3.6. `fact_crm_notes.csv`
- **Primary Keys:** `note_id` (also joinable on `date`, `customer_code`, `product_code`, `market`)
- **Important Columns:** `sales_rep`, `note_text`, `deal_stage`, `competitor_mentioned`

### 3.7. `fact_sales_calls.csv`
- **Primary Keys:** `call_id` (also joinable on `date`, `customer_code`, `product_code`, `market`)
- **Important Columns:** `sales_rep`, `duration_minutes`, `transcript`, `outcome`

## 4. Approved Joins
1. `fact_sales_monthly` → `dim_product` (on `product_code`)
2. `fact_sales_monthly` → `dim_customer` (on `customer_code`)
3. `dim_customer` → `dim_market` (on `market`)
4. Aggregated `fact_sales` (by market/product/date) → `fact_inventory`, `fact_marketing`, `fact_competitor_pricing` (on `market`, `product_code`, `date`)

## 5. Limitations
- Unstructured evidence (tickets, CRM notes, transcripts) is sparse. If a driver depends on unstructured evidence but none exists for that entity/date, the engine will return `NOT_AVAILABLE` instead of fabricating it.
