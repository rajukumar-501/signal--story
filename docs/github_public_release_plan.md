# Signal Story — Public GitHub Release Plan
## Accenture Decision Intelligence Hackathon Submission

---

## 1. Executive Summary

This document establishes the official public release plan for **Signal Story**, an evidence-grounded Decision Intelligence prototype developed for the **Accenture Decision Intelligence** hackathon track.

Signal Story combines deterministic statistical anomaly detection with multi-source causal arbitration, connected KPI modeling, context-aware analyst feedback learning, role-based access control, persona adaptation, and an executive-ready storytelling UI.

The goal of this release plan is to guarantee:
1. **Zero Secret Leakage**: Total elimination of any API keys, credentials, or private configuration from public tracking.
2. **Evaluation Ground Truth Isolation**: Physical and logical decoupling of benchmark answer keys from runtime execution paths.
3. **Repository Cleanliness**: Complete removal of temporary development caches, runtime logs, and platform-specific artifacts.
4. **Judge-Friendly Reproducibility**: 100% turnkey local and cloud execution with deterministic zero-API fallback modes.

---

## 2. Artifact Classification Matrix

Every file and directory in the repository has been audited and assigned an immutable classification tier:

| Classification Tier | Target Audience | Repository Treatment | Description |
|---|---|---|---|
| **Tier 1: Core Runtime (Public)** | Evaluators / Users | **Tracked in Git** | Core production modules (`src/`, `static/`, `app.py`, `streamlit_app.py`, `requirements.txt`). |
| **Tier 2: Semantic Contracts (Public)** | Evaluators / Auditors | **Tracked in Git** | Machine-readable schemas (`Data/semantic/` including KPI, DQ, Governance, Entitlement, Persona, and Telemetry contracts). |
| **Tier 3: Analytical Data (Public)** | Runtime Engine | **Tracked in Git** | Canonical warehouse partitions (`Data/Processed/`, `Data/raw/`, `Data/Synthetic/`) required for anomaly detection. |
| **Tier 4: Benchmark Suite (Public / Isolated)** | Evaluators / CI | **Tracked in Git (Segregated)** | Evaluation inputs (`Data/scenarios/evaluation_inputs/`) and ground truth (`Data/scenarios/evaluation_ground_truth/`). |
| **Tier 5: Historical Evaluation Records (Public)** | Evaluators / Reviewers | **Tracked in Git** | Benchmark result CSVs and JSON manifests (`Data/evaluation/`). |
| **Tier 6: Technical Documentation (Public)** | Hackathon Judges | **Tracked in Git** | System specs, phase audits, architecture diagrams, and checklists (`docs/`, `README.md`, `PROJECT_PLAN.md`). |
| **Tier 7: Automated Test Suite (Public)** | Developers / Judges | **Tracked in Git** | 40 test files covering regression, adversarial defense, and governance (`tests/`). |
| **Tier 8: Secrets & Credentials (Private / Forbidden)** | None | **Strictly Gitignored** | Live API keys (`.env`). Must NEVER be committed. |
| **Tier 9: Runtime State (Ephemeral)** | Local Runtime | **Strictly Gitignored** | Dynamic user feedback (`Data/feedback/`), runtime execution logs (`*.log`). |
| **Tier 10: Development Caches (Internal)** | Developer Local | **Strictly Gitignored** | Bytecode caches (`__pycache__/`, `*.pyc`), scratch scripts (`scratch/`). |

---

## 3. Secret Management & Credential Safety

### 3.1 Strict Separation of Configuration and Credentials
* **Committed Template**: `.env.example` provides a sanitized, credential-free schema specifying configuration keys (`LLM_PROVIDER`, `LLM_MODEL`, `GEMINI_API_KEY`, `HOST`, `PORT`).
* **Active Credentials File**: `.env` is permanently excluded via `.gitignore` (Rule: `.env*`, Exception: `!.env.example`).
* **Git History Audit**: Verified via `git log --all --source -- .env` that no `.env` file has ever been introduced into git commit history.
* **Source Code Scans**: Automated AST pattern scans confirm zero hardcoded strings matching API key regexes (`AIzaSy*`, `sk-*`, raw secret strings) in `src/`, `static/`, or `Data/`.

### 3.2 Dual Runtime Modes
1. **Assisted Analysis Mode (Live)**: Utilizes `GEMINI_API_KEY` from the environment for real-time Google Gemini LLM causal reasoning.
2. **Preview Mode (Deterministic Offline)**: When `GEMINI_API_KEY` is omitted or empty, the platform automatically routes to `MockReasoningProvider`, delivering deterministic, pre-validated executive insights with zero network calls and zero configuration required.

---

## 4. Evaluation Ground Truth Isolation

To preserve evaluation integrity, Signal Story enforces strict architectural segregation between runtime decision systems and benchmark answer keys:

```text
======================= RUNTIME EXECUTION PATH =======================
Data/Processed/ (Canonical Data) ──> src/analytics/ (Anomaly Detection)
                                             │
                                             ▼
                                  src/phase3b/input_adapter.py
                                  (Ground Truth Stripping & Validation)
                                             │
                                             ▼
                                  src/phase3b/engine.py (Reasoning)
                                             │
                                             ▼
                                  src/phase3b/validator.py (Safety Gates)

======================= ISOLATED EVALUATION PATH =====================
Data/scenarios/evaluation_ground_truth/ (Oracle Truth)
                                             │
                                             ▼
                                  tests/ & evaluation scripts
                                  (Zero linkage to runtime server)
```

