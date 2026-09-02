# Phase 5.5 Pre-Implementation Audit: Canonical Datasets, KPI Mapping, and Alignment Integrity

**Organization:** Accenture Decision Intelligence Platform / Signal Story  
**Date:** 2026-08-31  
**Status:** Pre-Implementation Verification Complete  
**Scope:** Strict Audit of 10 Canonical Datasets, Source Grains, Cadence Metadata, and Genuine KPI Linkages  

---

## 1. Executive Summary & Audit Mandate

This pre-implementation audit rigorously inspects all 10 canonical datasets within `Data/Processed/` to establish the ground-truth technical foundation for:
1. **The Connected KPI Evidence Layer**: Selecting 3–5 genuine, mathematically and dimensionally aligned KPIs across 2–3 distinct source systems and grains.
2. **Context-Aware Feedback Learning**: Establishing the exact dimensional scope (Market, Product, Category, Driver) to bound analyst feedback learning without polluting unrelated scenarios.

### Core Architectural Guardrails Enforced
- **Zero Modifications to Frozen Analytical Core:** `src/analytics/**`, `src/phase3b/**`, `Data/Processed/**`, and `Data/scenarios/**` remain strictly untouched.
- **Zero Fabricated Relationships:** No artificial causation, invented tables, synthetic cadences, or unbacked linkages are permitted.
- **Clear Epistemic Distinction:** Explicit separation between deterministic mathematical alignment, corroborating telemetry, and qualitative contextual evidence.

---

## 2. Canonical 10-Dataset Audit Table

The following matrix documents the verified schema, record counts, temporal boundaries, grain, refresh cadence, and genuine KPI fields across all 10 canonical tables.

| Dataset Name | Source System / Origin | Verified Row Count | Primary Key / Grain | Date/Period Field & Range | Refresh Cadence | Actual KPI / Telemetry Fields | Alignment Keys to Canonical Domain |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`fact_sales_monthly.csv`** | ERP Sales Invoicing Ledger | 799,962 | `(date, product_code, customer_code)` | `date`: 2018-09-01 to 2021-08-01 (36 monthly periods) | Monthly Batch ETL (T+1 post-month close) | `gross_sales_amount`, `gross_qty`, `return_sales_amount`, `return_qty`, `signed_sales_amount`, `net_sales_amount` | `customer_code` (joins `dim_customer` for `market`, `channel`, `platform`), `product_code` (joins `dim_product`) |
| **`fact_marketing_monthly.csv`** | Digital Ad Platforms (Google, Meta, Retail Media) | 246,744 | `(date, product_code, market, campaign_type, channel)` | `date`: 2018-09-01 to 2021-08-01 (36 monthly periods) | Monthly Ad Telemetry Ingestion | `spend`, `impressions`, `clicks`, `conversions`, `discount_percent` | Direct: `date`, `market`, `product_code`, `channel` |
| **`fact_competitor_pricing_monthly.csv`** | Competitor Intelligence Feed | 246,744 | `(date, product_code, market)` | `date`: 2018-09-01 to 2021-08-01 (36 monthly periods) | Monthly Web Scrape / Syndicate Feed | `our_price`, `average_competitor_price`, `competitor_a_price`, `competitor_b_price`, `price_gap_percent`, `promotion_flag` | Direct: `date`, `market`, `product_code` |
| **`fact_inventory_monthly.csv`** | Warehouse Management System (WMS) | 246,744 | `(date, product_code, market)` | `date`: 2018-09-01 to 2021-08-01 (36 monthly periods) | Monthly WMS Snapshot | `opening_stock_units`, `received_units`, `closing_stock_units`, `stockout_flag`, `stockout_hours` | Direct: `date`, `market`, `product_code` |
| **`fact_crm_notes.csv`** | Enterprise CRM Sales Logs | 3,500 | `note_id` (Event grain) | `date`: 2018-09-01 to 2021-08-01 | Transactional / Ad-hoc sales logging | `note_text`, `deal_stage`, `competitor_mentioned`, `sales_rep` | Direct: `date`, `market`, `product_code`, `customer_code` |
| **`fact_sales_calls.csv`** | Telephony Call Transcripts | 3,000 | `call_id` (Event grain) | `date`: 2018-09-01 to 2021-08-01 | Transactional / Call Log Ingestion | `transcript`, `duration_minutes`, `outcome`, `sales_rep` | Direct: `date`, `market`, `product_code`, `customer_code` |
| **`fact_support_tickets.csv`** | Customer Helpdesk System | 5,000 | `ticket_id` (Event grain) | `date`: 2018-09-01 to 2021-08-01 | Transactional / Ticket Closure ETL | `issue_category`, `sentiment`, `priority`, `ticket_text`, `resolution_time_hours` | Direct: `date`, `market`, `product_code`, `customer_code` |
| **`dim_product.csv`** | Product Master Catalog | 298 | `product_code` (Entity grain) | N/A (Static dimension) | Master Data Sync | `division`, `segment`, `category`, `product`, `variant` | `product_code` |
| **`dim_customer.csv`** | Customer Master Directory | 189 | `customer_code` (Entity grain) | N/A (Static dimension) | Master Data Sync | `customer`, `market`, `platform`, `channel` | `customer_code` |
| **`dim_market.csv`** | Geographic Hierarchy Master | 23 | `market` (Entity grain) | N/A (Static dimension) | Master Data Sync | `market`, `sub_zone`, `region` | `market` |

