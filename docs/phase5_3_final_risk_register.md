# Phase 5.3 — Final Risk Register

## 1. Executive Summary
This risk register identifies potential evaluation questions, technical vulnerabilities, and operational assumptions for **Signal Story** in the context of the Accenture Innovation Challenge.

---

## 2. Comprehensive Risk Matrix

| Risk ID | Risk Description | Severity | Likelihood | Impact | Current Prototype Mitigation | Live Demo Mitigation Strategy | Production Enterprise Mitigation |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **RSK-01** | **Evaluator Questions Causal Proof**: Judge asks whether the model proved mathematical causality or merely found temporal correlations. | `HIGH` | `HIGH` | `MEDIUM` | Strict causal language precision. System uses *"strongest supported explanation"*, *"evidence indicates"*, and explicitly disclaims A/B experimental proof. | Emphasize multi-dataset corroboration across independent domains and point out the transparent observational disclaimer in View 1 & View 3. | Implement automated Quasi-Experimental Causal Inference (Difference-in-Differences / Synthetic Controls). |
| **RSK-02** | **Live LLM API Latency / Rate Limits**: Live Gemini API request experiences network latency or upstream rate limiting during presentation. | `HIGH` | `MEDIUM` | `HIGH` | Dual-mode architecture with offline `MockReasoningProvider` fallback (0ms latency, 100% deterministic grounding). | Use toggle button in header to switch between "Assisted Analysis" (Live Gemini) and "Preview" (Offline Fast Engine). | Provision dedicated LLM inference endpoints with auto-scaling and Redis response caching. |
| **RSK-03** | **Data Staleness Question**: Judge asks why the warehouse data ends in August 2021. | `MEDIUM` | `MEDIUM` | `LOW` | Explicit temporal horizon modeling in Phase 5.2B (`data_trust_contract.json` & `data_quality.py`). | Explain that the historical accounting dataset covers 36 consecutive monthly accounting close partitions (2018–2021) for full baseline comparisons. | Implement automated CDC (Change Data Capture) pipelines from live ERP systems. |
| **RSK-04** | **Unsafe Autonomous Execution**: Judge questions whether the AI might execute harmful changes (e.g. cutting brand marketing or canceling orders) without human review. | `HIGH` | `MEDIUM` | `HIGH` | Phase 5.2D Decision Actionability & Safety Layer (`decision_action_contract.json`) enforcing `REQUIRES_HUMAN_APPROVAL` and "Before Acting" checklists. | Demonstrate the interactive Analyst Review Bar (`[Approve]`, `[Reject]`, `[Request Evidence]`) and emphasize human-in-the-loop governance. | Implement multi-signature authorization workflows and automated rollback webhooks. |
| **RSK-05** | **Over-fitting Demo Bias on S003**: Judge wonders if the platform only works on Scenario S003 (China Marketing). | `MEDIUM` | `LOW` | `MEDIUM` | All 8 benchmark scenarios (S001–S008) are fully functional in the dropdown, tested with 41 unit tests. | Switch live between S003 (Marketing), S001 (Returns), and S008 (Inconclusive / Uncertainty Preserved). | Continuously ingest multi-market telemetry across all global business units. |
| **RSK-06** | **Secret / API Key Leakage**: Exposure of Gemini API credentials in frontend payloads or GitHub repository. | `CRITICAL`| `LOW` | `CRITICAL`| Server-side environment isolation in `.env`; `tests/test_phase5_2d_decision_governance.py` validates zero secrets in all API responses. | Automated CI test confirms 0 credentials in git commits or response headers. | Enterprise Vault / AWS Secrets Manager integration with ephemeral token rotation. |
| **RSK-07** | **Scalability Beyond In-Memory Pandas**: Judge asks how the system handles 100M+ rows across global divisions. | `LOW` | `MEDIUM` | `LOW` | Clear architectural documentation in `phase5_2c_data_gap_inspection.md` specifying current in-memory scope (~1.3M rows) vs warehouse pushdown. | Explain the pushdown SQL architecture to BigQuery / Snowflake / ClickHouse. | Implement direct dbt / SQL pushdown queries with aggregated OLAP cube caching. |

---

## 3. Risk Summary & Mitigation Health
* **Critical Risks**: 0 Unmitigated.
* **High Severity Risks**: 3 (RSK-01 Causal Phrasing, RSK-02 API Latency, RSK-04 Autonomous Safety) — **100% Mitigated by Phase 5.2D Governance and Dual-Mode Fallback**.
* **Overall Assessment**: **SUBMISSION-READY & SAFE FOR LIVE EVALUATION**.
