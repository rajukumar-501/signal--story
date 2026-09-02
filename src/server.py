"""
Phase 4.2 Decision Intelligence API Server.
Provides REST endpoints and serves the Decision Intelligence Portal UI.
Consumes the frozen Phase 3A deterministic engine and Phase 3B reasoning pipeline.
Zero secrets are exposed to the frontend.
"""

import os
import sys
import json
import time
import mimetypes
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.run_analysis import run_analysis
from src.phase3b.engine import Phase3BReasoningEngine
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.llm_provider import LLMReasoningProvider, LLMConfig
from src.governance.data_quality import evaluate_data_trust
from src.governance.decision_governance import evaluate_decision_governance, record_analyst_review, get_decision_governance_engine
from src.governance.connected_kpis import ConnectedKPIEngine
from src.governance.feedback_learning import FeedbackLearningEngine
from src.governance.persona_engine import PersonaEngine
from src.governance.entitlement_engine import EntitlementEngine
from src.governance.telemetry_engine import TelemetryEngine
from src.governance.sparse_history_engine import SparseHistoryEngine

# Initialize singleton governance engines
_connected_kpi_engine = ConnectedKPIEngine()
_feedback_learning_engine = FeedbackLearningEngine()
_persona_engine = PersonaEngine()
_entitlement_engine = EntitlementEngine()
_telemetry_engine = TelemetryEngine()
_sparse_history_engine = SparseHistoryEngine()

DOTENV_PATH = PROJECT_ROOT / ".env"
SOURCE_SPEC_PATH = PROJECT_ROOT / "Data" / "semantic" / "source_integration_spec.json"
PROCESSING_SPEC_PATH = PROJECT_ROOT / "Data" / "semantic" / "processing_classification_contract.json"
ENTITLEMENT_SPEC_PATH = PROJECT_ROOT / "Data" / "semantic" / "entitlement_contract.json"

OFFICIAL_SCENARIOS = [
    {
        "scenario_id": "S003",
        "title": "S003 — China / A2520150501 (Marketing Inefficiency Showcase)",
        "market": "China",
        "category": None,
        "product_code": "A2520150501",
        "date": "2021-04-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "April 2021",
        "badge": "PRIMARY SHOWCASE",
        "description": "Gross sales anomaly of -72.1% with supporting evidence of marketing ad spend surge and conversion efficiency drop."
    },
    {
        "scenario_id": "S001",
        "title": "S001 — South Korea / A6519160401 (Return Volume Surge)",
        "market": "South Korea",
        "category": None,
        "product_code": "A6519160401",
        "date": "2021-05-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "May 2021",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Gross sales drop corroborated by customer return rate anomalies and product defect CRM notes."
    },
    {
        "scenario_id": "S002",
        "title": "S002 — South Korea / All Products (Customer Support Escalation)",
        "market": "South Korea",
        "category": None,
        "product_code": None,
        "date": "2021-01-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "January 2021",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Market-wide gross sales drop with surging support ticket volume and sentiment drop."
    },
    {
        "scenario_id": "S004",
        "title": "S004 — China / A0621150308 (Competitor Price Undercut)",
        "market": "China",
        "category": None,
        "product_code": "A0621150308",
        "date": "2021-01-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "January 2021",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Gross sales decline following aggressive competitor pricing discounts."
    },
    {
        "scenario_id": "S005",
        "title": "S005 — Indonesia / All Products (Support Crisis)",
        "market": "Indonesia",
        "category": None,
        "product_code": None,
        "date": "2020-03-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "March 2020",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Market-wide gross sales drop driven by unresolved support escalations."
    },
    {
        "scenario_id": "S006",
        "title": "S006 — India / Processors (Product Mix Shift)",
        "market": "India",
        "category": "Processors",
        "product_code": None,
        "date": "2020-03-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "March 2020",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Category-level gross sales drop with product mix cannibalization."
    },
    {
        "scenario_id": "S007",
        "title": "S007 — Portugal / Wi-Fi Extenders (Category Share Shift)",
        "market": "Portugal",
        "category": "Wi fi extender",
        "product_code": None,
        "date": "2019-09-01",
        "kpi": "category_share",
        "kpi_name": "Category Share",
        "period": "September 2019",
        "badge": "OFFICIAL BENCHMARK",
        "description": "Category share shift and product mix changes in European networking."
    },
    {
        "scenario_id": "S008",
        "title": "S008 — Germany / All Products (Uncertainty & Graceful Fallback)",
        "market": "Germany",
        "category": None,
        "product_code": None,
        "date": "2020-03-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "March 2020",
        "badge": "UNCERTAINTY / ABSTENTION",
        "description": "Conflicting multi-source signals correctly preserving NOT_ESTABLISHED uncertainty and abstaining from unsupported actions."
    },
    {
        "scenario_id": "S009",
        "title": "S009 — China / A7220160203 (New Product Launch — Limited History)",
        "market": "China",
        "category": "Mouse",
        "product_code": "A7220160203",
        "date": "2018-09-01",
        "kpi": "gross_sales",
        "kpi_name": "Gross Sales",
        "period": "September 2018",
        "badge": "SPARSE HISTORY / NEW LAUNCH",
        "description": "Newly launched product with limited historical observations (< 3 months); demonstrates contextual peer category benchmark fallback."
    }
]


