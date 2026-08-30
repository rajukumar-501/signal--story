# Phase 5.2A — Pre-Implementation Audit: Accenture KPI Semantic Contract

## 1. Executive Summary & Objective
This audit documents the existing state of KPI definitions, calculation logic, anomaly baselines, driver associations, lineage, and access restrictions in **Signal Story (Accenture Decision Intelligence Platform)**.
It establishes the blueprint for implementing a lightweight, machine-readable KPI Semantic Contract (`Data/semantic/kpi_contract.json`), a read-only API endpoint (`GET /api/kpi-contract`), and an enterprise governance presentation panel in the Signal Story frontend.

**Immutability Guarantee**:
The core analytical engines (`src/analytics/` and `src/phase3b/`), canonical datasets (`Data/Processed/`), and benchmark evaluations (`Data/scenarios/`) are **FROZEN** and will NOT be modified.

---

## 2. Codebase Inventory of Existing KPI & Analytical Metadata

| Metadata Dimension | Current Implementation in Repository | Source Code Location |
| :--- | :--- | :--- |
| **KPI Registry & Calculation** | Deterministic formulas for `gross_sales`, `signed_net_revenue`, `category_share`, `return_rate`, `marketing_spend`, `conversion_rate`, `ctr`, `price_gap`. | `src/analytics/kpi_engine.py` |
| **Baseline Method** | 3-month rolling average (`rolling_3m_baseline`) with prior-month comparative tracking (`mom_change_percent`). | `src/analytics/event_detector.py` (lines 72–88) |
| **Materiality & Anomaly Detection** | Percentage change relative to 3-month rolling baseline (`percentage_change`), magnitude computation, and status flags (`VALID`, `INSUFFICIENT_HISTORY`). | `src/analytics/event_detector.py` (lines 85–88, 135–136) |
| **Candidate Causal Drivers** | 9 structured driver families (`DRIVER_01_INVENTORY` through `DRIVER_09_UNEXPLAINED`) with expected metric directions, evidence conditions, and contradiction criteria. | `src/analytics/driver_catalog.py` (lines 7–80) |
| **Canonical Datasets & Grain** | 10 processed tables covering sales, inventory, marketing, competitive pricing, customer support, CRM notes, sales calls, and dimension tables. Monthly grains partitioned by Market, Product, Channel, Customer. | `src/analytics/data_model.py`<br>`Data/Processed/*.csv` |
| **Lineage & Data Flows** | Raw event ingestion $\rightarrow$ Cleaned canonical facts $\rightarrow$ `AnalyticalDataModel` $\rightarrow$ `KPIEngine` $\rightarrow$ `EventDetector` $\rightarrow$ `Phase3BReasoningEngine`. | Verified in codebase pipeline |
| **Scenario Metadata** | 8 benchmark scenarios (`S001`–`S008`) with assigned target KPIs (`gross_sales`, `category_share`), target dates, market/product scopes, and descriptions. | `src/server.py` (`OFFICIAL_SCENARIOS`) |
| **Security & Access Context** | Role-based categorization implicit in business domain (Executive, Finance, Commercial Strategy, QA/Support) and data sensitivity tiers. | Currently implicit; to be formalized |

---

## 3. Gap Analysis (What is Missing for Round 2 Compliance)

1. **Machine-Readable Semantic Contract File**:
   * Missing `Data/semantic/kpi_contract.json` specifying formal schema definitions, grain, units, formulas, candidate drivers, access roles, and lineage.
2. **Read-Only API Endpoint**:
   * Missing `GET /api/kpi-contract` exposing the formal semantic contract safely to downstream consumers and the UI.
3. **UI Governance Panel**:
   * The current UI displays signals, evidence, and integrity traces, but does not render the formal KPI governance definition (formula, grain, baseline rule, materiality threshold, access roles).
4. **Automated Test Coverage**:
   * Missing test suite validating contract schema, retrieval, multi-KPI queries, and immutability guarantees.

---

## 4. Planned Changes & File Map

### New Files to Create:
1. `Data/semantic/kpi_contract.json` — Machine-readable semantic contract catalog for all supported business KPIs.
2. `tests/test_phase5_2a_kpi_contract.py` — Automated test suite verifying contract integrity, API retrieval, schema completeness, and secret-safety.
3. `docs/phase5_2a_implementation_report.md` — Final Phase 5.2A implementation report.

### Existing Files to Modify:
1. `src/server.py` — Add `GET /api/kpi-contract` endpoint (with optional `?kpi_id=` filter) and link contract data into the scenario metadata.
2. `static/index.html` — Add a compact, clean "KPI Governance" metadata drawer/panel to the Signal Story header/view.
3. `static/styles.css` — Add styling for the KPI governance chip and details panel conforming to the enterprise SaaS design system.
4. `static/app.js` — Fetch KPI contract on scenario selection/load and render definition, calculation, grain, baseline method, materiality threshold, candidate drivers, and access roles.

### Frozen Files Protected (Zero Changes Permitted):
- `src/analytics/*` (All 13 analytical files frozen)
- `src/phase3b/*` (All reasoning and validator files frozen)
- `Data/Processed/*` (All 10 canonical datasets frozen)
- `Data/scenarios/*` (All ground truth and evaluation inputs frozen)

---

## 5. Verification & Safety Strategy
* All existing 157 unit and integration tests must continue to pass with 100% success.
* New tests will verify:
  * Contract JSON schema validity.
  * Correctness of formulas and driver mappings.
  * Safe handling of unknown/missing KPI IDs.
  * Total absence of secret exposure in API responses.
