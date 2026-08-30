# Phase 3B Evaluation Contract & Benchmark Design

## 1. Objective & Experimental Design
The purpose of the Phase 3B evaluation is to answer the core scientific question:
> **"Does LLM reasoning over structured and unstructured deterministic evidence improve decision intelligence quality compared with the deterministic engine alone?"**

To evaluate this without moving goalposts, the exact same 8 official scenarios (S001–S008) will be benchmarked:
- **Baseline (Control)**: Phase 3A Frozen Deterministic Engine.
- **Treatment**: Phase 3A Deterministic Engine + Phase 3B LLM Reasoning Layer.

---

## 2. Evaluation Metrics & Performance Baseline vs. Target

| Metric | Frozen Phase 3A Baseline | Phase 3B Aspirational Target Goal | Definition & Evaluation Role |
| :--- | :---: | :---: | :--- |
| **Established Driver Accuracy** | **50.0% (4/8)** | **$\ge 75.0\%$ (6/8)** | Aspirational target goal. Does `diagnosis.established_driver` match the true root cause without scenario tuning or ground-truth access? |
| **Top-3 Hypothesis Recall** | **100.0% (8/8)** | **100.0% (8/8)** | Preservation of full information recall in top candidate hypotheses. |
| **Mean Reciprocal Rank (MRR)** | **0.7143** (den: 7) | **$\ge 0.8500$** | Rank position of true cause in `ranked_hypotheses`. |
| **Status Accuracy** | **37.5% (3/8)** | **$\ge 62.5\%$ (5/8)** | Does `diagnosis.status` match true causal certainty? |
| **Uncertainty Accuracy (S008)** | **100.0% (1/1)** | **100.0% (1/1)** | Output `established_driver = null` and status `NOT_ESTABLISHED` on inconclusive data (S008). |
| **Unsupported-Claim Rate** | **0.0%** | **0.0% (Zero Hallucination)** | Strict requirement: zero assertions without verified evidence citations. |
| **Evidence Grounding Rate** | **100.0%** | **100.0%** | All claims backed by valid indexed `evidence_id` citations. |

> [!IMPORTANT]
> **Aspirational Performance Target Clarification**:
> The $\ge 75.0\%$ Established Driver Accuracy metric is an **aspirational Phase 3B performance target**. It must be evaluated objectively against the frozen S001–S008 evaluation dataset. It must NOT be achieved through scenario-specific tuning, hard-coded answers, ground-truth leakage, or modifications to Phase 3A heuristics or evaluation inputs.

---

## 3. Scenario-by-Scenario Evaluation Specifications

### Scenario S001
- **Scope**: South Korea, Product `A6519160401`, May 2021, `gross_sales`
- **Expected Established Driver**: `DRIVER_04_RETURNS`
- **Expected Status**: `STRONGLY_SUPPORTED`
- **Structured Evidence Available**: Return rate surged significantly MoM; gross returns spike.
- **Unstructured Evidence Available**: CRM logs noting product defects / returns.
- **Acceptable Reasoning**: Identifies that return rate increase is the primary driver behind net revenue / gross sales collapse.
- **Unacceptable Reasoning**: Attributing the drop to marketing inefficiency or generic market decline.
- **Uncertainty Requirement**: Must not claim inventory stockouts caused the drop when inventory was stable.

### Scenario S002
- **Scope**: South Korea, All Products, January 2021, `gross_sales`
- **Expected Established Driver**: `DRIVER_06_CUSTOMER`
- **Expected Status**: `STRONGLY_SUPPORTED`
- **Structured Evidence Available**: Retailer channel share dropped sharply MoM.
- **Unstructured Evidence Available**: Sales call transcripts discussing retailer contract disputes.
- **Acceptable Reasoning**: Synthesizes retailer channel decline with contract disputes in sales call transcripts.
- **Unacceptable Reasoning**: Treating the drop as an overall South Korea market-wide collapse.

### Scenario S003
- **Scope**: China, Product `A2520150501`, April 2021, `gross_sales`
- **Expected Established Driver**: `DRIVER_03_MARKETING`
- **Expected Status**: `STRONGLY_SUPPORTED`
- **Structured Evidence Available**: Marketing spend increased (+40%), conversion rate collapsed (-42%).
- **Acceptable Reasoning**: Explains that customer acquisition efficiency collapsed despite increased marketing investments.
- **Unacceptable Reasoning**: Citing competitor pricing when price gap was neutral.

### Scenario S004
- **Scope**: China, Product `A0621150308`, January 2021, `gross_sales`
- **Expected Established Driver**: `DRIVER_02_PRICING`
- **Expected Status**: `PLAUSIBLE`
- **Structured Evidence Available**: Competitor price gap increased (+8% premium relative to rivals).
- **Acceptable Reasoning**: Concludes that increased pricing premium drove customers to cheaper alternatives.
- **Unacceptable Reasoning**: Forcing a marketing inefficiency diagnosis.

### Scenario S005
- **Scope**: Indonesia, All Products, March 2020, `gross_sales`
- **Expected Established Driver**: `DRIVER_05_SUPPORT`
- **Expected Status**: `PLAUSIBLE`
- **Structured Evidence Available**: Support ticket surge, negative sentiment rate growth.
- **Unstructured Evidence Available**: CRM notes citing regional customer service outage.
- **Acceptable Reasoning**: Connects customer service outage notes with the ticket volume increase.
- **Unacceptable Reasoning**: Misattributing to product mix shifts.

### Scenario S006
- **Scope**: India, Category `Processors`, March 2020, `gross_sales`
- **Expected Established Driver**: `DRIVER_08_PRODUCT_MIX`
- **Expected Status**: `PLAUSIBLE`
- **Structured Evidence Available**: Category sales dropped while adjacent categories remained stable.
- **Acceptable Reasoning**: Explains category-specific demand shift away from processors.
- **Unacceptable Reasoning**: Misdiagnosing as India-wide macroeconomic collapse.

### Scenario S007
- **Scope**: Portugal, Category `Wi fi extender`, September 2019, `category_share`
- **Expected Established Driver**: `DRIVER_08_PRODUCT_MIX`
- **Expected Status**: `STRONGLY_SUPPORTED`
- **Structured Evidence Available**: Wi-fi extender category share dropped by over 50% relative to market.
- **Acceptable Reasoning**: Explains structural category share erosion.
- **Unacceptable Reasoning**: Attributing to support ticket anomalies.

### Scenario S008 (Uncertainty Test)
- **Scope**: Germany, All Products, March 2020, `gross_sales`
- **Expected Established Driver**: `null`
- **Expected Status**: `NOT_ESTABLISHED`
- **Structured Evidence Available**: Germany gross sales dropped ~90%, but peer markets dropped ~86% simultaneously; no specific product/channel/pricing driver anomaly exists.
- **Acceptable Reasoning**: Concludes that no single internal driver (Pricing, Support, Returns, Inventory, Marketing, Customer Channel) has sufficient specific evidence, correctly maintaining an unestablished / uncertain diagnosis.
- **Unacceptable Reasoning**: Forcing an established driver (e.g. claiming Customer Channel or Marketing caused the drop).
