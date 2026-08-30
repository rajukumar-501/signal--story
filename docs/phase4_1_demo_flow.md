# Phase 4.1 — S003 Primary Demonstration Flow & Script

**Author:** Lead Product Engineer & UX Architect  
**Milestone:** Phase 4.1 (Demo Flow Design)  
**Status:** SPECIFICATION COMPLETE  
**Primary Scenario:** Scenario S003 (China / Product `A2520150501` / Gross Sales Anomaly / April 2021)

---

## 1. Demonstration Objective

To present a concise, 90-second executive walkthrough demonstrating how the Accenture Decision Intelligence Platform detects a revenue collapse, arbitrates between competing hypotheses across multi-source enterprise data, verifies evidentiary grounding, and recommends actionable operational remediation.

---

## 2. 11-Step Walkthrough Flow

```
[1. Open App] ──► [2. Load S003] ──► [3. Anomaly Banner] ──► [4. Primary Driver]
                                                                     │
[7. Why It Won] ◄── [6. Competing Candidates] ◄── [5. Key Evidence] ◄┘
       │
       └──► [8. Confidence/Status] ──► [9. Action Plan] ──► [10. Evidence Trace] ──► [11. Trust / Audit]
```

---

### Step 1: Open the Application
- **Action:** Navigate to `http://localhost:8000`.
- **Display:** Executive dark-mode dashboard with header controls, scenario selector, and the three primary decision views.

### Step 2: Select & Execute Scenario S003
- **Action:** Select `S003 — China / A2520150501 (Marketing Inefficiency)` from the Scenario Selector dropdown and click **"Run Decision Intelligence Analysis"**.
- **Display:** Progressive loader shows Phase 3A deterministic event detection and Phase 3B causal arbitration executing live.

### Step 3: Executive View — What Happened? (The Anomaly)
- **Visual:** Red-accented Anomaly Banner.
- **Data Displayed:**
  - Metric: `Gross Sales`
  - Market / Scope: `China / Product A2520150501`
  - Period: `April 2021`
  - Movement: **`-72.06%`** vs Baseline ($994.25 actual vs $3,558.03 baseline).

### Step 4: Executive View — Why Did It Happen? (Primary Explanation)
- **Visual:** Emerald-bordered Primary Driver Hero Card.
- **Data Displayed:**
  - Driver: **`DRIVER_03_MARKETING` (Marketing Campaign Inefficiency)**
  - Summary: *"Digital marketing spend expanded by +40%, but acquisition conversion rates dropped -42%, causing a catastrophic return on ad spend."*

### Step 5: Executive View — Strongest Supporting Evidence
- **Visual:** Supporting Evidence Cards grid.
- **Data Displayed:**
  - Card 1 (`EVD-002`): Marketing spend spiked to **1,641.07** (+40% MoM) in `fact_marketing_monthly`.
  - Card 2 (`EVD-003`): Conversion rate collapsed to **3.63%** (-42% MoM) in `fact_marketing_monthly`.

### Step 6: Reasoning View — Competing Candidates
- **Action:** Switch to Tab 2: **"Evidence & Reasoning"**.
- **Visual:** Candidate Arbitration Matrix displaying all 8 investigated hypotheses.
- **Data Displayed:** Shows rank, scores, scope match (`MARKET`), timing (`DURING`), and contradiction count across `DRIVER_03_MARKETING`, `DRIVER_04_RETURNS`, `DRIVER_08_PRODUCT_MIX`, `DRIVER_02_PRICING`, `DRIVER_06_CUSTOMER`, `DRIVER_01_INVENTORY`, `DRIVER_07_MARKET`.

### Step 7: Reasoning View — Why the Selected Candidate Wins & Alternatives Lost
- **Visual:** "Why Selected" Rationale Box & "Why Alternatives Were Rejected" Accordion.
- **Narrative Displayed:**
  - *Pricing (`DRIVER_02_PRICING`):* Rejected because local competitor prices remained stable.
  - *Returns (`DRIVER_04_RETURNS`):* Rejected because return volumes were normal for this product code.
  - *Inventory (`DRIVER_01_INVENTORY`):* Disqualified due to 2 severe stockout contradictions.

### Step 8: Executive View — How Confident Should We Be?
- **Visual:** Causal Certainty Badge & Confidence Meter.
- **Data Displayed:**
  - Status: **`STRONGLY_SUPPORTED`** (or `PLAUSIBLE` depending on live/mock mode).
  - Confidence: **`HIGH`**.
  - Uncertainty: Explicitly notes unobserved competitor promotional activity in secondary channels.

### Step 9: Executive View — What Should We Do Next? (Action Plan)
- **Visual:** Action Plan Card with high-impact recommendations.
- **Action Items:**
  1. *Immediate:* Pause underperforming digital ad campaigns for product `A2520150501` in China.
  2. *Near-Term:* Audit landing page conversion funnel and audience targeting parameters.

### Step 10: Reasoning View — Granular Evidence & Citation Trace
- **Visual:** Color-coded Claim Stream (`OBSERVATION`, `INTERPRETATION`, `CAUSAL_CONCLUSION`, `RECOMMENDATION`).
- **Interactive Feature:** Clicking on `[EVD-002]` chip highlights the corresponding raw evidence card and displays data lineage.

### Step 11: Trust View — Auditability & Provenance Verification
- **Action:** Switch to Tab 3: **"Decision Trace & Trust"**.
- **Visual:** Governance & Safety Verification Card.
- **Data Displayed:**
  - 10-Step Safety Validator: **`PASSED (100% Gated)`**
  - Ground-Truth Leakage: **`0 (Strictly Isolated)`**
  - Provenance: **`LIVE_GEMINI (gemini-3.6-flash)`**
  - Telemetry: Latency recorded, zero hallucinations, full data lineage.

---

## 3. Demo Readiness Checklist

- [x] S003 story communicates WHAT, WHY, EVIDENCE, CONFIDENCE, and ACTIONS in under 90 seconds.
- [x] All 11 steps map 1:1 to actual backend outputs.
- [x] Zero hardcoding — results are fetched live through the backend API.
- [x] Fallback scenario (S008) can also be demonstrated seamlessly to prove graceful uncertainty handling.
