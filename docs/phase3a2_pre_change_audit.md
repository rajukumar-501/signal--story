# Phase 3A.2: Pre-Change Analytical Correctness Audit

This audit outlines the issues identified in the Phase 3A engine and the technical corrections required to harden the engine's analytical correctness prior to entering Phase 3B.

---

## PROBLEM 1: Market Driver Semantics are Incorrect

*   **Current Behavior:**
    If global sales decline by more than 15%, the candidate generator triggers `DRIVER_07_MARKET` regardless of whether the target market behaved differently from other markets.
*   **Relevant Code Location:**
    [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_generator.py#L291-L320) (`_generate_market_candidate`)
*   **Why it is Analytically Incorrect:**
    A global or company-wide decline does not prove a market-specific or regional driver. A market driver must mean the target market behaves materially worse or differently from an appropriate comparison population (e.g. rest-of-company or peer markets).
*   **Proposed Correction:**
    Compare target market growth MoM against the rest-of-company (all other markets combined) growth MoM. Only generate `DRIVER_07_MARKET` as a candidate if:
    1. The target market has a meaningful decline (growth < -10%).
    2. The target market underperforms the rest of the company by a material margin (e.g. difference in growth < -10%).
*   **Expected Behavioral Change:**
    `DRIVER_07_MARKET` will no longer trigger for global declines where all markets dropped similarly (like S008 Germany), but will still trigger if a specific market underperforms (like market-specific declines).

---

## PROBLEM 2: Category Scope is Not Consistently Respected

*   **Current Behavior:**
    The engine filters on `market` and `product_code` but does not filter other datasets (e.g. inventory, support, marketing) by `category` or `channel` when those fields are specified in the request.
*   **Relevant Code Location:**
    [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_generator.py#L60-L68) (`_get_mask`)
*   **Why it is Analytically Incorrect:**
    For requests that specify a category (e.g. S006: India + Processors, S007: Portugal + Wi fi extender), analyzing all categories in that market leads to misattribution. If a query is category-specific, the entire pipeline must restrict its analysis to the scope of that category.
*   **Proposed Correction:**
    Implement a centralized, reusable `_apply_scope(df, request)` function that matches dimensions by joining datasets on-the-fly where columns are missing (e.g. joining `fact_inventory_monthly` with `dim_product` to get `category` and filter by it). Use this helper across all drivers, event detection, and analyzers.
*   **Expected Behavioral Change:**
    Analyzing `Portugal + Wi fi extender` will only look at inventory, pricing, support, and sales metrics *for* Wi fi extender products in Portugal, correcting the misattributions in S006 and S007.

---

## PROBLEM 3: Outcome Evidence and Driver Evidence are Mixed

*   **Current Behavior:**
    A large gross sales decline is processed as direct evidence for a driver (e.g. global sales drop is treated as positive evidence for a market driver).
*   **Relevant Code Location:**
    [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_generator.py#L10-L55) and [`evidence_scorer.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/evidence_scorer.py)
*   **Why it is Analytically Incorrect:**
    A decline in sales proves that the business outcome occurred (outcome evidence). It does not prove that a specific driver (e.g. inventory or marketing) caused it. Outcomes must never be treated as direct causal evidence, and a large KPI movement should not by itself create high causal confidence.
*   **Proposed Correction:**
    Every piece of evidence must be tagged with a role: `OUTCOME`, `SUPPORTING`, `CONTRADICTORY`, or `CONTEXT`. Driver scores must be computed strictly from `SUPPORTING` and `CONTRADICTORY` evidence, keeping `OUTCOME` magnitude purely contextual.
*   **Expected Behavioral Change:**
    A huge drop in sales will show up in the trace as `OUTCOME` evidence but will not contribute points to the driver score. Driver scores will only rise if driver-specific files (pricing, inventory, etc.) contain corresponding anomalies.

---

## PROBLEM 4: Weak Cross-Source Evidence Layer

*   **Current Behavior:**
    Most drivers only query one dataset (typically `fact_sales_monthly` or their primary dataset), and the evidence source count is 1 for almost all scenarios.
*   **Relevant Code Location:**
    [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_generator.py#L69-L367)
*   **Why it is Analytically Incorrect:**
    A single-source check does not represent true cross-source corroboration. Multiple independent datasets must be queried and checked to confirm a hypothesis.
*   **Proposed Correction:**
    Retrieve and evaluate all required datasets defined in the `DriverCatalog`. For example, for the support driver, retrieve support tickets, CRM notes, and sales calls. Ensure that multiple rows from the same dataset are counted as 1 source, not multiple sources.
*   **Expected Behavioral Change:**
    Causal drivers will have detailed evidence items from multiple distinct source datasets, and the corroboration score will reflect the count of unique source datasets.

---

## PROBLEM 5: S008 Uncertainty Behavior is Incorrect

*   **Current Behavior:**
    Germany on 2020-03-01 sees a massive sales decline. Lacking specific driver evidence, the engine defaults to flagging `DRIVER_07_MARKET` as `STRONGLY_SUPPORTED`.
*   **Relevant Code Location:**
    [`driver_generator.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_generator.py#L291-L320) and [`driver_ranker.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/driver_ranker.py)
*   **Why it is Analytically Incorrect:**
    A massive drop in sales with no supporting driver-specific evidence is an unexplained anomaly, not a strongly supported market driver. The correct classification is `NOT_ESTABLISHED`.
*   **Proposed Correction:**
    Enforce a rule that if a candidate has no driver-specific supporting evidence (or if supporting evidence is weak/missing), the candidate must be scored as `0.0` and the overall status must be `NOT_ESTABLISHED`.
*   **Expected Behavioral Change:**
    S008 will return `NOT_ESTABLISHED` as the overall status, emerging naturally from general rules rather than scenario-specific hardcoding.

---

## PROBLEM 6: Contradiction Evidence Flow is Disconnected

*   **Current Behavior:**
    Contradictions are detected in `ContradictionEngine` and apply a flat subtraction penalty, but they do not dynamically flow into the final status of a candidate in a structured way (e.g., as explicit `CONTRADICTORY` evidence objects).
*   **Relevant Code Location:**
    [`contradiction_engine.py`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/src/analytics/contradiction_engine.py)
*   **Why it is Analytically Incorrect:**
    Contradictions should be treated as negative evidence in the trace and should have a strong, deterministic impact on confidence status.
*   **Proposed Correction:**
    Integrate contradiction detection as part of the evidence generation. Generate explicit evidence items with role `CONTRADICTORY`. If any `CONTRADICTORY` evidence is present, or if it dominates, apply a severe penalty to the score, and capping the driver status to `NOT_ESTABLISHED` or `WEAK`.
*   **Expected Behavioral Change:**
    Drivers with contradictory indicators (e.g. inventory decline hypothesis when stockout is 0) will have their confidence score reduced to 0 and status set to `NOT_ESTABLISHED`.

---

## PROBLEM 7: Phase 3A Report is Stale

*   **Current Behavior:**
    The existing report states that S008 returns `NOT_ESTABLISHED`, which contradicts the actual baseline results (where S008 returned `DRIVER_07_MARKET`).
*   **Relevant Code Location:**
    [`docs/phase3a_report.md`](file:///c:/Users/rajuk/OneDrive/Desktop%281%29/Accenture_Decision_Intelligence/docs/phase3a_report.md)
*   **Why it is Analytically Incorrect:**
    Documentation must reflect the true state of the code and execution results, never stating incorrect claims.
*   **Proposed Correction:**
    Regenerate/update the report with the correct baseline numbers and create a new report for Phase 3A.2.
*   **Expected Behavioral Change:**
    Documentation will match the actual output files and tests.
