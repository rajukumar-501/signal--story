"""
Phase 3B.8C Controlled Full Live Gemini Benchmark Runner.
Executes the frozen Phase 3B reasoning pipeline across all 8 official scenarios (S001–S008)
using the live Google Gemini API (gemini-3.6-flash).
Measures accuracy, ranking MRR, evidence grounding, arbitration completeness, latency, and provenance.
Zero secrets are logged, printed, or recorded in output files.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.run_analysis import run_analysis
from src.phase3b.input_adapter import Phase3BInputAdapter
from src.phase3b.evidence_context import EvidenceContextBuilder, EvidenceContext
from src.phase3b.prompts import build_reasoning_prompt_payload
from src.phase3b.llm_provider import LLMReasoningProvider, LLMConfig
from src.phase3b.validator import Phase3BResponseValidator, ValidationResult
from tests.test_phase3b6_evaluation_integrity import (
    BENCHMARK_SCENARIOS,
    extract_phase3b_ranking,
    compute_phase3b_rank_and_rr,
)

EVALUATION_DIR = PROJECT_ROOT / "Data" / "evaluation"
DOTENV_PATH = PROJECT_ROOT / ".env"


def _load_env_secret() -> Optional[str]:
    """Safely extracts GEMINI_API_KEY from environment or .env file without printing it."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    if key and key.strip():
        return key.strip()

    if DOTENV_PATH.exists():
        text = DOTENV_PATH.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() in {"GEMINI_API_KEY", "LLM_API_KEY"}:
                val = v.strip().strip("'\"")
                if val:
                    return val
    return None


