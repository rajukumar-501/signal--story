# Phase 2B: Scenario Ground Truth Report

## Overview
We have successfully processed the 8 shortlisted scenarios by independently verifying their metrics against the canonical datasets located in `data/processed/`.

## Deliverables Generated
1. **Verification Summary**: `data/scenarios/scenario_verification.csv` (tabular metrics verifying drops and anomalies)
2. **Ground Truth Key**: `data/scenarios/ground_truth.csv`
3. **Scenario Summary**: `data/scenarios/scenario_summary.csv`
4. **Evidence Packets**: `data/scenarios/S001_evidence.csv` through `S008_evidence.csv` (contains raw sales facts spanning current and previous period)
5. **AI Test Specs**: `tests/scenario_ground_truth.json` (no root-cause hints)
6. **Code**: `src/analytics/scenario_ground_truth.py`

## Verified Insights
The independent verification successfully matched the candidate metrics:
- **S001 (Returns Spike - SK):** Returns account for $22.5k against gross sales of $648, resulting in a net revenue negative impact.
- **S002 (Channel Shift - SK):** Brick & Mortar saw a catastrophic drop of ~68.5% in gross sales.
- **S003 (Marketing Inefficiency - China):** Gross sales collapsed ~85.8% for the target product despite marketing spend.
- **S004 (Competitive Pricing - China):** Product sales fell ~98.2%.
- **S005 (Support Deterioration - Indonesia):** Market sales collapsed ~87.5% across the board.
- **S006 (Category Demand Collapse - India):** Processors category dropped ~88.0%.
- **S007 (Product-mix Shift - Portugal):** Product sales actually surged (Wi fi extender gross increased from ~10.6k to 30.6k), confirming this is a mix-shift scenario rather than an isolated sales decline.
- **S008 (Market-wide shock - Germany):** Broad market collapse of ~87.7%.

## Conclusion
The evaluation datasets are now formally established and ready for integration into the AI agent evaluation harness in Phase 3.
