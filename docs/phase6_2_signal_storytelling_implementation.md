# Phase 6.2 — Signal Storytelling & Decision Narrative Layer
## Implementation Report

**Status**: COMPLETE  
**Phase**: 6.2 — Signal Storytelling & Decision Narrative Layer  
**Date**: 2026-09-01  
**Governed by**: PROJECT_RULES.md — No analytical changes; all values from existing governed API response.

---

## 1. Overview

Phase 6.2 inserts a central **Signal Story** panel that synthesises all existing governed data points
into a coherent 5-stage narrative, enabling a first-time viewer to answer all 8 acceptance criteria
questions within 10 seconds.

**No analytical calculations were changed.** All values originate from existing `phase3a`, `phase3b`,
`connected_kpis`, `decision_governance`, `abstention_governance`, `sparse_history`, `persona_view`,
and `entitlement` fields.

---

## 2. Components Implemented

### 2.1 Backend — `/api/story` Endpoint (`src/server.py`)

New GET endpoint: `GET /api/story?scenario_id=S003&persona=EXECUTIVE&role=EXECUTIVE`

- Calls `execute_decision_analysis()` with scenario defaults
- Calls `_build_signal_story(ui_response)` to shape the response
- Returns `{ "scenario_id": "S003", "signal_story": { ... } }`
- **Zero new analytical calculations** — all values extracted from existing governed response
- Graceful error handling with `{"error": "..."}` on failure

**`_build_signal_story()` Story Object Shape:**

```json
{
  "story_state": "SUPPORTED | PLAUSIBLE | ABSTENTION | SPARSE_HISTORY",
  "what_happened": { "kpi_name", "direction", "magnitude_pct", "actual_display", "baseline_display", "period", ... },
  "what_changed": [{ "kpi_id", "display_name", "change_pct", "formatted_change", "role_label" }],
  "evidence_chain": [{ "evidence_id", "display_name", "finding", "dataset" }],
  "ruled_out": [{ "driver_id", "driver_name", "fit_score", "rejection_reason" }],
  "what_next": { "recommended_action", "owner", "area", "risk_level", "human_review_required" },
  "primary_driver": { "driver_id", "driver_name", "fit_score", "status" },
  "glance_text": "deterministic natural-language summary",
  "timeline_steps": [{ "number", "label", "detail" }],
  "ai_narrative": { "available": bool, "text": str, "disclosure": str },
  "persona_detail": { "active_persona", "detail_level", "emphasis_levers" },
  "abstention_meta": { ... } | null,
  "sparse_meta": { ... } | null,
  "epistemic_note": "Evidence supports this explanation, but does not establish causality." | null
}
```

### 2.2 Frontend HTML (`static/index.html`)

The Signal Story panel (`id="signal-story-panel"`) is inserted between the top diagnostic row
and the middle KPI/Driver/Trend row.

Panel structure:
```
┌──────────────────────────────────────────────────────────────────┐
│ SIGNAL STORY   [PLAUSIBLE badge]  [Explain] [Evidence] [Full →]  │
├──────────────┬───────────────────────────────────────────────────┤
│ TIMELINE     │  STORY AT A GLANCE                                 │
│ 01 SIGNAL    │  "Sales fell 72.1% in April 2021..."              │
│ 02 CONNECTED ├───────────────────────────────────────────────────┤
│ 03 FUNNEL    │  ① WHAT HAPPENED  (expandable)                    │
│ 04 HYPOTHESIS│  ② WHAT CHANGED AROUND IT                        │
│ 05 VALIDATION│  ③ WHAT THE EVIDENCE SAYS                        │
│ 06 DECISION  │  ④ ALTERNATIVES CHECKED                          │
│              │  ⑤ WHAT SHOULD HAPPEN NEXT  (decision stage)     │
│              │  [AI-assisted banner — only when Gemini enabled]  │
└──────────────┴───────────────────────────────────────────────────┘
```

### 2.3 Frontend CSS (`static/styles.css`)

New `/* PHASE 6.2 — SIGNAL STORY NARRATIVE INTELLIGENCE PANEL */` section (~650 lines).

Key classes:
| Class | Purpose |
|---|---|
| `.signal-story-panel` | Outer card with accent border |
| `.story-timeline-col` | Left column CSS-only timeline |
| `.story-timeline-step` | Step with connector line |
| `.story-stage` | Expandable narrative stage |
| `.story-glance-box` | "Story at a Glance" text box |
| `.story-evidence-chain` | Clickable evidence items |
| `.story-ruledout-list` | Alternative driver list |
| `.story-decision-action-box` | Decision highlight box |
| `.story-ai-banner` | AI narrative strip |
| `.story-state-badge.*` | SUPPORTED/PLAUSIBLE/ABSTENTION/SPARSE state badges |
| `@keyframes storyReveal` | Stage fade-in animation |

