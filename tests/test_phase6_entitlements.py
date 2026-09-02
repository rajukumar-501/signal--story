"""
Unit Tests for Phase 6F: Role-Based Security & Entitlements.
Verifies access rights, data redaction of sensitive financial values,
and permission gating for Executive, Domain Analyst, and Restricted User roles.
"""

import unittest
from pathlib import Path
from src.governance.entitlement_engine import EntitlementEngine
from src.server import execute_decision_analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase6Entitlements(unittest.TestCase):
    """Tests for the Entitlement Engine and Role-Based Redaction."""

    def setUp(self):
        self.engine = EntitlementEngine()
        self.sample_payload = {
            "phase3a": {
                "event": {
                    "actual_value": 994.25,
                    "baseline_value": 3558.03
                }
            },
            "connected_kpis": {
                "connected_kpis": [
                    {"kpi_id": "gross_sales", "formatted_value": "$994.25", "formatted_change": "-72.1%"},
                    {"kpi_id": "marketing_spend", "formatted_value": "$1,641.07", "formatted_change": "+64.9%"}
                ]
            },
            "decision_governance": {
                "recommended_action": "Audit underperforming digital ad campaigns.",
                "finding_statement": "Marketing performance is primary."
            }
        }

    def test_executive_role_permissions(self):
        """Verifies Executive role has full access and action approval authority."""
        adapted = self.engine.apply_entitlements_to_payload(dict(self.sample_payload), role="EXECUTIVE")
        self.assertIn("entitlement", adapted)
        ent = adapted["entitlement"]
        self.assertEqual(ent["active_role"], "EXECUTIVE")
        self.assertFalse(ent["is_redacted"])
        self.assertTrue(ent["approval_authorized"])
        self.assertEqual(adapted["phase3a"]["event"]["actual_value"], 994.25)

    def test_domain_analyst_role_permissions(self):
        """Verifies Domain Analyst role has full telemetry access but review-only permissions."""
        adapted = self.engine.apply_entitlements_to_payload(dict(self.sample_payload), role="DOMAIN_ANALYST")
        self.assertIn("entitlement", adapted)
        ent = adapted["entitlement"]
        self.assertEqual(ent["active_role"], "DOMAIN_ANALYST")
        self.assertFalse(ent["is_redacted"])
        self.assertFalse(ent["approval_authorized"])

    def test_restricted_user_redaction(self):
        """Verifies Restricted User role has sensitive financial numbers redacted."""
        adapted = self.engine.apply_entitlements_to_payload(dict(self.sample_payload), role="RESTRICTED_USER")
        self.assertIn("entitlement", adapted)
        ent = adapted["entitlement"]
        self.assertEqual(ent["active_role"], "RESTRICTED_USER")
        self.assertTrue(ent["is_redacted"])
        self.assertFalse(ent["approval_authorized"])

        # Check redacted numbers
        self.assertEqual(adapted["phase3a"]["event"]["actual_value"], "[RESTRICTED - FINANCIAL CONFIDENTIAL]")
        self.assertEqual(adapted["connected_kpis"]["connected_kpis"][0]["formatted_value"], "[RESTRICTED]")
        self.assertIn("[RESTRICTED", adapted["decision_governance"]["recommended_action"])

    def test_server_role_redaction_integration(self):
        """Verifies that execute_decision_analysis redacts responses when requested with RESTRICTED_USER."""
        req_data = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "role": "RESTRICTED_USER"
        }
        resp = execute_decision_analysis(req_data)
        self.assertEqual(resp["entitlement"]["active_role"], "RESTRICTED_USER")
        self.assertEqual(resp["phase3a"]["event"]["actual_value"], "[RESTRICTED - FINANCIAL CONFIDENTIAL]")


if __name__ == "__main__":
    unittest.main()
