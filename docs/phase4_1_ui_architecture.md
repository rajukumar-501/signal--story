# Phase 4.1 — Decision Intelligence UI Architecture & Specification

**Author:** Lead Product Engineer & UX Architect  
**Milestone:** Phase 4.1 (UI Architecture & Design)  
**Status:** ARCHITECTURE APPROVED  
**Project:** Accenture Decision Intelligence Prototype

---

## 1. Current Project Architecture

The Accenture Decision Intelligence backend is structured into two frozen, layered tiers:
1. **Tier 1 (Phase 3A Deterministic Engine):** Ingests raw multidimensional scenario requests, evaluates baseline anomalies (`EventDetector`), generates 8 candidate drivers (`DriverGenerator`), scores empirical evidence (`EvidenceScorer`), evaluates contradictions (`ContradictionEngine`), ranks drivers (`DriverRanker`), and applies a 7-rule certainty gate (`DiagnosisGate`).
2. **Tier 2 (Phase 3B Evidence-Grounded Reasoning Layer):** Adapts Phase 3A outputs (`Phase3BInputAdapter`), sandboxes untrusted text and indexes evidence to `EVD-xxx` IDs (`EvidenceContextBuilder`), executes a 6-step causal arbitration prompt against Google Gemini (`LLMReasoningProvider`), validates response schemas and citations (`Phase3BResponseValidator`), and enforces safe deterministic fallbacks on error (`Phase3BReasoningEngine`).

---

## 2. Existing Frontend Status

Prior to Phase 4, the repository operated purely as a Python backend and evaluation engine. No web server or interactive UI existed. Analytical runs were triggered via CLI scripts or unit test harnesses.

---

## 3. Existing Backend Interface

The frontend communicates with the frozen backend via Python modules:
- `src.analytics.run_analysis.run_analysis(request: dict) -> dict`
- `src.phase3b.engine.run_phase3b_pipeline(phase3a_payload: dict, provider: Optional[ReasoningProvider]) -> dict`
- Benchmark scenario catalog: `tests.test_phase3b6_evaluation_integrity.BENCHMARK_SCENARIOS` (8 official scenarios S001–S008).

---

## 4. Phase 3B Output Structures

The reasoning engine produces a structured JSON dictionary:
```json
{
  "executive_summary": "Diagnostic arbitration establishes DRIVER_03_MARKETING...",
  "what_happened": "gross_sales shifted by -72.06% compared to historical baseline.",
  "diagnosis": {
    "driver": "DRIVER_03_MARKETING",
    "status": "STRONGLY_SUPPORTED",
    "confidence": "HIGH"
  },
  "candidate_comparisons": [
    {
      "driver": "DRIVER_03_MARKETING",
      "scope_alignment": "MARKET",
      "temporal_alignment": "DURING",
      "independent_source_count": 1,
      "contradiction_count": 0,
      "comparison_summary": "..."
    }
  ],
  "why_selected": "...",
  "why_alternatives_rejected": ["..."],
  "claims": [
    {
      "claim": "...",
      "claim_type": "OBSERVATION | INTERPRETATION | CAUSAL_CONCLUSION | RECOMMENDATION",
      "evidence_ids": ["EVD-002", "EVD-003"]
    }
  ],
  "supporting_evidence": [
    {
      "evidence_id": "EVD-002",
      "source_dataset": "fact_marketing_monthly",
      "metric": "spend",
      "finding": "..."
    }
  ],
  "contradictory_evidence": [],
  "uncertainties": ["..."],
  "recommended_next_steps": ["..."],
  "traceability": [{"evidence_id": "EVD-002", "source_dataset": "...", "record_id": null}],
  "validation_status": "PASSED",
  "pipeline_latency_ms": 25368.81
}
```

---

