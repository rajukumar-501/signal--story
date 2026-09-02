"""
Unit Tests for Phase 6D (Low-Confidence Abstention) and Phase 6E (Sparse History & New Launch).
Verifies detection of insufficient evidence, graceful abstention without aggressive recommendations,
and explicit fallback baseline methods for newly launched entities.
"""

import unittest
from pathlib import Path
from src.governance.sparse_history_engine import SparseHistoryEngine
from src.server import execute_decision_analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase6AbstentionAndSparseHistory(unittest.TestCase):
    """Tests for Abstention and Sparse History engines."""

    def setUp(self):
        self.sparse_engine = SparseHistoryEngine()

    def test_sparse_history_mature_baseline(self):
        """Verifies that entities with >= 3 historical months receive MATURE_HISTORY status."""
        res = self.sparse_engine.evaluate_baseline_maturity(historical_months_count=3, scenario_id="S003")
        self.assertFalse(res["is_sparse_history"])
        self.assertEqual(res["baseline_status"], "MATURE_HISTORY")
        self.assertEqual(res["baseline_confidence"], "HIGH")
        self.assertFalse(res["fallback_applied"])

    def test_sparse_history_limited_history(self):
        """Verifies that new launches with < 3 months receive LIMITED_HISTORY status with contextual baseline."""
        res = self.sparse_engine.evaluate_baseline_maturity(historical_months_count=1, scenario_id="S009", product_code="A7220160203")
        self.assertTrue(res["is_sparse_history"])
        self.assertEqual(res["baseline_status"], "LIMITED_HISTORY")
        self.assertEqual(res["baseline_confidence"], "LOW")
        self.assertTrue(res["fallback_applied"])
        self.assertIn("Peer Product Category Benchmark", res["baseline_method"])

    def test_s008_abstention_scenario_in_server(self):
        """Verifies that scenario S008 correctly triggers abstention governance and avoids unsupported actions."""
        req_data = {
            "scenario_id": "S008",
            "market": "Germany",
            "date": "2020-03-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        resp = execute_decision_analysis(req_data)

        self.assertIn("abstention_governance", resp)
        ag = resp["abstention_governance"]
        self.assertTrue(ag["is_abstaining"])
        self.assertEqual(ag["abstention_state"], "NO_ACTION_RECOMMENDED_UNTIL_VALIDATED")
        self.assertEqual(ag["confidence"], "NONE")
        self.assertGreater(len(ag["reasons"]), 0)
        self.assertGreater(len(ag["required_next_evidence"]), 0)

    def test_s009_sparse_history_scenario_in_server(self):
        """Verifies that scenario S009 correctly discloses sparse history in server response."""
        req_data = {
            "scenario_id": "S009",
            "market": "China",
            "product_code": "A7220160203",
            "category": "Mouse",
            "date": "2018-09-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        resp = execute_decision_analysis(req_data)

        self.assertIn("sparse_history", resp)
        sh = resp["sparse_history"]
        self.assertTrue(sh["is_sparse_history"])
        self.assertEqual(sh["baseline_status"], "LIMITED_HISTORY")
        self.assertEqual(sh["baseline_confidence"], "LOW")


if __name__ == "__main__":
    unittest.main()