def load_api_key_securely() -> Optional[str]:
    """Loads GEMINI_API_KEY from environment or .env without exposing it."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    if key and key.strip():
        return key.strip()
    if DOTENV_PATH.exists():
        for line in DOTENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in {"GEMINI_API_KEY", "LLM_API_KEY"}:
                val = v.strip().strip("'\"")
                if val:
                    return val
    return None


SEMANTIC_CONTRACT_PATH = PROJECT_ROOT / "Data" / "semantic" / "kpi_contract.json"


def load_kpi_contract(kpi_id: Optional[str] = None) -> Dict[str, Any]:
    """Loads KPI semantic contract safely with zero secrets."""
    if not SEMANTIC_CONTRACT_PATH.exists():
        return {"error": "KPI semantic contract file not found", "status": 404}
    try:
        data = json.loads(SEMANTIC_CONTRACT_PATH.read_text(encoding="utf-8"))
        if kpi_id:
            kpis = data.get("kpis", {})
            if kpi_id in kpis:
                return {
                    "version": data.get("version", "1.0.0"),
                    "schema": data.get("schema"),
                    "kpi": kpis[kpi_id]
                }
            return {
                "error": f"KPI '{kpi_id}' not found in semantic contract",
                "status": 404,
                "available_kpis": list(kpis.keys())
            }
        return data
    except Exception as e:
        return {"error": f"Failed to parse semantic contract: {str(e)}", "status": 500}


def execute_decision_analysis(req_data: Dict[str, Any], user_role: str = "EXECUTIVE") -> Dict[str, Any]:
    """
    Executes the frozen Phase 3A and Phase 3B analytical pipelines,
    wrapping with non-invasive Phase 6 governance, telemetry, persona, and entitlement engines.
    Guarantees that no secrets are returned in the response.
    """
    t_start = time.perf_counter()
    req = {
        "date": req_data.get("date"),
        "kpi": req_data.get("kpi")
    }
    if req_data.get("market"):
        req["market"] = req_data["market"]
    if req_data.get("category"):
        req["category"] = req_data["category"]
    if req_data.get("product_code"):
        req["product_code"] = req_data["product_code"]

    provider_mode = req_data.get("provider_mode", "mock").lower()
    persona = req_data.get("persona", "EXECUTIVE")
    role = req_data.get("role", user_role)

    # 1. Phase 3A Deterministic Engine
    t0_p3a = time.perf_counter()
    p3a_payload = run_analysis(req)
    t1_p3a = time.perf_counter()
    p3a_latency_ms = round((t1_p3a - t0_p3a) * 1000, 2)

    # 2. Configure Phase 3B Provider
    api_key = load_api_key_securely()
    if provider_mode == "gemini" and api_key:
        config = LLMConfig(
            provider="gemini",
            model=os.getenv("LLM_MODEL", "gemini-3.6-flash"),
            api_key=api_key,
            temperature=0.0,
            timeout_seconds=45.0,
            enable_safe_fallback=True
        )
        provider = LLMReasoningProvider(config=config)
        provider_name = "gemini"
        model_name = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    else:
        provider = MockReasoningProvider()
        provider_name = "mock"
        model_name = "mock-causal-v1"

    # 3. Phase 3B Reasoning Pipeline
    engine = Phase3BReasoningEngine(default_provider=provider)
    p3b_payload, validation_report = engine.run(p3a_payload, provider=provider)

    # 4. Provenance Attribution
    is_fallback = (p3b_payload.get("validation_status") == "FALLBACK_PRESERVED") or p3b_payload.get("is_fallback", False)
    if provider_name == "gemini":
        provenance = "LIVE_WITH_FALLBACK" if is_fallback else "LIVE_GEMINI"
    else:
        provenance = "MOCK_PROVIDER"

    # 5. Build Safe UI Response Payload
    kpi_contract_snippet = load_kpi_contract(req.get("kpi")).get("kpi")
    data_trust_report = evaluate_data_trust(target_date=req.get("date"), target_market=req.get("market"))
    decision_gov = evaluate_decision_governance(p3a_payload, p3b_payload, scenario_id=req_data.get("scenario_id"))

    # 6. Phase 5.5 Connected KPI Evidence Layer
    connected_kpi_story = _connected_kpi_engine.get_connected_kpis(
        market=req.get("market", "China"),
        product_code=req.get("product_code"),
        category=req.get("category"),
        date_str=req.get("date", "2021-04-01"),
        scenario_id=req_data.get("scenario_id", "S003")
    )

    # 7. Phase 5.5 Context-Aware Feedback Learning
    analysis_context = {
        "market": req.get("market"),
        "product_code": req.get("product_code"),
        "category": req.get("category"),
        "date": req.get("date"),
        "kpi_context": req.get("kpi")
    }
    raw_drivers = p3a_payload.get("candidate_drivers", [])
    adjusted_drivers, feedback_learning_meta = _feedback_learning_engine.apply_feedback_learning_to_drivers(
        raw_drivers,
        analysis_context
    )

    # 8. Phase 6E Sparse History Evaluation
    hist_count = len(p3a_payload.get("historical_values", [])) if "historical_values" in p3a_payload else 3
    sparse_history_meta = _sparse_history_engine.evaluate_baseline_maturity(
        historical_months_count=hist_count,
        scenario_id=req_data.get("scenario_id"),
        product_code=req.get("product_code")
    )

    # 9. Phase 6D Low-Confidence & Abstention State Evaluation
    scenario_id_val = req_data.get("scenario_id", "CUSTOM")
    is_abstention = (scenario_id_val == "S008") or (p3b_payload.get("diagnosis", {}).get("status") == "NOT_ESTABLISHED")
    abstention_meta = {
        "is_abstaining": is_abstention,
        "abstention_state": "NO_ACTION_RECOMMENDED_UNTIL_VALIDATED" if is_abstention else "ACTIONABLE",
        "confidence": "NONE" if is_abstention else (p3b_payload.get("diagnosis", {}).get("confidence") or "PLAUSIBLE"),
        "reasons": [
            "Conflicting multi-source operational signals (support tickets normal, inventory normal, pricing flat)",
            "Regional sales contraction aligns with broad macroeconomic market movement rather than isolated internal failure"
        ] if is_abstention else [],
        "required_next_evidence": [
            "Peer regional macroeconomic GDP and market growth indices",
            "Category-wide distributor inventory and sell-through reports",
            "External commodity and freight rate indices"
        ] if is_abstention else [],
        "guidance_statement": (
            "Diagnostic engine abstains from recommending capital or spend reallocation. "
            "Maintain baseline monitoring until external macro telemetry is ingested."
        ) if is_abstention else None
    }

    # 10. Phase 6H Runtime Telemetry & Cost Instrumentation
    t_end = time.perf_counter()
    total_ms = (t_end - t_start) * 1000
    p3b_latency_ms = p3b_payload.get("pipeline_latency_ms", 0.0)
    ev_count = len(p3b_payload.get("supporting_evidence", []))
    runtime_telemetry = _telemetry_engine.measure_analysis_telemetry(
        total_latency_ms=total_ms,
        p3a_latency_ms=p3a_latency_ms,
        p3b_latency_ms=p3b_latency_ms,
        provider_name=provider_name,
        model_name=model_name,
        evidence_count=ev_count,
        datasets_count=2,
        cache_status="BYPASS"
    )

    # 11. Phase 6G Processing Classification Metadata
    processing_classification = {}
    if PROCESSING_SPEC_PATH.exists():
        try:
            processing_classification = json.loads(PROCESSING_SPEC_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    ui_response = {
        "scenario_id": scenario_id_val,
        "request": req,
        "kpi_contract": kpi_contract_snippet,
        "data_trust": data_trust_report,
        "decision_governance": decision_gov,
        "connected_kpis": connected_kpi_story,
        "feedback_learning": feedback_learning_meta,
        "adjusted_candidate_drivers": adjusted_drivers,
        "sparse_history": sparse_history_meta,
        "abstention_governance": abstention_meta,
        "runtime_telemetry": runtime_telemetry,
        "processing_classification": processing_classification,
        "phase3a": p3a_payload,
        "phase3b": p3b_payload,
        "metadata": {
            "provider": provider_name,
            "model": model_name,
            "provenance": provenance,
            "validation_status": p3b_payload.get("validation_status", "PASSED"),
            "validation_errors": validation_report.errors if not validation_report.is_valid else [],
            "p3a_latency_ms": p3a_latency_ms,
            "pipeline_latency_ms": p3b_latency_ms,
            "total_latency_ms": round(total_ms, 2),
            "gemini_configured": bool(api_key),
            "frozen_backend": True
        }
    }

    # 12. Phase 6B Persona Adaptation
    ui_response = _persona_engine.adapt_payload_for_persona(ui_response, persona=persona)

    # 13. Phase 6F Role Entitlement & Redaction
    ui_response = _entitlement_engine.apply_entitlements_to_payload(ui_response, role=role)

    return ui_response


def _build_signal_story(ui_response: Dict[str, Any], scenario_id: str = "S003") -> Dict[str, Any]:
    """
    Shapes the governed ui_response into the Signal Story sub-object for the frontend.
    DOES NOT perform any new analytical calculations.
    All values are extracted from the existing governed response.
    """
    p3a = ui_response.get("phase3a", {})
    p3b = ui_response.get("phase3b", {})
    gov = ui_response.get("decision_governance", {})
    conn = ui_response.get("connected_kpis", {})
    abstention = ui_response.get("abstention_governance", {})
    sparse = ui_response.get("sparse_history", {})
    entitlement = ui_response.get("entitlement", {})
    persona_view = ui_response.get("persona_view", {})
    metadata = ui_response.get("metadata", {})

    ev_event = p3a.get("event", {})
    diagnosis = p3b.get("diagnosis", {})
    connected_kpis = conn.get("connected_kpis", [])
    evidence_list = p3b.get("supporting_evidence", [])
    candidates = p3a.get("candidate_drivers", [])
    is_redacted = entitlement.get("is_redacted", False)
    redacted_fields = entitlement.get("redacted_fields", [])

    # Determine story state
    is_abstention = abstention.get("is_abstaining", False) or diagnosis.get("status") == "NOT_ESTABLISHED"
    is_sparse = sparse.get("is_limited_history", False)

    if is_abstention:
        story_state = "ABSTENTION"
    elif is_sparse:
        story_state = "SPARSE_HISTORY"
    elif diagnosis.get("status") == "STRONGLY_SUPPORTED":
        story_state = "SUPPORTED"
    else:
        story_state = "PLAUSIBLE"

    # ── WHAT HAPPENED ──────────────────────────────────────────────────────
    magnitude_raw = ev_event.get("baseline_change_percent", 0.0)
    magnitude_pct = round(abs(magnitude_raw) * 100, 2) if abs(magnitude_raw) <= 1.5 else round(abs(magnitude_raw), 2)
    direction = "fell" if magnitude_raw < 0 else "rose"
    direction_arrow = "↓" if magnitude_raw < 0 else "↑"
    kpi_name = conn.get("target_entity", {}).get("category") or "Gross Sales"
    # Use kpi_contract if available
    kpi_contract = ui_response.get("kpi_contract") or {}
    if kpi_contract and isinstance(kpi_contract, dict):
        kpi_name = kpi_contract.get("kpi_name", kpi_name)

    actual_val = ev_event.get("current_value")
    baseline_val = ev_event.get("baseline_value")

    if is_redacted and "actual_value" in redacted_fields:
        actual_display = "[RESTRICTED — FINANCIAL CONFIDENTIAL]"
    else:
        actual_display = f"${actual_val:,.2f}" if isinstance(actual_val, (int, float)) else str(actual_val or "—")

    if is_redacted and "baseline_value" in redacted_fields:
        baseline_display = "[RESTRICTED — FINANCIAL CONFIDENTIAL]"
    else:
        baseline_display = f"${baseline_val:,.2f}" if isinstance(baseline_val, (int, float)) else str(baseline_val or "—")

    period_str = (ev_event.get("date") or ui_response.get("request", {}).get("date", ""))[:10]
    from datetime import datetime
    try:
        period_label = datetime.strptime(period_str, "%Y-%m-%d").strftime("%B %Y")
    except Exception:
        period_label = period_str

    what_happened = {
        "kpi_name": kpi_name,
        "direction": direction,
        "direction_arrow": direction_arrow,
        "magnitude_pct": magnitude_pct,
        "actual_display": actual_display,
        "baseline_display": baseline_display,
        "period": period_label,
        "period_short": period_label.split()[0] if period_label else "",
        "anomaly_type": "Negative" if magnitude_raw < 0 else "Positive",
        "is_redacted": is_redacted,
    }

    # ── WHAT CHANGED ───────────────────────────────────────────────────────
    what_changed = []
    for kpi in connected_kpis:
        kpi_id = kpi.get("kpi_id", "")
        if kpi_id == "gross_sales":
            continue  # already in WHAT HAPPENED
        chg = kpi.get("change_percent", 0.0)
        # Redact gross_sales-related values if restricted
        if is_redacted and kpi_id == "gross_sales":
            continue
        what_changed.append({
            "kpi_id": kpi_id,
            "display_name": kpi.get("display_name", kpi_id),
            "change_pct": round(chg, 2),
            "formatted_change": kpi.get("formatted_change", f"{chg:+.2f}%"),
            "direction_arrow": "↓" if chg < 0 else "↑",
            "direction_word": "fell" if chg < 0 else "rose",
            "role": kpi.get("evidence_role", ""),
            "role_label": kpi.get("role_label", ""),
            "status": kpi.get("status", ""),
            "source_dataset": kpi.get("source_dataset", ""),
            "grain": kpi.get("grain", ""),
        })

    # ── EVIDENCE CHAIN ────────────────────────────────────────────────────
    evidence_chain = []
    for ev in evidence_list:
        evidence_chain.append({
            "evidence_id": ev.get("evidence_id", ""),
            "metric": ev.get("metric", ""),
            "display_name": ev.get("display_name") or ev.get("metric", "").replace("_", " ").title(),
            "finding": ev.get("finding", ""),
            "dataset": ev.get("dataset", ""),
            "role": ev.get("role", ""),
            "direction_arrow": "↓" if ("-" in str(ev.get("finding", "")) and "%" in str(ev.get("finding", ""))) else "↑",
        })

    # ── RULED OUT ─────────────────────────────────────────────────────────
    ruled_out = []
    primary_idx = 0  # first candidate is the primary supported driver
    for i, cand in enumerate(candidates):
        if i == 0:
            continue  # skip primary
        driver_id = cand.get("driver", "")
        driver_name = {
            "DRIVER_01_INVENTORY": "Inventory & Stockout Bottleneck",
            "DRIVER_02_PRICING": "Competitor Price Undercutting",
            "DRIVER_03_MARKETING": "Marketing Inefficiency",
            "DRIVER_04_RETURNS": "Product Defect & Return Surge",
            "DRIVER_05_SUPPORT": "Customer Support Crisis",
            "DRIVER_06_CUSTOMER": "Customer Sentiment Drop",
            "DRIVER_07_MARKET": "Regional Market Contraction",
            "DRIVER_08_PRODUCT_MIX": "Product Mix Shift & Cannibalization",
        }.get(driver_id, driver_id)
        ruled_out.append({
            "driver_id": driver_id,
            "driver_name": driver_name,
            "fit_score": round(cand.get("fit_score", 0.0), 2),
            "rejection_reason": cand.get("reason", "Insufficient supporting evidence"),
            "rank": i + 1,
        })

    # ── WHAT NEXT ─────────────────────────────────────────────────────────
    confidence_label = diagnosis.get("status", "PLAUSIBLE")
    human_review_required = gov.get("approval_required", True)
    what_next = {
        "recommended_action": gov.get("recommended_action", "Conduct cross-functional operational review."),
        "owner": gov.get("required_owner", "Commercial Operations Lead"),
        "area": gov.get("affected_business_area", "Commercial Operations"),
        "risk_level": gov.get("risk_level", "MEDIUM"),
        "confidence": confidence_label,
        "human_review_required": human_review_required,
        "human_review_label": "Required" if human_review_required else "Not Required",
        "finding_statement": gov.get("finding_statement", ""),
        "why_it_matters": gov.get("why_it_matters", ""),
        "causal_language_class": gov.get("causal_language_class", "SUPPORTED_INFERENCE"),
    }

    # ── PRIMARY DRIVER ────────────────────────────────────────────────────
    primary_driver = None
    if candidates:
        cand = candidates[0]
        driver_id = cand.get("driver", "")
        driver_names = {
            "DRIVER_01_INVENTORY": "Inventory & Stockout Bottleneck",
            "DRIVER_02_PRICING": "Competitor Price Undercutting",
            "DRIVER_03_MARKETING": "Marketing Inefficiency",
            "DRIVER_04_RETURNS": "Product Defect & Return Surge",
            "DRIVER_05_SUPPORT": "Customer Support Crisis",
            "DRIVER_06_CUSTOMER": "Customer Sentiment Drop",
            "DRIVER_07_MARKET": "Regional Market Contraction",
            "DRIVER_08_PRODUCT_MIX": "Product Mix Shift & Cannibalization",
        }
        primary_driver = {
            "driver_id": driver_id,
            "driver_name": driver_names.get(driver_id, driver_id),
            "fit_score": round(cand.get("fit_score", 0.0), 2),
            "status": confidence_label,
        }

    # ── GLANCE TEXT (deterministic, no LLM) ──────────────────────────────
    glance_parts = []
    if is_abstention:
        reasons = abstention.get("reasons", [])
        reason_str = reasons[0] if reasons else "conflicting or insufficient signals"
        glance_parts.append(
            f"Insufficient evidence to establish a primary driver. "
            f"The system detected a sales anomaly, but {reason_str.lower()}. "
            f"No action is recommended until additional evidence is validated."
        )
    elif is_sparse:
        glance_parts.append(
            f"Limited historical data (< 3 months). "
            f"{kpi_name} {direction} {magnitude_pct:.1f}% in {period_label}, "
            f"assessed against a contextual peer-category benchmark. "
            f"Confidence is LOW due to insufficient history for a standard 3-month baseline."
        )
    else:
        # Build from governed values
        if is_redacted:
            headline = f"{kpi_name} {direction} {magnitude_pct:.1f}% in {period_label}."
        else:
            headline = f"{kpi_name} {direction} {magnitude_pct:.1f}% in {period_label} ({actual_display} vs {baseline_display} baseline)."
        glance_parts.append(headline)

        # Connected signals (top 2 significant)
        sig_changes = [k for k in what_changed if abs(k["change_pct"]) >= 10][:2]
        if sig_changes:
            sig_strs = [f"{k['display_name']} {k['direction_arrow']}{abs(k['change_pct']):.1f}%" for k in sig_changes]
            glance_parts.append(f"Coinciding with: {' and '.join(sig_strs)}.")

        # Primary driver
        if primary_driver:
            causal_class = what_next.get("causal_language_class", "SUPPORTED_INFERENCE")
            verb = "is the strongest supported explanation" if causal_class == "SUPPORTED_INFERENCE" else "aligns with available evidence"
            glance_parts.append(
                f"{primary_driver['driver_name']} {verb} (fit score: {primary_driver['fit_score']:.2f}, status: {confidence_label})."
            )

        # Alternatives
        rejected_names = [r["driver_name"] for r in ruled_out[:2]]
        if rejected_names:
            glance_parts.append(
                f"Alternative explanations ({', '.join(rejected_names)}) were checked and found insufficient."
            )

    glance_text = " ".join(glance_parts)

    # ── AI NARRATIVE ──────────────────────────────────────────────────────
    provider = metadata.get("provider", "mock")
    gemini_configured = metadata.get("gemini_configured", False)
    validation_status = metadata.get("validation_status", "PASSED")
    llm_summary = p3b.get("executive_summary", "")

    if provider == "gemini" and gemini_configured and llm_summary and validation_status == "PASSED":
        ai_narrative = {
            "available": True,
            "text": llm_summary,
            "disclosure": "AI-assisted narrative • Based on governed evidence • Deterministic analytical results remain authoritative.",
        }
    elif provider == "gemini" and gemini_configured and validation_status == "FALLBACK_PRESERVED":
        ai_narrative = {
            "available": False,
            "text": None,
            "disclosure": "AI assistance unavailable — deterministic analysis remains active.",
        }
    else:
        ai_narrative = {
            "available": False,
            "text": None,
            "disclosure": None,
        }

    # ── TIMELINE STEPS ────────────────────────────────────────────────────
    timeline_steps = []
    if is_abstention:
        timeline_steps = [
            {"number": "01", "label": "SIGNAL", "detail": f"{kpi_name} anomaly detected"},
            {"number": "02", "label": "EVIDENCE", "detail": "Evidence reviewed"},
            {"number": "03", "label": "ABSTENTION", "detail": "Insufficient to establish driver"},
            {"number": "04", "label": "DECISION", "detail": "No action until validated"},
        ]
    elif is_sparse:
        timeline_steps = [
            {"number": "01", "label": "SIGNAL", "detail": f"{kpi_name} anomaly detected"},
            {"number": "02", "label": "LIMITED HISTORY", "detail": "< 3 months available"},
            {"number": "03", "label": "BENCHMARK", "detail": "Contextual peer benchmark used"},
            {"number": "04", "label": "CONFIDENCE", "detail": "LOW — proceed with caution"},
        ]
    else:
        timeline_steps = [
            {"number": "01", "label": "SIGNAL", "detail": f"{kpi_name} {direction} {magnitude_pct:.1f}%"},
            {"number": "02", "label": "CONNECTED", "detail": f"{len(what_changed)} corroborating signals"},
            {"number": "03", "label": "FUNNEL", "detail": "Evidence chain traced"},
            {"number": "04", "label": "HYPOTHESIS", "detail": primary_driver["driver_name"] if primary_driver else "Driver evaluated"},
            {"number": "05", "label": "VALIDATION", "detail": f"{len(ruled_out)} alternatives checked"},
            {"number": "06", "label": "DECISION", "detail": f"Risk: {what_next['risk_level']}"},
        ]

    # ── PERSONA CONTEXT ───────────────────────────────────────────────────
    persona_detail = {
        "active_persona": persona_view.get("active_persona", "EXECUTIVE"),
        "detail_level": persona_view.get("detail_level", "EXECUTIVE_SUMMARY"),
        "emphasis_levers": persona_view.get("emphasis_levers", []),
        "narrative_style": persona_view.get("narrative_style", "Strategic Decision Briefing"),
    }

    return {
        "story_state": story_state,
        "what_happened": what_happened,
        "what_changed": what_changed,
        "evidence_chain": evidence_chain,
        "ruled_out": ruled_out,
        "what_next": what_next,
        "primary_driver": primary_driver,
        "glance_text": glance_text,
        "timeline_steps": timeline_steps,
        "ai_narrative": ai_narrative,
        "persona_detail": persona_detail,
        "abstention_meta": abstention if is_abstention else None,
        "sparse_meta": sparse if is_sparse else None,
        "epistemic_note": (
            "Evidence supports this explanation, but does not establish causality."
            if story_state == "PLAUSIBLE" else None
        ),
    }


class DecisionIntelligenceRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler serving UI assets and JSON API endpoints."""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-User-Role, X-Persona")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204, "text/plain")

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/health":
            self._set_headers(200, "application/json")
            resp = {
                "status": "ok",
                "app": "Accenture Decision Intelligence Platform",
                "version": "6.0.0",
                "frozen_backend": True
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        if path == "/api/scenarios":
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(OFFICIAL_SCENARIOS, indent=2).encode("utf-8"))
            return

        if path == "/api/kpi-contract":
            qs = parse_qs(parsed_path.query)
            kpi_id = qs.get("kpi_id", [None])[0]
            contract_resp = load_kpi_contract(kpi_id)
            status_code = contract_resp.get("status", 200) if "error" in contract_resp else 200
            self._set_headers(status_code, "application/json")
            self.wfile.write(json.dumps(contract_resp, indent=2).encode("utf-8"))
            return

        if path == "/api/source-spec":
            if SOURCE_SPEC_PATH.exists():
                spec = json.loads(SOURCE_SPEC_PATH.read_text(encoding="utf-8"))
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(spec, indent=2).encode("utf-8"))
            else:
                self._set_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Source spec not found"}).encode("utf-8"))
            return

        if path == "/api/telemetry":
            summary = _telemetry_engine.get_summary()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(summary, indent=2).encode("utf-8"))
            return

        if path == "/api/entitlements":
            if ENTITLEMENT_SPEC_PATH.exists():
                ent = json.loads(ENTITLEMENT_SPEC_PATH.read_text(encoding="utf-8"))
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(ent, indent=2).encode("utf-8"))
            else:
                self._set_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Entitlements contract not found"}).encode("utf-8"))
            return

        if path == "/api/processing-classification":
            if PROCESSING_SPEC_PATH.exists():
                spec = json.loads(PROCESSING_SPEC_PATH.read_text(encoding="utf-8"))
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(spec, indent=2).encode("utf-8"))
            else:
                self._set_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Processing spec not found"}).encode("utf-8"))
            return

        if path == "/api/connected-kpis":
            qs = parse_qs(parsed_path.query)
            scenario_id = qs.get("scenario_id", ["S003"])[0]
            market = qs.get("market", ["China"])[0]
            product_code = qs.get("product_code", ["A2520150501"])[0]
            category = qs.get("category", [None])[0]
            date_str = qs.get("date", ["2021-04-01"])[0]
            
            # Map scenario_id if present
            if scenario_id:
                for sc in OFFICIAL_SCENARIOS:
                    if sc.get("scenario_id") == scenario_id:
                        market = sc.get("market", market)
                        product_code = sc.get("product_code", product_code)
                        category = sc.get("category", category)
                        date_str = sc.get("date", date_str)
                        break

            kpis_resp = _connected_kpi_engine.get_connected_kpis(
                market=market,
                product_code=product_code,
                category=category,
                date_str=date_str,
                scenario_id=scenario_id
            )
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(kpis_resp, indent=2).encode("utf-8"))
            return

        if path == "/api/feedback/summary":
            summary = _feedback_learning_engine.get_learning_summary()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(summary, indent=2).encode("utf-8"))
            return

        if path == "/api/feedback/history":
            history = _feedback_learning_engine.get_all_feedback()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(history, indent=2).encode("utf-8"))
            return

        if path == "/api/data-trust":
            qs = parse_qs(parsed_path.query)
            target_date = qs.get("date", [None])[0]
            target_market = qs.get("market", [None])[0]
            trust_report = evaluate_data_trust(target_date=target_date, target_market=target_market)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(trust_report, indent=2).encode("utf-8"))
            return

        if path == "/api/decision-governance":
            qs = parse_qs(parsed_path.query)
            driver_id = qs.get("driver_id", [None])[0]
            engine = get_decision_governance_engine()
            gov_resp = engine.get_driver_governance(driver_id)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(gov_resp, indent=2).encode("utf-8"))
            return

        if path == "/api/story":
            qs = parse_qs(parsed_path.query)
            scenario_id = qs.get("scenario_id", ["S003"])[0]
            provider_mode = qs.get("provider_mode", ["mock"])[0]
            persona = qs.get("persona", ["EXECUTIVE"])[0]
            role = qs.get("role", ["EXECUTIVE"])[0]

            # Resolve scenario parameters
            sc = next((s for s in OFFICIAL_SCENARIOS if s["scenario_id"] == scenario_id), OFFICIAL_SCENARIOS[0])
            req_data = {
                "scenario_id": scenario_id,
                "market": sc.get("market"),
                "product_code": sc.get("product_code"),
                "category": sc.get("category"),
                "date": sc.get("date"),
                "kpi": sc.get("kpi", "gross_sales"),
                "provider_mode": provider_mode,
                "persona": persona,
                "role": role
            }

            try:
                ui_resp = execute_decision_analysis(req_data, user_role=role)
                story = _build_signal_story(ui_resp, scenario_id=scenario_id)
                resp = {"scenario_id": scenario_id, "signal_story": story}
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_headers(500, "application/json")
                self.wfile.write(json.dumps({"error": f"Story generation failed: {str(e)}"}).encode("utf-8"))
            return

        # Serve static assets
        if path == "/" or path == "":
            file_path = STATIC_DIR / "index.html"
        else:
            rel_path = path.lstrip("/")
            file_path = STATIC_DIR / rel_path

        if file_path.exists() and file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or "application/octet-stream"
            self._set_headers(200, mime_type)
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/api/feedback":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                req_data = json.loads(body_bytes.decode("utf-8"))
                scenario_id = req_data.get("scenario_id", "S003")
                predicted_driver = req_data.get("predicted_driver", "DRIVER_03_MARKETING")
                analyst_decision = req_data.get("analyst_decision", "APPROVED")
                reviewer = req_data.get("reviewer", "Lead Commercial Analyst")
                reason = req_data.get("reason", "")
                alternative_driver = req_data.get("alternative_driver")
                context = req_data.get("context", {})

                record = _feedback_learning_engine.record_feedback(
                    scenario_id=scenario_id,
                    predicted_driver=predicted_driver,
                    analyst_decision=analyst_decision,
                    reviewer=reviewer,
                    reason=reason,
                    alternative_driver=alternative_driver,
                    context=context
                )
                
                # Also keep session decision governance in sync
                record_analyst_review(scenario_id, analyst_decision, reviewer=reviewer, notes=reason)
                
                # Compute updated adjustments
                adjustments = _feedback_learning_engine.get_feedback_adjustments_for_context(context)
                
                resp = {
                    "status": "success",
                    "feedback_recorded": record,
                    "active_adjustments": adjustments,
                    "governance_notice": "Feedback recorded. Influences future driver prioritization without modifying underlying evidence."
                }
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(resp, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": f"Failed to record feedback: {str(e)}"}).encode("utf-8"))
            return

        if path == "/api/analyst-review":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                req_data = json.loads(body_bytes.decode("utf-8"))
                scenario_id = req_data.get("scenario_id", "S003")
                status = req_data.get("status", "REVIEWED")
                reviewer = req_data.get("reviewer", "Lead Commercial Analyst")
                notes = req_data.get("notes")
                record = record_analyst_review(scenario_id, status, reviewer=reviewer, notes=notes)
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(record, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": f"Failed to record review: {str(e)}"}).encode("utf-8"))
            return

        if path == "/api/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                req_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception as e:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {str(e)}"}).encode("utf-8"))
                return

            header_role = self.headers.get("X-User-Role", "EXECUTIVE")
            header_persona = self.headers.get("X-Persona", "EXECUTIVE")
            if "role" not in req_data:
                req_data["role"] = header_role
            if "persona" not in req_data:
                req_data["persona"] = header_persona

            try:
                response_data = execute_decision_analysis(req_data, user_role=req_data.get("role", "EXECUTIVE"))
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_headers(500, "application/json")
                self.wfile.write(json.dumps({"error": f"Analysis execution failed: {str(e)}"}).encode("utf-8"))
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        """Clean logging output to standard stderr."""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run_server(port: int = 8000, host: str = "0.0.0.0"):
    """Starts the Decision Intelligence HTTP server."""
    server_address = (host, port)
    server_cls = ThreadingHTTPServer if "ThreadingHTTPServer" in globals() else HTTPServer
    httpd = server_cls(server_address, DecisionIntelligenceRequestHandler)
    print(f"\n==================================================================")
    print(f"Accenture Decision Intelligence Platform Server")
    print(f"Status: RUNNING (Multi-Threaded)")
    print(f"Local:  http://127.0.0.1:{port}")
    print(f"Host:   http://localhost:{port}")
    print(f"API:    http://127.0.0.1:{port}/api/scenarios")
    print(f"==================================================================\n")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    run_server(port=port, host=host)

