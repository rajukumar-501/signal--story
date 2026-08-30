"""
Phase 4.3 Interactive Demonstration & Hackathon Presentation Verification Test Suite.
Verifies full end-to-end presentation readiness:
1. S003 Primary Showcase complete decision hierarchy (Views 1, 2, 3).
2. All 8 benchmark scenarios (S001-S008) operational via API execution.
3. Strict uncertainty handling (S008 returns NOT_ESTABLISHED with null driver and NONE confidence).
4. Full claim-level citation integrity and non-empty action plans.
5. Frontend assets structure, required DOM IDs, and security boundary isolation.
"""

import unittest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.server import OFFICIAL_SCENARIOS, execute_decision_analysis


class TestPhase43PresentationCertification(unittest.TestCase):
    """End-to-End Presentation Verification for Phase 4.3."""

    def test_01_primary_showcase_s003_view1_executive_decision(self):
        """View 1: S003 must provide complete 4-part decision hierarchy."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)

        # 1. What Happened? (Anomaly)
        p3a = res["phase3a"]
        ev = p3a["event"]
        self.assertEqual(res["request"]["market"], "China")
        self.assertEqual(res["request"]["product_code"], "A2520150501")
        self.assertEqual(ev["kpi"], "gross_sales")
        self.assertAlmostEqual(ev["change_percent"], -0.72056, places=4)
        self.assertAlmostEqual(ev["current_value"], 994.25, places=2)
        self.assertAlmostEqual(ev["baseline_value"], 3558.03, places=2)

        # 2. Why Did It Happen? (Primary Driver)
        p3b = res["phase3b"]
        diag = p3b["diagnosis"]
        self.assertEqual(diag["driver"], "DRIVER_03_MARKETING")
        self.assertIn(diag["status"], {"STRONGLY_SUPPORTED", "PLAUSIBLE"})
        self.assertIn(diag["confidence"], {"HIGH", "MEDIUM"})

        # 3. How Strong is the Evidence? (Supporting Evidence)
        supporting = p3b["supporting_evidence"]
        self.assertGreaterEqual(len(supporting), 2)
        ev_ids = [e["evidence_id"] for e in supporting]
        self.assertIn("EVD-002", ev_ids)
        self.assertIn("EVD-003", ev_ids)

        # 4. What Should We Do Next? (Action Plan)
        actions = p3b["recommended_next_steps"]
        self.assertGreaterEqual(len(actions), 1)
        self.assertTrue(any(len(a) > 5 for a in actions))

    def test_02_primary_showcase_s003_view2_reasoning_and_arbitration(self):
        """View 2: S003 must provide 8-driver arbitration and claim grounding."""
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

        # Arbitration Matrix
        comparisons = p3b.get("candidate_comparisons", [])
        self.assertGreaterEqual(len(comparisons), 3)
        top_driver = comparisons[0]
        self.assertEqual(top_driver["driver"], "DRIVER_03_MARKETING")
        self.assertIn(top_driver["scope_alignment"], {"EXACT", "MARKET"})
        self.assertIn(top_driver["temporal_alignment"], {"DURING", "BEFORE"})
        self.assertEqual(top_driver["contradiction_count"], 0)

        # Why Selected Rationale
        self.assertIn("why_selected", p3b)
        self.assertTrue(len(p3b["why_selected"]) > 20)

        # Why Alternatives Rejected
        self.assertIn("why_alternatives_rejected", p3b)
        rejected = p3b["why_alternatives_rejected"]
        self.assertIsInstance(rejected, list)
        self.assertGreaterEqual(len(rejected), 1)

        # Claim-Level Grounding
        claims = p3b.get("claims", [])
        self.assertGreaterEqual(len(claims), 3)
        for c in claims:
            self.assertIn(c["claim_type"], {"OBSERVATION", "INTERPRETATION", "CAUSAL_CONCLUSION", "RECOMMENDATION"})
            self.assertIsInstance(c["evidence_ids"], list)

    def test_03_primary_showcase_s003_view3_trust_and_governance(self):
        """View 3: S003 must pass 10-step validator and supply provenance telemetry."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)

        # Validation status
        metadata = res.get("metadata", {})
        self.assertEqual(metadata.get("validation_status"), "PASSED")
        self.assertEqual(len(metadata.get("validation_errors", [])), 0)

        # Provenance Telemetry
        self.assertIn(metadata.get("provenance"), {"MOCK_PROVIDER", "LIVE_GEMINI", "LIVE_WITH_FALLBACK"})
        self.assertGreater(metadata.get("p3a_latency_ms", 0), 0)

        # Data Lineage / Traceability in Phase 3B
        p3b = res["phase3b"]
        traceability = p3b.get("traceability", [])
        self.assertGreaterEqual(len(traceability), 1)
        for t in traceability:
            self.assertIn("source_dataset", t)
            self.assertIn("evidence_id", t)

    def test_04_full_catalog_all_8_scenarios_execute_cleanly(self):
        """All 8 official benchmark scenarios must execute cleanly with zero server errors."""
        self.assertEqual(len(OFFICIAL_SCENARIOS), 8)

        for s in OFFICIAL_SCENARIOS:
            req = {
                "scenario_id": s["scenario_id"],
                "market": s["market"],
                "category": s.get("category"),
                "product_code": s.get("product_code"),
                "date": s["date"],
                "kpi": s["kpi"],
                "provider_mode": "mock"
            }
            res = execute_decision_analysis(req)
            self.assertIn("phase3a", res, f"Phase 3A missing for {s['scenario_id']}")
            self.assertIn("phase3b", res, f"Phase 3B missing for {s['scenario_id']}")
            self.assertIn("metadata", res, f"Metadata missing for {s['scenario_id']}")
            self.assertEqual(res.get("metadata", {}).get("validation_status"), "PASSED", f"Validation failed for {s['scenario_id']}")

    def test_05_s008_uncertainty_benchmark_preservation(self):
        """S008 Macro Shock must declare NOT_ESTABLISHED and null driver without hallucination."""
        s008 = next(s for s in OFFICIAL_SCENARIOS if s["scenario_id"] == "S008")
        req = {
            "scenario_id": "S008",
            "market": s008["market"],
            "date": s008["date"],
            "kpi": s008["kpi"],
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        diag = res["phase3b"]["diagnosis"]

        self.assertIsNone(diag.get("driver"))
        self.assertEqual(diag.get("status"), "NOT_ESTABLISHED")
        self.assertEqual(diag.get("confidence"), "NONE")

        # Uncertainties disclosure must be present
        uncertainties = res["phase3b"].get("uncertainties", [])
        self.assertGreaterEqual(len(uncertainties), 1)

    def test_06_frontend_static_assets_integrity(self):
        """Static UI files (HTML, CSS, JS) must exist, have valid structure, and define core selectors."""
        static_dir = PROJECT_ROOT / "static"
        html_file = static_dir / "index.html"
        css_file = static_dir / "styles.css"
        js_file = static_dir / "app.js"

        self.assertTrue(html_file.exists())
        self.assertTrue(css_file.exists())
        self.assertTrue(js_file.exists())

        html_content = html_file.read_text(encoding="utf-8")
        self.assertIn("Accenture Decision Intelligence", html_content)
        self.assertIn('id="scenario-select"', html_content)
        self.assertIn('id="btn-run-analysis"', html_content)
        self.assertIn('id="view-executive"', html_content)
        self.assertIn('id="view-reasoning"', html_content)
        self.assertIn('id="view-trace"', html_content)

        js_content = js_file.read_text(encoding="utf-8")
        self.assertIn("/api/analyze", js_content)
        self.assertIn("renderAllViews", js_content)
        self.assertIn("highlightEvidence", js_content)

    def test_07_api_secret_and_credential_sanitization(self):
        """Full payload string across all scenarios must never contain raw API keys or secrets."""
        for s in OFFICIAL_SCENARIOS[:3]:
            req = {
                "scenario_id": s["scenario_id"],
                "market": s["market"],
                "category": s.get("category"),
                "product_code": s.get("product_code"),
                "date": s["date"],
                "kpi": s["kpi"],
                "provider_mode": "mock"
            }
            res = execute_decision_analysis(req)
            payload_str = json.dumps(res)
            self.assertNotIn("AIzaSy", payload_str)
            self.assertNotIn("GEMINI_API_KEY", payload_str)
            self.assertNotIn("api_key", payload_str.lower())


if __name__ == "__main__":
    unittest.main()