### Architectural Guarantees
1. **Physical Isolation**: Ground truth answer keys are stored exclusively in `Data/scenarios/evaluation_ground_truth/` and `tests/scenario_ground_truth.json`.
2. **AST Input Contract Guard**: `src/phase3b/input_adapter.py` and `src/reasoning/input_contract.py` actively inspect all input dictionaries and raise `ValueError` / reject payloads if fields like `true_root_cause`, `expected_driver`, or `ground_truth` are detected.
3. **Runtime Server Isolation**: Neither `app.py`, `streamlit_app.py`, nor `src/server.py` import or reference evaluation directories.

---

## 5. Repository Structure for Public Release

```text
signal-story/
├── app.py                             # Native HTTP application server launcher
├── streamlit_app.py                   # Streamlit Community Cloud web application
├── requirements.txt                   # Standard runtime dependencies
├── .env.example                       # Sanitized configuration template
├── .gitignore                         # Comprehensive secrets & cache exclusion rules
├── README.md                          # Main project briefing, architecture & demo guide
├── PROJECT_PLAN.md                    # Engineering roadmap across Phase 1 to Phase 6
├── PROJECT_PROGRESS.md                # Phase-by-phase implementation log & audit status
├── PROJECT_RULES.md                   # Development principles & architectural contracts
│
├── Data/
│   ├── Processed/                     # 10 Canonical warehouse partition datasets (CSV)
│   ├── raw/                           # Original source reference tables (CSV)
│   ├── Synthetic/                     # Synthetic domain telemetry partitions (CSV)
│   ├── semantic/                      # 8 Governance & semantic contracts (JSON)
│   │   ├── kpi_contract.json          # Metric hierarchy & threshold specifications
│   │   ├── data_trust_contract.json   # 40-rule data quality verification contract
│   │   ├── decision_action_contract.json # Operational risk & actionability contract
│   │   ├── connected_kpi_contract.json   # Cross-source metric correlation schema
│   │   ├── entitlement_contract.json  # Role-based access & redaction policy
│   │   ├── persona_contract.json      # Narrative depth & persona adaptation rules
│   │   ├── processing_classification_contract.json # LLM vs Non-LLM boundary contract
│   │   └── source_integration_spec.json  # Multi-source system lineage specification
│   ├── scenarios/                     # Benchmark definitions & isolated ground truth
│   │   ├── evaluation_inputs/         # Input parameters for scenarios S001–S008
│   │   └── evaluation_ground_truth/   # Oracle ground truth for benchmark verification
│   └── evaluation/                    # Multi-run evaluation outputs & manifests (CSV/JSON)
│
├── src/
│   ├── server.py                      # Multi-threaded standard library HTTP API server
│   ├── data/                          # Data preprocessing pipelines
│   ├── governance/                    # Enterprise trust, quality & security layer
│   │   ├── data_quality.py            # 40 deterministic DQ rules engine
│   │   ├── decision_governance.py     # Decision safety & human oversight engine
│   │   ├── connected_kpis.py          # Cross-source connected KPI evidence engine
│   │   ├── entitlement_engine.py      # Role-based redaction & field filtering
│   │   ├── persona_engine.py          # Executive vs Technical narrative adapter
│   │   ├── feedback_learning.py       # Bounded context-aware feedback calibration
│   │   ├── telemetry_engine.py        # Latency, model calls & token cost telemetry
│   │   └── sparse_history_engine.py   # Launch product & cold-start baseline fallback
│   ├── analytics/                     # Phase 3A: Deterministic Anomaly Engine (FROZEN)
│   │   ├── event_detector.py          # Statistical baseline calculation
│   │   ├── driver_catalog.py          # 8 Canonical business hypotheses catalog
│   │   ├── driver_generator.py        # Multi-source feature extraction
│   │   ├── evidence_scorer.py         # Temporal & magnitude fit scoring
│   │   ├── contradiction_engine.py    # Evidence conflict detection
│   │   └── driver_ranker.py           # Multi-hypothesis arbitration matrix
│   └── phase3b/                       # Phase 3B: Reasoning, Citations & Validation (FROZEN)
│       ├── engine.py                  # Phase 3B reasoning pipeline coordinator
│       ├── evidence_context.py        # Ground truth-free prompt context builder
│       ├── llm_provider.py            # Native REST HTTP client for Google Gemini
│       ├── mock_reasoning_provider.py # Fast deterministic preview provider
│       └── validator.py               # 10-step deterministic safety gate
│
├── static/                            # Frontend Single Page Application
│   ├── index.html                     # Semantic, accessible UI layout
│   ├── styles.css                     # Flat enterprise SaaS design system
│   └── app.js                         # State controller, citation badges & feedback loop
│
├── tests/                             # 40 Automated unit, regression & governance test suites
└── docs/                              # Detailed engineering specifications & phase reports
```

---

## 6. Cloud & Local Deployment Protocol

### 6.1 Local Native Execution
```bash
# 1. Clone repository
git clone https://github.com/rajukumar-501/signal-story.git
cd signal-story

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch native server
python app.py
# Server starts at http://127.0.0.1:8000
```

### 6.2 Streamlit Community Cloud Execution
Signal Story includes a dedicated, cloud-native Streamlit implementation (`streamlit_app.py`) optimized for zero-configuration deployment:
```bash
streamlit run streamlit_app.py
# Streamlit UI launches at http://localhost:8501
```

---

## 7. Submission Checklist & Release Sign-Off

- [x] Zero API credentials or private keys in repository tracking.
- [x] Ground truth answer keys strictly isolated from runtime execution paths.
- [x] Runtime feedback files (`Data/feedback/`) excluded via `.gitignore`.
- [x] All 8 semantic contracts verified and documented.
- [x] Dual-mode execution (Live Gemini + Offline Preview) operational.
- [x] Local native server (`app.py`) and Cloud application (`streamlit_app.py`) validated.
- [x] Full automated test suite passes with zero regressions.