---

## 3. Deep-Dive Audit: Scenario S003 (China, A2520150501, 2021-04)

### Target Entity Context
- **Scenario ID:** `S003`
- **Market:** `China`
- **Product Code:** `A2520150501` (`AQ Maxima Ms`, Segment: `Accessories`, Category: `Mouse`, Division: `P & A`)
- **Period of Anomaly:** `2021-04-01`
- **Baseline Period:** `2021-01-01` to `2021-03-01` (3-Month Rolling Unweighted Arithmetic Mean)
- **True Ground Truth Root Cause:** `Marketing Inefficiency`

### Actual S003 Historical Telemetry Across Datasets

#### A. ERP Sales Ledger (`fact_sales_monthly.csv` + `dim_customer.csv`)
| Period | Gross Sales ($) | Gross Qty (Units) | Return Sales ($) | Return Qty (Units) | Signed Net Revenue ($) | Active Customers |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2021-01** | $590.11 | 96 | $10,036.88 | 1,494 | -$9,446.77 | 2 (Neptune, Amazon) |
| **2021-02** | $3,074.39 | 468 | $0.00 | 0 | $3,074.39 | 2 (Neptune, Amazon) |
| **2021-03** | $7,009.60 | 1,047 | $0.00 | 0 | $7,009.60 | 3 (Neptune, Amazon, Leader) |
| **3-Mo Baseline** | **$3,558.03** | **537.0** | **$3,345.63** | **498.0** | **$212.41** | **2.3** |
| **2021-04 (Event)**| **$994.25** | **142** | **$8,094.00** | **1,211** | **-$7,099.75** | **2 (Neptune, Leader)** |
| **Variance vs Base**| **-72.06%** | **-73.56%** | +141.93% | +143.17% | -3,442.48% | -13.04% |

#### B. Digital Ad Telemetry (`fact_marketing_monthly.csv`)
| Period | Marketing Spend ($) | Impressions | Clicks | Conversions | CTR (%) | CVR (%) | CPC ($) | Discount % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **2021-01** | $1,691.02 | 113,585 | 4,791 | 348 | 4.22% | 7.26% | $0.35 | 9.2% |
| **2021-02** | $587.96 | 27,185 | 882 | 49 | 3.24% | 5.56% | $0.67 | 10.4% |
| **2021-03** | $705.85 | 25,706 | 698 | 55 | 2.72% | 7.88% | $1.01 | 12.0% |
| **3-Mo Baseline** | **$994.94** | **55,492** | **2,124** | **151** | **3.83%** | **7.09%** | **$0.47** | **10.5%** |
| **2021-04 (Event)**| **$1,641.07** | **89,414** | **853** | **31** | **0.95%** | **3.63%** | **$1.92** | **11.6%** |
| **Variance vs Base**| **+64.94%** | **+61.13%** | **-59.83%** | **-79.43%** | **-75.07%** | **-48.78%** | **+310.64%** | +1.1 pp |

#### C. Competitor Pricing Telemetry (`fact_competitor_pricing_monthly.csv`)
| Period | Our Price ($) | Avg Competitor Price ($) | Price Gap % | Promotion Flag | Discount % |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2021-01** | $6.15 | $6.20 | -0.81% | 0 | 0.0% |
| **2021-02** | $6.01 | $6.02 | -0.17% | 0 | 0.0% |
| **2021-03** | $5.85 | $5.85 | 0.00% | 0 | 0.0% |
| **3-Mo Baseline** | **$6.00** | **$6.02** | **-0.33%** | **0** | **0.0%** |
| **2021-04 (Event)**| **$5.98** | **$5.98** | **0.00%** | **0** | **0.0%** |
| **Variance vs Base**| -0.33% | -0.66% | +0.33 pp | 0 | 0.0 pp |

*Finding:* Pricing gap was flat at 0.00% in 2021-04. Pricing pressure is non-causal for S003.

#### D. Warehouse Inventory Telemetry (`fact_inventory_monthly.csv`)
| Period | Opening Stock (Units) | Received (Units) | Closing Stock (Units) | Stockout Flag | Stockout Hours |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2021-01** | 25 | 18 | 43 | 0 | 0 |
| **2021-02** | 534 | 400 | 934 | 0 | 0 |
| **2021-03** | 1,626 | 1,220 | 2,846 | 0 | 0 |
| **3-Mo Baseline** | **728** | **546** | **1,274** | **0** | **0** |
| **2021-04 (Event)**| **21** | **16** | **37** | **0** | **0** |
| **Variance vs Base**| -97.12% | -97.07% | -97.09% | 0 | 0 |

*Finding:* Stockout flag and hours remained strictly at 0. Physical inventory stock remained positive throughout the month.

