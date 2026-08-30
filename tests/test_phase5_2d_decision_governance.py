"""
Phase 5.2D — Decision Actionability, Operational Safety & Human Oversight Test Suite.
Tests deterministic decision governance evaluation, risk tiers, action safety classifications,
preconditions, causal language precision, human-in-the-loop review state machine,
API endpoints, secret isolation, and frozen analytical core immutability.
"""

import unittest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.governance.decision_governance import (
    DecisionGovernanceEngine,
    evaluate_decision_governance,
    record_analyst_review,
    get_decision_governance_engine
)
from src.server import execute_decision_analysis


class TestPhase52DDecisionGovernance(unittest.TestCase):
    """Decision governance and action safety test suite for Phase 5.2D."""

    def setUp(self):
        self.engine = DecisionGovernanceEngine()

    def test_01_marketing_driver_governance_specification(self):
        """DRIVER_03_MARKETING must map to MEDIUM risk and require human approval."""
        gov = self.engine.get_driver_governance("DRIVER_03_MARKETING")
        self.assertEqual(gov["driver_id"], "DRIVER_03_MARKETING")
        self.assertEqual(gov["risk_level"], "MEDIUM")
        self.assertIn(gov["safety_classification"], {"REQUIRES_VALIDATION", "REQUIRES_HUMAN_APPROVAL"})
        self.assertTrue(gov["approval_required"])
        self.assertGreaterEqual(len(gov["prerequisites"]), 3)
        self.assertGreaterEqual(len(gov["operational_risks"]), 2)
        self.assertEqual(gov["causal_language_class"], "SUPPORTED_INFERENCE")

    def test_02_return_driver_high_risk(self):
        """DRIVER_01_RETURN must map to HIGH risk with QA ownership."""
        gov = self.engine.get_driver_governance("DRIVER_01_RETURN")
        self.assertEqual(gov["risk_level"], "HIGH")
        self.assertEqual(gov["safety_classification"], "REQUIRES_HUMAN_APPROVAL")
        self.assertIn("QA", gov["required_owner"])

    def test_03_inconclusive_driver_safety(self):
        """DRIVER_08_INCONCLUSIVE must map to DO_NOT_EXECUTE_AUTOMATICALLY."""
        gov = self.engine.get_driver_governance("DRIVER_08_INCONCLUSIVE")
        self.assertEqual(gov["safety_classification"], "DO_NOT_EXECUTE_AUTOMATICALLY")
        self.assertEqual(gov["causal_language_class"], "INCONCLUSIVE_OBSERVATION")
        self.assertEqual(gov["risk_level"], "LOW")

    def test_04_evaluate_decision_governance_s003(self):
        """evaluate_decision_governance for S003 diagnosis must generate precision causal finding."""
        mock_p3a = {"event": {"kpi": "gross_sales", "date": "2021-04-01"}}
        mock_p3b = {
            "diagnosis": {"driver": "DRIVER_03_MARKETING", "status": "STRONGLY_SUPPORTED"},
            "executive_summary": "Marketing ad spend increased while conversion deteriorated."
        }
        res = self.engine.evaluate_decision_governance(mock_p3a, mock_p3b, scenario_id="S003")
        self.assertEqual(res["driver_id"], "DRIVER_03_MARKETING")
        self.assertEqual(res["risk_level"], "MEDIUM")
        self.assertIn("strongest supported explanation", res["finding_statement"])
        self.assertIn("governance_disclaimer", res)

    def test_05_inconclusive_scenario_evaluation(self):
        """Inconclusive diagnosis must preserve uncertainty and advise against localized action."""
        mock_p3a = {"event": {"kpi": "gross_sales", "date": "2020-03-01"}}
        mock_p3b = {
            "diagnosis": {"driver": None, "status": "NOT_ESTABLISHED"}
        }
        res = self.engine.evaluate_decision_governance(mock_p3a, mock_p3b, scenario_id="S008")
        self.assertEqual(res["driver_id"], "DRIVER_08_INCONCLUSIVE")
        self.assertEqual(res["safety_classification"], "DO_NOT_EXECUTE_AUTOMATICALLY")
        self.assertIn("no single internal operational driver", res["finding_statement"])

    def test_06_human_review_state_transitions(self):
        """Analyst review state machine must record APPROVED, REVIEWED, REJECTED, NEEDS_MORE_EVIDENCE."""
        r1 = record_analyst_review("S003", "APPROVED", reviewer="Senior Commercial VP", notes="Approved budget shift")
        self.assertEqual(r1["status"], "APPROVED")
        self.assertEqual(r1["reviewer"], "Senior Commercial VP")

        r2 = record_analyst_review("S004", "NEEDS_MORE_EVIDENCE", notes="Need competitor elasticity model")
        self.assertEqual(r2["status"], "NEEDS_MORE_EVIDENCE")

        mock_p3a = {"event": {"kpi": "gross_sales"}}
        mock_p3b = {"diagnosis": {"driver": "DRIVER_03_MARKETING", "status": "STRONGLY_SUPPORTED"}}
        res = evaluate_decision_governance(mock_p3a, mock_p3b, scenario_id="S003")
        self.assertEqual(res["human_review"]["status"], "APPROVED")

    def test_07_api_analyze_embeds_decision_governance(self):
        """POST /api/analyze response must include decision_governance object without breaking contract."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        self.assertIn("decision_governance", res)
        gov = res["decision_governance"]
        self.assertEqual(gov["driver_id"], "DRIVER_03_MARKETING")
        self.assertEqual(gov["risk_level"], "MEDIUM")
        self.assertIn("prerequisites", gov)
        self.assertIn("operational_risks", gov)
        self.assertIn("human_review", gov)

    def test_08_zero_secrets_exposure(self):
        """Decision governance payload must not contain any API credentials."""
        gov = self.engine.get_driver_governance("DRIVER_03_MARKETING")
        gov_str = json.dumps(gov)
        self.assertNotIn("GEMINI_API_KEY", gov_str)
        self.assertNotIn("AIzaSy", gov_str)

    def test_09_s003_analytical_outcome_immutability(self):
        """S003 analytical output must remain 100% frozen and unmodified."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        ev = res["phase3a"]["event"]
        diag = res["phase3b"]["diagnosis"]

        self.assertAlmostEqual(ev["change_percent"], -0.72056, places=4)
        self.assertEqual(diag["driver"], "DRIVER_03_MARKETING")
        self.assertIn(diag["status"], {"STRONGLY_SUPPORTED", "PLAUSIBLE"})
        actual_val = ev.get("current_value") if "current_value" in ev else ev.get("actual_value")
        self.assertAlmostEqual(actual_val, 994.25, places=2)
        self.assertAlmostEqual(ev["baseline_value"], 3558.03, places=2)


if __name__ == "__main__":
    unittest.main()
