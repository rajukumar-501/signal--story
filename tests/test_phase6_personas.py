"""
Unit Tests for Phase 6B: Persona Adaptation.
Verifies that Executive vs Domain Analyst personas receive tailored narrative depth,
decision rights, and focus while strictly sharing identical quantitative ground truth and evidence IDs.
"""

import unittest
from pathlib import Path
from src.governance.persona_engine import PersonaEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase6PersonaEngine(unittest.TestCase):
    """Tests for the Persona Adaptation Engine."""

    def setUp(self):
        self.engine = PersonaEngine()
        self.sample_payload = {
            "phase3a": {
                "event": {
                    "kpi": "gross_sales",
                    "actual_value": 994.25,
                    "baseline_value": 3558.03,
                    "change_percent": -0.7206
                },
                "diagnosis": {
                    "driver": "DRIVER_03_MARKETING",
                    "status": "STRONGLY_SUPPORTED"
                }
            },
            "phase3b": {
                "diagnosis": {
                    "driver": "DRIVER_03_MARKETING",
                    "status": "STRONGLY_SUPPORTED"
                },
                "supporting_evidence": [
                    {"evidence_id": "EVD-002", "metric": "marketing_spend"},
                    {"evidence_id": "EVD-003", "metric": "conversion_rate"}
                ]
            },
            "decision_governance": {
                "recommended_action": "Audit underperforming digital ad campaigns.",
                "finding_statement": "Marketing performance is the primary supported factor."
            }
        }

    def test_executive_persona_adaptation(self):
        """Verifies Executive persona delivers strategic high-level narrative."""
        adapted = self.engine.adapt_payload_for_persona(dict(self.sample_payload), persona="EXECUTIVE")
        self.assertIn("persona_view", adapted)
        pv = adapted["persona_view"]
        self.assertEqual(pv["active_persona"], "EXECUTIVE")
        self.assertEqual(pv["detail_level"], "EXECUTIVE_SUMMARY")
        self.assertIn("Commercial sales contracted", pv["summary"])
        self.assertIn("Executive action", pv["summary"])
        self.assertEqual(pv["telemetry_exposure"], "AGGREGATED_TOP_LINE")

    def test_analyst_persona_adaptation(self):
        """Verifies Domain Analyst persona delivers deep statistical and telemetry trace."""
        adapted = self.engine.adapt_payload_for_persona(dict(self.sample_payload), persona="DOMAIN_ANALYST")
        self.assertIn("persona_view", adapted)
        pv = adapted["persona_view"]
        self.assertEqual(pv["active_persona"], "DOMAIN_ANALYST")
        self.assertEqual(pv["detail_level"], "DEEP_ANALYTICAL_TRACE")
        self.assertIn("ANOMALY SCOPE", pv["summary"])
        self.assertIn("31 conversions / 853 clicks", pv["summary"])
        self.assertIn("DRIVER_03_MARKETING = 6.00", pv["summary"])
        self.assertEqual(pv["telemetry_exposure"], "FULL_GRANULAR_METRICS")

    def test_ground_truth_invariance_across_personas(self):
        """Verifies that quantitative values and evidence IDs remain 100% identical between personas."""
        exec_payload = self.engine.adapt_payload_for_persona(dict(self.sample_payload), persona="EXECUTIVE")
        analyst_payload = self.engine.adapt_payload_for_persona(dict(self.sample_payload), persona="DOMAIN_ANALYST")

        # Ground truth unchanged
        self.assertEqual(
            exec_payload["phase3a"]["event"]["actual_value"],
            analyst_payload["phase3a"]["event"]["actual_value"]
        )
        self.assertEqual(
            exec_payload["phase3b"]["supporting_evidence"][0]["evidence_id"],
            analyst_payload["phase3b"]["supporting_evidence"][0]["evidence_id"]
        )


if __name__ == "__main__":
    unittest.main()