## 5. Proposed UI Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│               ENTERPRISE DECISION INTELLIGENCE PORTAL                   │
├────────────────────────────────────────────────────────────────────────┤
│  Top Navigation: Scenario Selector (S001–S008) | Provider Mode Toggle │
├────────────────────────────────────────────────────────────────────────┤
│  View 1: EXECUTIVE DECISION VIEW                                       │
│  ┌─────────────────────────────────┬─────────────────────────────────┐  │
│  │ 1. WHAT HAPPENED? (Anomaly)     │ 2. WHY DID IT HAPPEN? (Driver)  │  │
│  │ - Gross Sales: -72.06% vs base  │ - Primary Driver: Marketing Ineff│  │
│  │ - Scope: China / A2520150501    │ - Status: STRONGLY_SUPPORTED    │  │
│  ├─────────────────────────────────┼─────────────────────────────────┤  │
│  │ 3. SUPPORTING EVIDENCE (Cards)  │ 4. RECOMMENDED ACTION (Decide)  │  │
│  │ - EVD-002: Spend surge (+40%)   │ - Reallocate digital ad spend   │  │
│  │ - EVD-003: Conversion collapse  │ - Audit campaign targeting      │  │
│  └─────────────────────────────────┴─────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────┤
│  View 2: EVIDENCE & REASONING VIEW                                     │
│  ┌─────────────────────────────────┬─────────────────────────────────┐  │
│  │ A. CANDIDATE ARBITRATION MATRIX │ B. CAUSAL CLAIMS & CITATIONS    │  │
│  │ - 8 Hypotheses Ranked           │ - [OBS] Sales drop (EVD-001)    │  │
│  │ - Scope & Temporal Alignment    │ - [INT] Marketing focus (EVD-002│  │
│  │ - Contradiction Penalties       │ - [CAU] Root cause conclusion   │  │
│  │ - Why Alternatives Rejected     │ - [REC] Targeted remediation    │  │
│  └─────────────────────────────────┴─────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────┤
│  View 3: DECISION TRACE & TRUST VIEW                                   │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ - Deterministic vs Reasoning Alignment (P3A: 0.7143 | P3B: 0.7143) │  │
│  │ - Validator Status: PASSED (10/10 Gating Rules Compliant)          │  │
│  │ - Provenance: LIVE_GEMINI (gemini-3.6-flash, 25.37s)               │  │
│  │ - Data Lineage & Sandboxed Evidence Records                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Component Hierarchy

```text
DecisionIntelligenceApp
│
├── AppHeader
│   ├── BrandLogo & ProductTitle ("Accenture Decision Intelligence")
│   ├── ScenarioSelectorDropdown (S001–S008 Quick Select)
│   ├── ExecutionModeToggle (Live Gemini vs Fast Mock)
│   └── TriggerAnalysisButton
│
├── ViewNavigationTabs
│   ├── TabButton("Executive Decision", badge: Primary)
│   ├── TabButton("Evidence & Reasoning", badge: 8 Candidates)
│   └── TabButton("Decision Trace & Trust", badge: Audited)
│
├── ExecutiveDecisionView (View 1)
│   ├── AnomalyAlertBanner (Metric, Baseline, Delta %, Market Scope)
│   ├── PrimaryDriverCard (Driver Badge, Causal Status, Confidence)
│   ├── ExecutiveSummaryPanel (Synthesis Narrative)
│   ├── EvidenceHighlightGrid (Top 2–4 Supporting Evidence Cards)
│   └── ActionPlanCard (Recommended Next Steps & Decision Impact)
│
├── EvidenceReasoningView (View 2)
│   ├── CandidateArbitrationTable (Rank, Driver, Score, Scope, Timing, Contradictions)
│   ├── WhySelectedPanel & RejectionDetailsAccordion
│   ├── ClaimCitationStream (Color-coded by Claim Type: Obs/Int/Causal/Rec)
│   ├── SupportingEvidenceExplorer (Filterable multi-source cards)
│   └── UncertaintyBoundaryNotice (Explicit limits & unobserved factors)
│
└── DecisionTraceTrustView (View 3)
    ├── EngineComparisonCard (Phase 3A vs Phase 3B Outputs)
    ├── SafetyValidatorStatus (Schema Check, ID Citation Validation)
    ├── ProvenanceTelemetry (Provider, Model, Latency, Token Notice)
    ├── FallbackDiagnosticPanel (Active when fallback is invoked)
    └── EvidenceLineageTable (Dataset, Record ID, Evidence ID)
```

---

## 7. State Management Approach

- **State Container:** Clean client-side state module (`appState`) in vanilla JavaScript.
- **Key State Variables:**
  - `currentScenarioId`: Currently selected scenario ID (`S001`–`S008`).
  - `activeView`: Active tab (`executive`, `reasoning`, `trust`).
  - `executionMode`: `live_gemini` or `fast_mock`.
  - `loadingState`: `idle`, `loading_p3a`, `loading_p3b`, `complete`, `error`.
  - `p3aPayload`: Result object from deterministic engine.
  - `p3bPayload`: Result object from reasoning engine.
  - `provenanceMetadata`: `{ provider, model, mode, latency_ms, validation_passed }`.

---

## 8. Data Flow

1. User selects scenario from dropdown (e.g. S003) and clicks **"Analyze Anomaly"**.
2. Frontend dispatches `POST /api/analyze` with scenario parameters (`market`, `product_code`, `date`, `kpi`, `provider_mode`).
3. Backend executes `run_analysis(request)` (Phase 3A) and passes output to `run_phase3b_pipeline(p3a_payload)` (Phase 3B).
4. Backend packages `{ phase3a: p3a, phase3b: p3b, metadata: {...} }` and returns HTTP 200 JSON.
5. Frontend parses response into `appState` and triggers reactive re-render of active view with zero page reload.

---

## 9. Error Handling

- **Network / Server Down:** Shows non-blocking toast alert: `"Backend server unavailable. Please ensure local server is running on port 8000."`
- **Invalid Parameters:** Gracefully flags baseline status if `baseline_status != "VALID"`.
- **API Failure:** Displays safe deterministic fallback banner with explicit reason.

---

## 10. Loading States

- Multi-stage progressive loader:
  - Step 1: *"Detecting KPI anomaly & computing historical baseline..."* (~50ms)
  - Step 2: *"Generating candidate hypotheses & scoring multi-source evidence..."* (~150ms)
  - Step 3: *"Executing causal arbitration with Google Gemini reasoning engine..."* (~20–30s in Live Mode, ~1s in Mock Mode)
- Visual animated progress bar with elapsed timer.

---

## 11. Fallback States (e.g. S008)

When `validation_status == "FALLBACK_PRESERVED"` or `provenance == "LIVE_WITH_FALLBACK"`:
- Status banner displays: `[REASONING FALLBACK ACTIVE] — Deterministic analytical result preserved.`
- Provenance badge displays: `LIVE_WITH_FALLBACK (Deterministic Safe Mode)`.
- Replaces AI reasoning with deterministic diagnostic rule string.

---

## 12. Evidence Visualization Strategy

- **Visual Separation:**
  - `OBSERVED EVIDENCE`: Clean blue badge (`EVD-002`, `fact_marketing_monthly`, metric: `spend`, value: `1641.07`).
  - `ANALYTICAL INFERENCE`: Purple badge with score and ranking.
  - `CAUSAL INTERPRETATION`: Emerald badge with certainty status (`STRONGLY_SUPPORTED`).
  - `UNCERTAINTY`: Amber warning badge with explicitly documented boundary limits.
- **Evidence Cards:** Contain Dataset name, Lineage, Metric, Baseline vs Event value, and Temporal role.

---

## 13. Reasoning Visualization Strategy

- **Arbitration Matrix:** Interactive table comparing 8 candidates across Scope Alignment, Temporal Precedence, Independent Source Count, and Contradiction Count.
- **Claim-Level Citation Stream:** Shows individual assertions paired directly with clickable `[EVD-xxx]` chips that highlight the corresponding evidence card.

---

## 14. Trust & Audit Visualization Strategy

- **Side-by-Side Comparison:** Compares Phase 3A deterministic driver vs Phase 3B reasoning driver.
- **10-Step Safety Audit Badge:** Displays green checkmarks for Schema Conformity, Citation Integrity, Uncertainty Gating, and Zero Oracle Leakage.
- **Telemetry Bar:** Displays exact execution latency, provider model (`gemini-3.6-flash`), and endpoint security status.

---

## 15. S003 Primary Demo Flow

- **Scenario:** China / Product `A2520150501` (`gross_sales`, `2021-04-01`).
- **Storyline:**
  1. *What Happened:* Gross sales collapsed -72.06% ($994.25 vs $3,558.03 baseline).
  2. *Why:* Marketing campaign inefficiency (`DRIVER_03_MARKETING`) — ad spend surged +40% while conversion rates plummeted -42%.
  3. *Why Alternatives Lost:* Competitor pricing was normal; return rates showed zero spike.
  4. *What To Do:* Reallocate digital ad spend and audit conversion funnel.
  5. *Trust:* 100% evidence grounding with zero unsupported claims.

---

## 16. Backend / UI Contract

- Full contract specifications defined in [`docs/phase4_1_backend_ui_contract.md`](file:///c:/Users/rajuk/OneDrive/Desktop(1)/Accenture_Decision_Intelligence/docs/phase4_1_backend_ui_contract.md).

---

## 17. Freeze Boundary

Phase 3A, Phase 3B, datasets, ground truth, and benchmark evaluation files remain strictly **FROZEN**.

---

## 18. Technical Risks & Mitigation

| Risk | Mitigation |
| :--- | :--- |
| **Live API Latency (~25s)** | Provide interactive `Fast Mock Mode` toggle for instant 1-second presentation demos, alongside `Live Gemini Mode` for live proof. |
| **API Rate Limiting (HTTP 429)** | Safe fallback gracefully displays deterministic analysis with clear fallback badge. |

---

## 19. Implementation Sequence for Phase 4.2+

1. **Phase 4.2 (Backend API Server):** Create lightweight Python HTTP server (`src/server.py` / `app.py`) bridging the static frontend and frozen analytical pipelines.
2. **Phase 4.3 (Frontend Design System & Components):** Implement `index.html`, `styles.css`, and modular JavaScript view renderers (`app.js`, `views/*.js`).
3. **Phase 4.4 (Interactive Verification & Demo Walkthrough):** Validate full S001–S008 interactive execution, S003 demo flow, and fallback handling in browser.

---

## 20. Acceptance Criteria Checklist

- [x] Three dedicated views designed (Executive Decision, Evidence & Reasoning, Trust / Trace)
- [x] Clear visual distinction between Observed, Inferred, Causal, and Uncertainty data
- [x] Real S003 data flow mapped from frozen backend to UI
- [x] Live vs Fallback provenance handling defined
- [x] Zero recalculation of analytical metrics in frontend
- [x] Backend frozen boundaries preserved