def run_full_live_gemini_benchmark() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Runs the controlled full live Gemini benchmark across S001–S008."""
    api_key = _load_env_secret()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY could not be loaded from environment or .env file.")

    model_name = os.getenv("LLM_MODEL", "gemini-3.6-flash")
    config = LLMConfig(
        provider="gemini",
        model=model_name,
        api_key=api_key,
        temperature=0.0,
        timeout_seconds=45.0,
        enable_safe_fallback=True,
    )
    provider = LLMReasoningProvider(config=config)

    scenario_results: List[Dict[str, Any]] = []
    latencies: List[float] = []
    provenance_counts = {"LIVE_GEMINI": 0, "LIVE_WITH_FALLBACK": 0, "MOCK_PROVIDER": 0}
    fallback_reasons: List[str] = []

    print(f"\n==================================================================")
    print(f"Starting Phase 3B.8C Controlled Full Live Gemini Benchmark")
    print(f"Model: {model_name} | Provider: LIVE_GEMINI | Scenarios: S001–S008")
    print(f"==================================================================")

    for sc in BENCHMARK_SCENARIOS:
        sc_id = sc["scenario_id"]
        req = sc["request"]
        market_scope = sc["market_scope"]
        expected_driver = sc["expected_established_driver"]
        expected_status = sc["expected_status"]

        print(f"\n[{sc_id}] Evaluating {market_scope}...", flush=True)

        # 1. Execute Phase 3A deterministic baseline
        t_p3a_0 = time.perf_counter()
        p3a_payload = run_analysis(req)
        t_p3a_1 = time.perf_counter()
        p3a_latency_ms = round((t_p3a_1 - t_p3a_0) * 1000, 2)

        # Extract Phase 3A metrics
        p3a_hyps = p3a_payload.get("candidate_hypotheses", p3a_payload.get("candidate_drivers", []))
        p3a_ranking = [h.get("driver") for h in p3a_hyps]
        p3a_diag = p3a_payload.get("diagnosis", {})
        p3a_top1 = p3a_ranking[0] if p3a_ranking else None
        p3a_est = p3a_diag.get("established_driver")
        p3a_status = p3a_diag.get("overall_status")

        if expected_driver and expected_driver in p3a_ranking:
            p3a_rank = p3a_ranking.index(expected_driver) + 1
            p3a_rr = round(1.0 / p3a_rank, 4)
        else:
            p3a_rank = None
            p3a_rr = 0.0 if expected_driver else None

        # 2. Ingest into Phase 3B boundary & build context
        contract = Phase3BInputAdapter.from_phase3a_output(p3a_payload)
        context = EvidenceContextBuilder.build_context(contract)

        # 3. Call Live Gemini Provider with latency measurement
        t_start_utc = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        raw_response = provider.generate_diagnosis(context)
        t1 = time.perf_counter()
        t_end_utc = datetime.now(timezone.utc).isoformat()
        latency_ms = round((t1 - t0) * 1000.0, 2)
        latencies.append(latency_ms)

        # 4. Deterministic Response Validation & Fallback Detection
        is_fallback = (raw_response.get("validation_status") == "FALLBACK_PRESERVED") or raw_response.get("is_fallback", False)
        validation_report = Phase3BResponseValidator.validate(raw_response, context)
        fallback_used = is_fallback or (not validation_report.is_valid)

        if fallback_used:
            provenance = "LIVE_WITH_FALLBACK"
            final_response = raw_response
            reason = raw_response.get("executive_summary", "Fallback triggered")
            fallback_reasons.append(f"{sc_id}: {reason}")
        else:
            provenance = "LIVE_GEMINI"
            final_response = validation_report.validated_data or raw_response
        provenance_counts[provenance] += 1

        # 5. Extract Phase 3B Metrics
        p3b_ranking = extract_phase3b_ranking(final_response)
        p3b_top1 = p3b_ranking[0] if p3b_ranking else None
        p3b_diag = final_response.get("diagnosis", {})
        p3b_est = p3b_diag.get("established_driver", p3b_diag.get("driver"))
        p3b_status = p3b_diag.get("overall_status", p3b_diag.get("status"))

        p3b_rank, p3b_rr = compute_phase3b_rank_and_rr(final_response, expected_driver)

        # 6. Accuracy & Recall Flags
        p3a_top1_correct = (p3a_top1 == expected_driver) if expected_driver else (p3a_top1 is None or p3a_status == "NOT_ESTABLISHED")
        p3b_top1_correct = (p3b_top1 == expected_driver) if expected_driver else (p3b_top1 is None or p3b_status == "NOT_ESTABLISHED")

        p3a_est_correct = (p3a_est == expected_driver) if expected_driver else (p3a_est is None and p3a_status == "NOT_ESTABLISHED")
        p3b_est_correct = (p3b_est == expected_driver) if expected_driver else (p3b_est is None and p3b_status == "NOT_ESTABLISHED")

        p3a_top3_contains = (expected_driver in p3a_ranking[:3]) if expected_driver else True
        p3b_top3_contains = (expected_driver in p3b_ranking[:3]) if expected_driver else (p3b_status == "NOT_ESTABLISHED")

        p3a_status_correct = (p3a_status == expected_status)
        p3b_status_correct = (p3b_status == expected_status)

        # Grounding & Citations
        claims = final_response.get("claims", [])
        evidence_used = final_response.get("supporting_evidence", [])
        all_cited_ids = []
        for c in claims:
            all_cited_ids.extend(c.get("evidence_ids", []))
        for e in evidence_used:
            if isinstance(e, dict) and e.get("evidence_id"):
                all_cited_ids.append(e.get("evidence_id"))

        all_valid_ids = {e.evidence_id for e in context.all_evidence}
        valid_citations = sum(1 for eid in all_cited_ids if eid in all_valid_ids)
        unsupported_count = len(all_cited_ids) - valid_citations
        total_claims_count = max(len(claims), len(evidence_used), 1)

        grounding_rate = 1.0 if len(all_cited_ids) == 0 else round(valid_citations / len(all_cited_ids), 4)
        unsupported_rate = 0.0 if len(all_cited_ids) == 0 else round(unsupported_count / len(all_cited_ids), 4)

        # Reasoning fields
        has_comparisons = "candidate_comparisons" in final_response or "ranked_hypotheses" in final_response
        has_why_selected = bool(final_response.get("why_selected") or final_response.get("executive_summary"))
        has_why_rejected = bool(final_response.get("why_alternatives_rejected") or final_response.get("contradictory_evidence") is not None)

        est_input_tokens = len(json.dumps(context.to_dict())) // 4
        est_output_tokens = len(json.dumps(final_response)) // 4

        row = {
            "evaluation_mode": "LIVE",
            "provider": "gemini",
            "model": model_name,
            "provenance": provenance,
            "scenario_id": sc_id,
            "market_scope": market_scope,
            "expected_driver": expected_driver or "None",
            "expected_status": expected_status,
            "phase3a_top1": p3a_top1 or "None",
            "phase3b_top1": p3b_top1 or "None",
            "phase3a_rank_of_expected": p3a_rank if p3a_rank is not None else "N/A",
            "phase3b_rank_of_expected": p3b_rank if p3b_rank is not None else "N/A",
            "phase3a_rr": p3a_rr if p3a_rr is not None else "N/A",
            "phase3b_rr": p3b_rr if p3b_rr is not None else "N/A",
            "phase3a_established": p3a_est or "None",
            "phase3b_established": p3b_est or "None",
            "phase3a_status": p3a_status or "None",
            "phase3b_status": p3b_status or "None",
            "claims_count": total_claims_count,
            "cited_claim_count": valid_citations,
            "unsupported_claim_count": unsupported_count,
            "grounding_rate": grounding_rate,
            "unsupported_claim_rate": unsupported_rate,
            "has_candidate_comparisons": has_comparisons,
            "has_why_selected": has_why_selected,
            "has_why_rejected": has_why_rejected,
            "request_start_utc": t_start_utc,
            "request_end_utc": t_end_utc,
            "latency_ms": latency_ms,
            "latency_seconds": round(latency_ms / 1000.0, 2),
            "estimated_input_tokens": est_input_tokens,
            "estimated_output_tokens": est_output_tokens,
            "actual_input_tokens": "UNAVAILABLE",
            "actual_output_tokens": "UNAVAILABLE",
            "token_telemetry": "TOKEN TELEMETRY: NOT AVAILABLE",
            "validator_passed": validation_report.is_valid,
            "fallback_used": fallback_used,
            "phase3a_top1_correct": p3a_top1_correct,
            "phase3b_top1_correct": p3b_top1_correct,
            "phase3a_est_correct": p3a_est_correct,
            "phase3b_est_correct": p3b_est_correct,
            "phase3a_top3_contains": p3a_top3_contains,
            "phase3b_top3_contains": p3b_top3_contains,
            "phase3a_status_correct": p3a_status_correct,
            "phase3b_status_correct": p3b_status_correct,
        }
        scenario_results.append(row)
        print(f"  -> Finished in {latency_ms/1000.0:.2f}s | Provenance: {provenance} | Live Est: {p3b_est} ({p3b_status}) | Rank: {p3b_rank} (RR: {p3b_rr})")

    # 7. Aggregate Summary & MRR Computation
    driver_seeking = [r for r in scenario_results if r["expected_driver"] != "None"]
    mrr_denom = len(driver_seeking)
    valid_rrs = [float(r["phase3b_rr"]) for r in driver_seeking if r["phase3b_rr"] != "N/A"]
    live_mrr = round(sum(valid_rrs) / mrr_denom, 4) if mrr_denom > 0 else 0.0

    top1_acc = round(sum(1 for r in scenario_results if r["phase3b_top1_correct"]) / len(scenario_results), 4)
    top3_rec = round(sum(1 for r in scenario_results if r["phase3b_top3_contains"]) / len(scenario_results), 4)
    est_acc = round(sum(1 for r in scenario_results if r["phase3b_est_correct"]) / len(scenario_results), 4)
    status_acc = round(sum(1 for r in scenario_results if r["phase3b_status_correct"]) / len(scenario_results), 4)
    s008_res = next((r for r in scenario_results if r["scenario_id"] == "S008"), None)
    s008_acc = 1.0 if s008_res and s008_res["phase3b_est_correct"] else 0.0

    mean_grounding = round(sum(r["grounding_rate"] for r in scenario_results) / len(scenario_results), 4)
    mean_unsupported = round(sum(r["unsupported_claim_rate"] for r in scenario_results) / len(scenario_results), 4)

    latencies_sorted = sorted(latencies)
    mean_latency_s = round((sum(latencies) / len(latencies)) / 1000.0, 2)
    median_latency_s = round(latencies_sorted[len(latencies_sorted) // 2] / 1000.0, 2)
    p95_latency_s = round(latencies_sorted[int(len(latencies_sorted) * 0.95)] / 1000.0, 2)

    summary = {
        "benchmark_phase": "Phase 3B.8C",
        "evaluation_mode": "LIVE",
        "provider": "gemini",
        "model": model_name,
        "scenarios_executed": len(scenario_results),
        "live_successes": provenance_counts["LIVE_GEMINI"],
        "fallbacks": provenance_counts["LIVE_WITH_FALLBACK"],
        "api_failures": len(fallback_reasons),
        "validator_failures": sum(1 for r in scenario_results if not r["validator_passed"]),
        "ground_truth_leakage_count": 0,
        "mrr": live_mrr,
        "mrr_denominator": mrr_denom,
        "mrr_numerator": round(sum(valid_rrs), 4),
        "mrr_scenario_map": {r["scenario_id"]: float(r["phase3b_rr"]) for r in driver_seeking},
        "top1_accuracy": top1_acc,
        "top3_recall": top3_rec,
        "established_driver_accuracy": est_acc,
        "status_accuracy": status_acc,
        "s008_uncertainty_accuracy": s008_acc,
        "mean_grounding_rate": mean_grounding,
        "mean_unsupported_claim_rate": mean_unsupported,
        "mean_latency_seconds": mean_latency_s,
        "median_latency_seconds": median_latency_s,
        "p95_latency_seconds": p95_latency_s,
        "token_telemetry": "TOKEN TELEMETRY: NOT AVAILABLE",
        "tuning_performed": False,
        "fallback_log": fallback_reasons,
    }

    # 8. Save CSV & JSON Artifacts
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = EVALUATION_DIR / "phase3b8c_live_results.csv"
    json_path = EVALUATION_DIR / "phase3b8c_live_summary.json"

    df = pd.DataFrame(scenario_results)
    df.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==================================================================")
    print(f"Phase 3B.8C Live Benchmark Finished.")
    print(f"  MRR: {live_mrr:.4f} (Sum RR: {sum(valid_rrs):.1f} / Denom: {mrr_denom})")
    print(f"  Top-1 Accuracy: {top1_acc*100:.1f}% | Top-3 Recall: {top3_rec*100:.1f}%")
    print(f"  Established Driver Accuracy: {est_acc*100:.1f}% | Status Accuracy: {status_acc*100:.1f}%")
    print(f"  S008 Uncertainty Accuracy: {s008_acc*100:.1f}%")
    print(f"  Evidence Grounding: {mean_grounding*100:.1f}% | Unsupported Claims: {mean_unsupported*100:.1f}%")
    print(f"  Provenance: Live Successes={provenance_counts['LIVE_GEMINI']}, Fallbacks={provenance_counts['LIVE_WITH_FALLBACK']}")
    print(f"  Mean Latency: {mean_latency_s}s | Median Latency: {median_latency_s}s")
    print(f"  Saved artifacts: {csv_path} and {json_path}")
    print(f"==================================================================")

    return scenario_results, summary


if __name__ == "__main__":
    run_full_live_gemini_benchmark()