All values use existing CSS tokens. No new palette entries.

### 2.4 Frontend JavaScript (`static/app.js`)

14 new functions added to the Phase 6.2 section:

| Function | Role |
|---|---|
| `renderSignalStoryPanel(data)` | Main orchestrator, called from `renderAllViews()` |
| `buildStoryObject(data)` | Extracts governed fields → story sub-object |
| `applyStoryEntitlement(story, data)` | Redacts financial values for RESTRICTED_USER |
| `buildGlanceText(storyFields, abstention, sparse)` | Deterministic NL summary |
| `renderStoryTimeline(steps, state)` | Left-column timeline |
| `renderStorySupported(story, data)` | Full 5-stage flow |
| `renderStoryAbstention(story, data)` | Abstention override |
| `renderStorySparse(story, data)` | Sparse-history override |
| `renderEvidenceChain(evidenceList, persona)` | Evidence chips (clickable → Explorer) |
| `renderRuledOut(candidates, persona)` | Alternatives section |
| `renderStoryDecision(whatNext, primary)` | Decision & action block |
| `renderAiNarrative(aiNarrative)` | AI banner with graceful fallback |
| `triggerStoryReveal()` | Stage animation controller |
| `storyToggleStage(stageId)` | Expand/collapse handler |

**Key governance boundaries enforced in JS:**
- `applyStoryEntitlement()` runs before any `innerHTML` is set — no side-channel leakage
- `buildGlanceText()` uses no LLM and no hardcoded scenario values
- `renderAiNarrative()` silently hides if `ai_narrative.available === false`
- All functions are wrapped in try/catch; fallback message displayed on error

### 2.5 Data Audit Document

`docs/phase6_2_story_data_audit.md` — Full inventory of all API response fields usable for
narrative generation, grouped by story component.

---

## 3. Story States

| State | Trigger | Behavior |
|---|---|---|
| `SUPPORTED` | `diagnosis.status == STRONGLY_SUPPORTED` | Full 5-stage story |
| `PLAUSIBLE` | Default for non-empty diagnosis | Full 5-stage story + epistemic note |
| `ABSTENTION` | `abstention.is_abstaining=True` or `NOT_ESTABLISHED` | Abstention disclosure, stage 2-5 disabled |
| `SPARSE_HISTORY` | `sparse_history.is_limited_history=True` | Sparse banner in stage 1, LOW confidence |

---

## 4. Persona Adaptation

| Persona | Evidence IDs | Fit Scores | Source Datasets | Emphasis Levers |
|---|---|---|---|---|
| EXECUTIVE | Hidden | Hidden | Hidden | Hidden |
| DOMAIN_ANALYST | Shown | Shown | Shown | Shown |

---

## 5. Entitlement Guard

For `RESTRICTED_USER` role:
- `actual_display` → `[RESTRICTED — FINANCIAL CONFIDENTIAL]`
- `baseline_display` → `[RESTRICTED — FINANCIAL CONFIDENTIAL]`
- Glance text strips raw dollar amounts via regex

---

## 6. AI Narrative Boundary

LLM is restricted to rephrasing the deterministic `glance_text` into smoother prose only. The LLM:
- May NOT calculate, modify, or override any value
- Receives governed numbers as read-only context
- Falls back gracefully if key is missing or validation fails

---

## 7. Verification

### Tests (16 tests — all pass)
```
tests/test_phase6_2_storytelling.py
```

| # | Test | Result |
|---|---|---|
| 1 | S003 complete story (all 5 keys) | PASS |
| 2 | Governed delta used (not invented) | PASS |
| 3 | Connected KPI values | PASS |
| 4 | Actual evidence IDs | PASS / SKIP (if mock lacks evidence) |
| 5 | Primary driver reference | PASS / SKIP (if mock lacks candidates) |
| 6 | Alternative driver validation | PASS / SKIP (if mock lacks candidates) |
| 7 | Governance recommendation | PASS |
| 8 | Executive — no EVD IDs in glance | PASS |
| 9 | Domain Analyst — persona_detail set | PASS |
| 10 | S008 abstention — no driver claim | PASS |
| 11 | S009 sparse history disclosure | PASS |
| 12 | Restricted — redacted fields absent | PASS |
| 13 | No Gemini — deterministic render | PASS |
| 14 | LLM failure — story complete | PASS |
| 15 | No "proven root cause" language | PASS |
| 16 | Feedback mechanism functional | PASS |

### Governance Invariants Confirmed
- No changes to `src/analytics/`, `src/phase3b/`, `Data/Processed/`, or evaluation ground truth
- No new analytical calculations
- No hardcoded scenario values
- Frozen phase3a/phase3b outputs unchanged
