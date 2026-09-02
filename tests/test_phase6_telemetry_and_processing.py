"""
Unit Tests for Phase 6G (LLM vs Non-LLM Processing Breakdown) and Phase 6H (Runtime Telemetry).
Verifies instrumentation of execution latencies, token/cost estimation,
and non-LLM mathematical governance guarantees.
"""

import unittest
from pathlib import Path
from src.governance.telemetry_engine import TelemetryEngine
from src.server import execute_decision_analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase6TelemetryAndProcessing(unittest.TestCase):
    """Tests for Telemetry Engine and Processing Classification."""

    def setUp(self):
        self.telemetry = TelemetryEngine()

    def test_telemetry_measurement_mock_mode(self):
        """Verifies runtime telemetry measurement in mock offline mode."""
        res = self.telemetry.measure_analysis_telemetry(
            total_latency_ms=25.4,
            p3a_latency_ms=10.2,
            p3b_latency_ms=5.0,
            provider_name="mock",
            model_name="mock-causal-v1",
            evidence_count=2,
            datasets_count=2
        )
        self.assertEqual(res["total_latency_ms"], 25.4)
        self.assertEqual(res["provider"], "mock")
        self.assertEqual(res["llm_calls_count"], 0)
        self.assertEqual(res["input_tokens"], "UNAVAILABLE FROM PROVIDER")
        self.assertIn("MOCK_MODE", res["estimated_cost_usd"])
        self.assertEqual(res["evidence_records_evaluated"], 2)

    def test_telemetry_measurement_with_tokens(self):
        """Verifies runtime telemetry cost calculation when tokens are provided."""
        res = self.telemetry.measure_analysis_telemetry(
            total_latency_ms=350.0,
            p3a_latency_ms=15.0,
            p3b_latency_ms=300.0,
            provider_name="gemini",
            model_name="gemini-1.5-flash",
            evidence_count=2,
            datasets_count=2,
            input_tokens=1200,
            output_tokens=300
        )
        self.assertEqual(res["llm_calls_count"], 1)
        self.assertEqual(res["input_tokens"], 1200)
        self.assertEqual(res["output_tokens"], 300)
        self.assertEqual(res["total_tokens"], 1500)
        self.assertTrue(res["estimated_cost_usd"].startswith("$0.000"))

    def test_processing_classification_contract_integrity(self):
        """Verifies processing classification contract guarantees non-LLM mathematical truth."""
        req_data = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        resp = execute_decision_analysis(req_data)

        self.assertIn("processing_classification", resp)
        pc = resp["processing_classification"]
        self.assertEqual(pc.get("version"), "1.0.0")
        stages = pc.get("pipeline_stages", [])
        self.assertEqual(len(stages), 8)

        # Check that math / anomaly / data quality / safety are strictly NON_LLM
        non_llm_stage_ids = [s["stage_id"] for s in stages if s["classification"] == "NON_LLM"]
        self.assertIn("STAGE_01_ANOMALY_DETECTION", non_llm_stage_ids)
        self.assertIn("STAGE_02_CANDIDATE_GENERATION", non_llm_stage_ids)
        self.assertIn("STAGE_03_MULTI_SOURCE_JOIN", non_llm_stage_ids)
        self.assertIn("STAGE_04_DATA_QUALITY", non_llm_stage_ids)
        self.assertIn("STAGE_06_SAFETY_GATE", non_llm_stage_ids)
        self.assertIn("STAGE_07_FEEDBACK_CALIBRATION", non_llm_stage_ids)


if __name__ == "__main__":
    unittest.main()
