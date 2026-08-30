# Project Rules — Accenture Decision Intelligence Prototype

These rules are non-negotiable governance policies for all current and future engineering work in this repository. Every developer and AI assistant must adhere strictly to these principles.

---

## Rule 1 — Protect Phase Boundaries

Never modify an earlier completed phase merely to make a later phase pass.
- Each phase represents a validated baseline.
- Backward compatibility with upstream phase artifacts must be strictly preserved.
- If a downstream phase exposes a legitimate bug in an upstream phase, the issue must be formally documented and reviewed before any upstream changes are made.

---

## Rule 2 — Phase 3A Protection

Phase 3A is **FROZEN**:
- **Do NOT** change deterministic analytical logic in `src/analytics/`.
- **Do NOT** change driver scoring formulas in `evidence_scorer.py`.
- **Do NOT** change KPI calculation rules in `kpi_engine.py`.
- **Do NOT** change candidate generation logic in `driver_generator.py`.
- **Do NOT** change diagnosis gate rules in `diagnosis.py`.
- **Do NOT** tune thresholds or change evaluation behavior to artificially inflate Phase 3A benchmark scores.

If Phase 3B requires an altered or expanded interface, document the requirement first rather than silently modifying Phase 3A production code.

---

## Rule 3 — Ground Truth Isolation

The production analytical path, runtime LLM prompts, context builders, and reasoning engines must **NEVER** access:
- `Data/scenarios/evaluation_ground_truth/`
- `Data/scenarios/ground_truth.csv`
- `tests/scenario_ground_truth.json`
- Oracle fields (`true_root_cause`, `root_cause_status`, `expected_driver`, `expected_established_driver`, `target_cause`).

Ground truth files are strictly for post-generation evaluation in test suites and must remain completely segregated from runtime execution.

---

## Rule 4 — No Evaluation Leakage

Never hardcode or inject:
- Scenario IDs (e.g. `if scenario_id == 'S001': ...`).
- Expected drivers or root-cause answers into runtime heuristics or prompts.
- Ground-truth labels into test fixtures masquerading as production code.
- Scenario-specific special cases into general reasoning logic.

All diagnostic reasoning must emerge organically from the provided evidence payload.

---

## Rule 5 — No Fabricated Evidence (Anti-Hallucination)

Every evidence claim, metric number, and data finding in the system output must have traceable provenance:
- Citations must reference valid, indexed evidence items (`evidence_id`, `source_dataset`, and `record_id` / `metric`).
- If an unstructured note or metric does not exist in the source telemetry, the system must **NEVER** invent or assume it.
- Hallucinated evidence citations will fail validation and are treated as catastrophic system failures.

---

## Rule 6 — Evidence vs Interpretation

Maintain a strict separation between:
1. **Observed Evidence**: Factual measurements extracted directly from canonical tables (`fact_sales_monthly`, `fact_marketing_monthly`, etc.).
2. **Analytical Inference**: Statistical changes, relative peer comparisons, and MoM trends computed by deterministic engines.
3. **Causal Interpretation**: Hypothesized causal relationships between drivers and outcomes.
4. **Uncertainty**: Known unknowns, unobserved variables, and lack of statistical support.

Do **NOT** present correlation as proven causation. Reserve the status `PROVEN` solely for deterministic definitions and use `STRONGLY_SUPPORTED` or `PLAUSIBLE` for observational findings.

---

## Rule 7 — Uncertainty Must Be Allowed

`NOT_ESTABLISHED` is a legitimate, necessary, and high-value outcome:
- When evidence is insufficient, contradictory, or confounded by macro-market trends (such as scenario S008), the system must explicitly declare `overall_status = "NOT_ESTABLISHED"` and `established_driver = null`.
- The reasoning engine must never force a causal explanation when the underlying data does not support it.

---

## Rule 8 — Deterministic Analytics Remain Deterministic

The LLM must **NOT** replace, re-calculate, or override deterministic KPI calculations already established in Phase 3A:
- Calculations of revenue, margin, return rates, and percentage shifts belong strictly to the deterministic analytical engine.
- The LLM's role is synthesis, semantic interpretation of text, hypothesis arbitration, and business explanation.

---

## Rule 9 — LLM Role

The Phase 3B LLM should reason over controlled analytical outputs and indexed evidence:
- It must act as an objective synthesizer and decision-support partner.
- It must interpret unstructured CRM notes and sales call transcripts in the context of numerical telemetry.
- It must not independently invent metrics, hallucinate database facts, or bypass deterministic validation gates.

---

## Rule 10 — Evaluation Integrity

Evaluation datasets and benchmarks must remain strictly isolated:
- The evaluation harness must evaluate model outputs strictly after reasoning has concluded.
- Benchmarks must use identical criteria across all comparative runs (Phase 3A baseline vs Phase 3B treatment).
- Benchmark metrics (Top-1 Accuracy, Top-3 Recall, MRR, Uncertainty Accuracy, Grounding Rate) must never be redefined to mask regressions.