#### E. Qualitative Intelligence (`fact_crm_notes.csv`, `fact_sales_calls.csv`, `fact_support_tickets.csv`)
- **China Market Records (2021-04):** 7 CRM notes, 4 sales calls, 4 support tickets.
- **Product `A2520150501` Specific Records:** 0 defect tickets, 0 customer service delivery escalations.
- **Contextual Interpretation:** Qualitative logs confirm absence of widespread product dissatisfaction or operational delivery failures on this product in China during 2021-04.

---

## 4. Selection & Mapping of 5 Connected KPIs for S003

Based on real data, the following 5 KPIs form the genuine Connected KPI story:

| KPI Key | KPI Display Name | Evidence Role | Source Table | Source Grain | Refresh Cadence | Baseline (Jan-Mar) | Event Value (2021-04) | Delta / Change | Alignment Dimension Keys |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`gross_sales`** | Gross Sales | **Outcome KPI** | `fact_sales_monthly.csv` | Monthly by Market, Customer, Product | Monthly Batch ETL | $3,558.03 | $994.25 | **-72.06%** (-$2,563.78) | `date`, `market`, `product_code` |
| **`order_volume`** | Gross Order Volume (Units) | **Corroborating KPI** | `fact_sales_monthly.csv` | Monthly by Market, Customer, Product | Monthly Batch ETL | 537.0 units | 142.0 units | **-73.56%** (-395.0 units) | `date`, `market`, `product_code` |
| **`marketing_spend`** | Marketing Investment | **Driver Signal** | `fact_marketing_monthly.csv` | Monthly by Market, Product, Campaign, Channel | Monthly Ad Telemetry | $994.94 | $1,641.07 | **+64.94%** (+$646.13) | `date`, `market`, `product_code` |
| **`conversion_rate`** | Marketing Conversion Rate | **Driver Signal** | `fact_marketing_monthly.csv` | Monthly by Market, Product, Campaign, Channel | Monthly Ad Telemetry | 7.09% | 3.63% | **-48.78%** (-3.46 pp) | `date`, `market`, `product_code` |
| **`click_through_rate`** | Click-Through Rate (CTR) | **Corroborating Signal** | `fact_marketing_monthly.csv` | Monthly by Market, Product, Campaign, Channel | Monthly Ad Telemetry | 3.83% | 0.95% | **-75.07%** (-2.87 pp) | `date`, `market`, `product_code` |

---

## 5. Epistemic Classification: Deterministic vs. Contextual Relationships

### A. Deterministic Mathematical Relationships (Supported by Data)
1. **Sales & Volume Co-Movement:** Gross Sales ($994.25) and Order Volume (142 units) are arithmetically linked within the sales ledger (`fact_sales_monthly.csv`). The unit volume drop (-73.56%) directly aligns with the gross revenue contraction (-72.06%).
2. **Marketing Telemetry Co-Movement:** Marketing spend increased by +64.94% while conversion rate collapsed from 7.09% to 3.63% (-48.78%) and CTR collapsed from 3.83% to 0.95% (-75.07%). Cost per click escalated by +310.64% ($0.47 to $1.92). All metrics are mathematically derived from `fact_marketing_monthly.csv`.
3. **Cross-Source Dimensional Alignment:** The alignment between the sales ledger and the marketing telemetry is deterministically joined on `(date='2021-04-01', market='China', product_code='A2520150501')`.

### B. Contextual Relationships (Corroborating, Non-Deterministic)
1. **Absence of Customer Support / Delivery Quality Escalations:** The lack of defect tickets or CRM complaints for product `A2520150501` in China during 2021-04 contextually eliminates customer service failure as the primary driver.
2. **Price Parity Context:** Price gap remaining at 0.00% contextually corroborates that competitor pricing was not the catalyst.

---

## 6. Unsupported Relationships & Guardrails (MUST NOT Be Presented)

The following claims and representations are strictly prohibited in the system:

1. **NO Direct Causal Claims:** Do not use phrasing like *"Ad spend caused sales to drop"* or *"Root cause is proven by conversion rate"*.  
   *Approved Phrasing:* *"Evidence indicates aligned contraction in conversion efficiency while ad spend escalated; corroborating signals support marketing inefficiency."*
2. **NO Synthetic High-Frequency Grains:** Do not claim daily or hourly marketing telemetry. All canonical tables in this prototype are monthly.
3. **NO Unbacked Support Ticket Causal Links:** Do not link support ticket complaints from other products (e.g. `A4821110802`) to this scenario's root cause.
4. **NO Invented Telemetry Fields:** Metrics like "Website Bounce Rate" or "Customer NPS" do not exist in the canonical tables and must never be displayed as real telemetry.

---

## 7. Audit Sign-Off & Implementation Prerequisites

- [x] All 10 canonical datasets inspected and row counts/schemas verified.
- [x] Actual KPI fields and calculations verified against real data.
- [x] Scenario S003 historical figures audited and baseline deltas calculated.
- [x] Dimensional alignment keys verified (`date`, `market`, `product_code`).
- [x] Unsupported relationships and prohibited causal claims explicitly cataloged.

**Audit Status:** APPROVED FOR IMPLEMENTATION (Proceeding to Parts B–L upon user review).
