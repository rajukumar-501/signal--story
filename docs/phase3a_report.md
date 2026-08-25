# Phase 3A: Deterministic Cross-Source Analytical Engine

## 1. Executive Summary
This report details the implementation and baseline evaluation of Phase 3A: The Deterministic Cross-Source Analytical Engine for the Accenture Decision Intelligence Prototype. The primary objective was to build a rigorous, deterministic Python backend that independently identifies analytical events, generates hypotheses (candidate drivers), scores evidence across multiple data sources, and resolves contradictions—all strictly without the use of LLMs or access to ground-truth labels. 

The deterministic engine successfully identifies structural anomalies and evaluates candidates based on hard rules. However, this Phase 3A.1 baseline evaluation proves unequivocally that heuristic-based thresholding has severe limitations when analyzing complex business scenarios across diverse markets.

This document establishes the **Deterministic Baseline** and perfectly sets the stage for Phase 3B, where an LLM will be integrated as an orchestrator and reasoning engine over this deterministic layer.

## 2. Architecture & Data Flow
The architecture consists of a pipeline of modular components designed to process requests deterministically:
1. **Analytical Data Model (`data_model.py`)**: Centralized data loader that ensures single-source-of-truth loading of the canonical `Data/Processed/` datasets. It joins dimensional data and enforces strict schema compliance.
2. **KPI Engine (`kpi_engine.py`)**: Standardized calculation primitives (Gross Sales, Net Revenue, ROI, Margin, Return Rate, Category Share). It enforces business rules (e.g., `SUM(signed_sales_amount)` for True Net Revenue).
3. **Event Detector (`event_detector.py`)**: Computes month-over-month (MoM) and a 3-month rolling baseline (`mean(prev_1m, prev_2m, prev_3m)`) and flags statistical anomalies.
4. **Driver Catalog (`driver_catalog.py`)**: A registry defining 9 distinct driver families and their required evidence metrics.
5. **Candidate Generator (`driver_generator.py`)**: Applies deterministic thresholds across slices (market, category, channel) to hypothesize drivers.
6. **Evidence Scorer (`evidence_scorer.py`)**: Quantifies evidence strength based on magnitude (0-8 points), cross-source corroboration (3 points per additional distinct dataset), and evidence depth (1.5 points per item).
7. **Contradiction Engine (`contradiction_engine.py`)**: Detects logical fallacies (e.g., flagging Marketing Inefficiency when marketing spend is zero) and penalizes scores.
8. **Driver Ranker (`driver_ranker.py`)**: Ranks drivers, applies uncertainty thresholds (`STRONGLY_SUPPORTED` >= 7.5, `PLAUSIBLE` >= 5.0, `NOT_ESTABLISHED` < 5.0).
9. **Diagnosis Formatter (`diagnosis.py`)**: Packages the output into a structured JSON payload.

## 3. Strict Data Isolation
A critical requirement of Phase 3A.1 was the strict prohibition of accessing the ground truth folder or using true root causes in the request. The engine only reads from `Data/Processed/` and `Data/Raw/`. An automated test suite (`test_phase3a_engine.py`) verifies that:
- `sys.modules` contains no references to the `evaluation_ground_truth` module.
- `run_analysis()` never accepts `expected_driver` or `true_root_cause`.
- The `src/analytics/` production code contains no references to truth datasets, ensuring zero leakage.

## 4. Phase 3A.1 Baseline Accuracy Results
The engine was rigorously evaluated against the 8 official Phase 2B scenarios, producing the following baseline metrics:

> [!IMPORTANT]
> **Top-1 Accuracy:** 12.5% (1 / 8)
> **Top-3 Recall:** 75.0% (6 / 8)
> **Status Accuracy:** 50.0% (4 / 8)
> **S008 (Uncertainty test) Correct:** False

### 4.1 Scenario Breakdown

| Scenario | Market | Category / Product | True Root Cause | Detected Top Driver | Result | Analysis |
|----------|--------|-------------------|-----------------|---------------------|--------|----------|
| **S001** | South Korea | A6519160401 | `DRIVER_04_RETURNS` | `DRIVER_03_MARKETING` | **Failure.** The rules triggered on marketing shifts, missing the massive returns spike nuance. |
| **S002** | South Korea | - | `DRIVER_06_CUSTOMER` | `DRIVER_07_MARKET` | **Failure.** The channel shift was overshadowed by the broader market shift heuristics. |
| **S003** | China | A2520150501 | `DRIVER_03_MARKETING` | `DRIVER_03_MARKETING` | **Success!** Correctly identified marketing inefficiency as the primary driver. |
| **S004** | China | A0621150308 | `DRIVER_02_PRICING` | `DRIVER_07_MARKET` | **Failure.** Market shift heuristics overpowered the pricing anomaly. |
| **S005** | Indonesia | - | `DRIVER_05_SUPPORT` | `DRIVER_07_MARKET` | **Failure.** The unstructured root cause (Service Outage) was entirely missed. |
| **S006** | India | Processors | `DRIVER_08_PRODUCT_MIX` | `DRIVER_07_MARKET` | **Failure.** Market shift rules triggered instead of category-specific dynamics. |
| **S007** | Portugal | Wi fi extender | `DRIVER_08_PRODUCT_MIX` | `DRIVER_05_SUPPORT` | **Failure.** Misattributed to support metrics despite implementing `category_share`. |
| **S008** | Germany | - | `NOT_ESTABLISHED` | `DRIVER_07_MARKET` | **Failure.** The engine found a massive 90% drop in Germany in March 2020 and confidently attributed it to a `DRIVER_07_MARKET` anomaly, failing the uncertainty test. |

### 4.2 Key Limitations & Failure Modes
1. **Heuristic Brittleness**: Static percentage thresholds are extremely brittle. A massive structural drop (like Germany in March 2020) triggers multiple heuristic rules, causing the engine to confidently assert a false positive (Market Anomaly) rather than correctly admitting uncertainty.
2. **False Positives (Overshadowing)**: `DRIVER_07_MARKET` heuristics frequently overshadowed nuanced causes like Pricing (S004), Channel Shifts (S002), and Product Mix (S006). Deterministic scoring logic struggles to weigh conflicting metrics.
3. **Inability to Read Text**: S005 (Customer Service Outage) is clearly documented in unstructured CRM logs, but the deterministic engine only sees numerical counts, failing to grasp the "why."
4. **Baseline vs. MoM**: The event detector outputs both month-over-month and 3-month rolling baseline metrics. In volatile periods, fixed baselines fail to contextualize sudden macroeconomic shifts.

## 5. Conclusion and Recommendations for Phase 3B
Phase 3A.1 successfully established the deterministic boundaries, path consistencies, and numerical guardrails. The engine provides a mathematically sound, cross-source structured data payload without any data leakage.

However, the **12.5% Top-1 Accuracy** proves unequivocally that **Decision Intelligence cannot be fully automated with deterministic rules alone.** The rigid thresholds are too easily tricked by massive macroeconomic shocks and generic correlations.

**Phase 3B Recommendation**:
Integrate an LLM reasoning layer to consume the output of this deterministic engine. The LLM will:
- Process the unstructured text in CRM logs (resolving S005).
- Reason about the mathematical evidence presented by the deterministic engine to separate correlation from causation.
- Adapt dynamically to market scale and global events, replacing rigid thresholds with contextual understanding (resolving the S008 uncertainty failure).
- Act as the final synthesizer, bridging the gap between numerical anomalies and business reality.