---

## Rule 11 — Reproducibility

Every code modification and milestone achievement must have:
1. **Implementation Evidence**: Clean, documented source code.
2. **Test Evidence**: Automated unit and regression tests verifying behavior.
3. **Documentation**: Clear reports documenting methodology and findings.
4. **Reproducible Execution**: Deterministic execution paths (temperature=0 for LLMs, deterministic seeds where applicable).

---

## Rule 12 — No Silent Changes

If a task requires changing a frozen component or modifying an established contract:
1. **STOP**.
2. Document **why** the change is necessary.
3. Document **what** specifically would change.
4. Document the **impact** on upstream and downstream components.
5. Document **alternative approaches** that avoid modifying frozen code.
6. Obtain explicit authorization before proceeding.

---

## Rule 13 — Progress Tracking & Engineering Workflow

### Before starting ANY implementation task:
1. Read `PROJECT_PLAN.md`.
2. Read `PROJECT_PROGRESS.md`.
3. Read `PROJECT_RULES.md`.
4. Identify the current phase and authorized task.
5. Identify dependencies and frozen components.
6. Execute only the next authorized task within scope.

### After completing ANY task:
1. Run all relevant unit and regression test suites.
2. Verify zero regressions on earlier phases.
3. Record what changed (files created, modified, deleted).
4. Record test execution results and metrics.
5. Record remaining work.
6. Update `PROJECT_PROGRESS.md` (dashboard, current position, change log).
7. Update `PROJECT_PLAN.md` only if the architecture or roadmap itself changed.
8. **Never rewrite history** in progress logs.

## Rule 14 — MRR Calculation & Provenance Protocol

Calculation must precede documentation:
- The MRR (Mean Reciprocal Rank) metric is mathematically defined as:
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **Eligible Scenarios ($|Q| = 7$)**: Scenarios S001 through S007 are driver-seeking queries with explicit target causal drivers.
- **Treatment of S008**: S008 is an uncertainty benchmark scenario where ground truth is `NOT_ESTABLISHED` and `expected_established_driver = None`. Because no target driver exists in the candidate catalog, S008 is evaluated under **Uncertainty Accuracy** ($1/1 = 100.0\%$) and excluded from the ranking MRR denominator ($N=7$).
- **Canonical Value**:
  $$\text{Numerator} = 0.5 + 0.5 + 1.0 + 1.0 + 1.0 + 0.5 + 0.5 = 5.0$$
  $$\text{Denominator} = 7$$
  $$\text{Canonical MRR} = \frac{5.0}{7} = \mathbf{0.7143}$$
- Never alter the denominator or assign artificial ranks to S008 to manipulate the MRR value.

---

## DOCUMENTATION / IMPLEMENTATION CONFLICTS

The repository audit identified the following minor documentation and tooling inconsistencies:

1. **Test Execution Pathing (`PYTHONPATH`)**:
   - Running `python tests/test_phase3a3_accuracy.py` directly from the repository root fails with `ModuleNotFoundError: No module named 'src'` because `.` is not on `sys.path`.
   - Running via `python -m unittest discover -s tests` or `python -m tests.test_phase3a3_accuracy` succeeds with 100% pass rate.
   - *Resolution*: Follow standard Python module invocation (`python -m unittest discover -s tests`). Do not alter frozen test files.

2. **Dataset File Naming Discrepancies in Architecture Docs (Resolved)**:
   - `docs/phase3b_ground_truth_isolation.md` previously referenced `fact_pricing_competitor_monthly.csv` and `fact_sales_call_transcripts.csv`.
   - The actual canonical filenames in `Data/Processed/` are `fact_competitor_pricing_monthly.csv` and `fact_sales_calls.csv`.
   - *Resolution*: Corrected `docs/phase3b_ground_truth_isolation.md` to match the exact 10 canonical files in `Data/Processed/`.

3. **Status Accuracy Reporting Evolution**:
   - In Phase 3A.1 (`docs/phase3a_report.md`), Status Accuracy was reported as 50.0% (4/8).
   - In Phase 3A.2/3A.3 (`docs/phase3a2_report.md`, `docs/phase3a3_comparison.md`), Status Accuracy is 37.5% (3/8) due to stricter single-source confidence capping (PLAUSIBLE instead of over-confident STRONGLY_SUPPORTED).
   - *Resolution*: Stricter scoring is intentional and documented in `PROJECT_PROGRESS.md`.

4. **Legacy Scenario Evidence Files**:
   - Legacy files `Data/scenarios/S001_evidence.csv`–`S008_evidence.csv` from Phase 2B coexist alongside `Data/scenarios/evaluation_inputs/` from Phase 2B.1/2B.2.
   - *Resolution*: `Data/scenarios/evaluation_inputs/` is the canonical, sanitized input directory for all evaluations.
