"""
Phase 4.2 Decision Intelligence UI & API Integration Tests.
Verifies API endpoints, S003 data contract, multi-source evidence mapping,
uncertainty handling, fallback preservation, secret protection, and error boundaries.
"""

import unittest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.server import OFFICIAL_SCENARIOS, execute_decision_analysis


class TestPhase4DecisionAPI(unittest.TestCase):
    """Unit and integration tests for Phase 4.2 API layer."""

    def test_01_scenario_catalog_integrity(self):
        """Official scenario catalog must contain all 8 scenarios with S003 as primary showcase."""
        self.assertEqual(len(OFFICIAL_SCENARIOS), 8)
        scenario_ids = [s["scenario_id"] for s in OFFICIAL_SCENARIOS]
        self.assertIn("S003", scenario_ids)
        self.assertIn("S001", scenario_ids)
        self.assertIn("S008", scenario_ids)

        s003 = next(s for s in OFFICIAL_SCENARIOS if s["scenario_id"] == "S003")
        self.assertEqual(s003["market"], "China")
        self.assertEqual(s003["product_code"], "A2520150501")
        self.assertEqual(s003["badge"], "PRIMARY SHOWCASE")

    def test_02_execute_s003_analysis(self):
        """S003 execution through the real backend must return valid Phase 3A and 3B payloads."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)

        self.assertIn("phase3a", res)
        self.assertIn("phase3b", res)
        self.assertIn("metadata", res)

        # Verify Phase 3A Anomaly
        ev = res["phase3a"]["event"]
        self.assertEqual(ev["kpi"], "gross_sales")
        self.assertAlmostEqual(ev["change_percent"], -0.72056, places=4)

        # Verify Phase 3B Diagnosis
        diag = res["phase3b"]["diagnosis"]
        self.assertEqual(diag["driver"], "DRIVER_03_MARKETING")
        self.assertIn(diag["status"], {"STRONGLY_SUPPORTED", "PLAUSIBLE"})

    def test_03_evidence_structure_and_citations(self):
        """Phase 3B response must contain valid supporting evidence and claim-level citations."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        p3b = res["phase3b"]

        # Supporting Evidence
        supporting = p3b.get("supporting_evidence", [])
        self.assertGreater(len(supporting), 0)
        for ev_item in supporting:
            self.assertTrue(ev_item["evidence_id"].startswith("EVD-"))
            self.assertTrue(bool(ev_item["source_dataset"]))

        # Claims & Grounding
        claims = p3b.get("claims", [])
        self.assertGreater(len(claims), 0)
        for c in claims:
            self.assertIn(c["claim_type"], {"OBSERVATION", "INTERPRETATION", "CAUSAL_CONCLUSION", "RECOMMENDATION"})
            self.assertIsInstance(c["evidence_ids"], list)

    def test_04_arbitration_comparisons_present(self):
        """Candidate arbitration matrix must compare all investigated drivers."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        comparisons = res["phase3b"].get("candidate_comparisons", [])
        self.assertGreater(len(comparisons), 0)

        top_comp = comparisons[0]
        self.assertIn("scope_alignment", top_comp)
        self.assertIn("temporal_alignment", top_comp)
        self.assertIn("contradiction_count", top_comp)

    def test_05_uncertainty_and_fallback_preservation_s008(self):
        """S008 uncertainty scenario must preserve NOT_ESTABLISHED and null established driver."""
        req = {
            "scenario_id": "S008",
            "market": "Germany",
            "date": "2020-03-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        diag = res["phase3b"]["diagnosis"]

        self.assertIsNone(diag.get("driver"))
        self.assertEqual(diag.get("status"), "NOT_ESTABLISHED")

    def test_06_api_secret_isolation(self):
        """API response must never expose GEMINI_API_KEY or secret credentials."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        res_str = json.dumps(res)

        self.assertNotIn("AIzaSy", res_str)
        self.assertNotIn("GEMINI_API_KEY", res_str)
        self.assertNotIn("LLM_API_KEY", res_str)
        self.assertNotIn("secret", res_str.lower())

    def test_07_actionable_recommendations_present(self):
        """Phase 3B response must supply structured, actionable next steps."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        actions = res["phase3b"].get("recommended_next_steps", [])
        self.assertIsInstance(actions, list)
        self.assertGreater(len(actions), 0)


if __name__ == "__main__":
    unittest.main()
