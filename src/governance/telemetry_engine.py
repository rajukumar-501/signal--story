"""
Runtime Telemetry & Cost Instrumentation Engine (Phase 6H).
Measures real request latency, deterministic vs LLM processing time,
model calls, token counts, and estimated cost per decision insight.
"""

import time
from typing import Dict, Any, Optional

# Standard Pricing per 1M tokens
MODEL_PRICING = {
    "gemini-1.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-2.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gpt-4o-mini": {"input_per_m": 0.15, "output_per_m": 0.60}
}


class TelemetryEngine:
    """Instruments and records runtime performance, latency, and cost telemetry."""

    def __init__(self):
        self.session_requests = 0
        self.total_latency_sum_ms = 0.0
        self.total_cost_usd = 0.0
        self.history = []

    def measure_analysis_telemetry(
        self,
        total_latency_ms: float,
        p3a_latency_ms: float,
        p3b_latency_ms: float,
        provider_name: str,
        model_name: str,
        evidence_count: int,
        datasets_count: int = 2,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cache_status: str = "BYPASS"
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive runtime telemetry payload for an analysis execution.
        """
        deterministic_latency_ms = round(p3a_latency_ms + max(0.0, total_latency_ms - p3a_latency_ms - p3b_latency_ms), 2)
        llm_latency_ms = round(p3b_latency_ms, 2)
        is_live_llm = provider_name in ["gemini", "openai"] and llm_latency_ms > 0

        # Token metrics
        if input_tokens is not None and output_tokens is not None:
            token_display_in = input_tokens
            token_display_out = output_tokens
            total_tokens = input_tokens + output_tokens
            
            # Compute cost
            rates = MODEL_PRICING.get(model_name, {"input_per_m": 0.075, "output_per_m": 0.30})
            cost = (input_tokens / 1_000_000.0 * rates["input_per_m"]) + (output_tokens / 1_000_000.0 * rates["output_per_m"])
            cost_display = f"${cost:.6f}"
            cost_val = round(cost, 6)
        else:
            token_display_in = "UNAVAILABLE FROM PROVIDER"
            token_display_out = "UNAVAILABLE FROM PROVIDER"
            total_tokens = "UNAVAILABLE FROM PROVIDER"
            cost_display = "$0.000000 (MOCK_MODE)" if not is_live_llm else "UNAVAILABLE FROM PROVIDER"
            cost_val = 0.0

        telemetry = {
            "total_latency_ms": round(total_latency_ms, 2),
            "deterministic_latency_ms": deterministic_latency_ms,
            "llm_latency_ms": llm_latency_ms,
            "llm_calls_count": 1 if is_live_llm else 0,
            "provider": provider_name,
            "model": model_name,
            "input_tokens": token_display_in,
            "output_tokens": token_display_out,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost_display,
            "evidence_records_evaluated": evidence_count,
            "datasets_queried_count": datasets_count,
            "cache_status": cache_status,
            "measured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # Track session aggregates
        self.session_requests += 1
        self.total_latency_sum_ms += total_latency_ms
        self.total_cost_usd += cost_val
        self.history.append(telemetry)
        if len(self.history) > 100:
            self.history.pop(0)

        return telemetry

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregate session telemetry metrics for GET /api/telemetry."""
        avg_latency = round(self.total_latency_sum_ms / max(1, self.session_requests), 2)
        return {
            "total_requests_served": self.session_requests,
            "average_latency_ms": avg_latency,
            "total_estimated_cost_usd": round(self.total_cost_usd, 6),
            "recent_executions_count": len(self.history),
            "recent_history": self.history[-10:]
        }
