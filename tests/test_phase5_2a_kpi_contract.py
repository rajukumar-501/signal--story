"""
Phase 5.2A — Accenture KPI & Semantic Contract Automated Test Suite.
Verifies machine-readable contract existence, JSON schema compliance,
multi-KPI coverage, API retrieval, secret protection, and frozen-core immutability.
"""

import unittest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.server import load_kpi_contract, execute_decision_analysis, OFFICIAL_SCENARIOS


class TestPhase52AKPIContract(unittest.TestCase):
    """Automated tests for Accenture KPI Semantic Contract specification."""

    def setUp(self):
        self.contract_path = PROJECT_ROOT / "Data" / "semantic" / "kpi_contract.json"

    def test_01_contract_file_exists_and_valid_json(self):
        """Semantic contract JSON file must exist and parse without syntax errors."""
        self.assertTrue(self.contract_path.exists(), "Data/semantic/kpi_contract.json does not exist")
        raw_text = self.contract_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        self.assertIn("version", data)
        self.assertIn("schema", data)
        self.assertIn("kpis", data)
        self.assertIsInstance(data["kpis"], dict)

    def test_02_required_fields_present_in_all_kpis(self):
        """All registered KPIs must declare all 15 required Accenture contract fields."""
        required_fields = [
            "kpi_id",
            "name",
            "business_definition",
            "unit",
            "calculation",
            "grain",
            "baseline_method",
            "materiality_threshold",
            "candidate_drivers",
            "source_datasets",
            "source_freshness",
            "analytical_method",
            "lineage_reference",
            "access_roles",
            "sensitivity_classification"
        ]

        data = load_kpi_contract()
        self.assertNotIn("error", data)
        kpis = data.get("kpis", {})
        self.assertGreaterEqual(len(kpis), 2, "Must support at least 2 distinct KPIs")

        for kpi_id, kpi_meta in kpis.items():
            for field in required_fields:
                self.assertIn(field, kpi_meta, f"KPI '{kpi_id}' is missing required field '{field}'")
                val = kpi_meta[field]
                self.assertIsNotNone(val, f"Field '{field}' in KPI '{kpi_id}' cannot be null")
                if isinstance(val, (list, str)):
                    self.assertGreater(len(val), 0, f"Field '{field}' in KPI '{kpi_id}' cannot be empty")

    def test_03_multi_kpi_coverage(self):
        """Contract must support primary benchmark KPIs: gross_sales and category_share."""
        data = load_kpi_contract()
        kpis = data.get("kpis", {})
        self.assertIn("gross_sales", kpis)
        self.assertIn("category_share", kpis)
        self.assertIn("signed_net_revenue", kpis)

        # Verify gross_sales specific contract
        gs = kpis["gross_sales"]
        self.assertEqual(gs["kpi_id"], "gross_sales")
        self.assertEqual(gs["unit"], "USD ($)")
        self.assertEqual(gs["calculation"], "SUM(gross_sales_amount)")
        self.assertEqual(len(gs["candidate_drivers"]), 9)

        # Verify category_share specific contract
        cs = kpis["category_share"]
        self.assertEqual(cs["kpi_id"], "category_share")
        self.assertEqual(cs["unit"], "Percentage (%)")
        self.assertIn("DRIVER_08_PRODUCT_MIX", [d["driver_id"] for d in cs["candidate_drivers"]])

    def test_04_api_kpi_contract_retrieval(self):
        """load_kpi_contract must support full catalog and filtered KPI queries."""
        # Full contract
        full = load_kpi_contract()
        self.assertIn("version", full)
        self.assertIn("kpis", full)

        # Specific KPI query
        single = load_kpi_contract("gross_sales")
        self.assertNotIn("error", single)
        self.assertIn("kpi", single)
        self.assertEqual(single["kpi"]["kpi_id"], "gross_sales")

        # Unknown KPI handling
        invalid = load_kpi_contract("non_existent_kpi")
        self.assertIn("error", invalid)
        self.assertEqual(invalid["status"], 404)
        self.assertIn("available_kpis", invalid)

    def test_05_execute_decision_analysis_integration(self):
        """execute_decision_analysis response must include the kpi_contract object."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        self.assertIn("kpi_contract", res)
        self.assertIsNotNone(res["kpi_contract"])
        self.assertEqual(res["kpi_contract"]["kpi_id"], "gross_sales")
        self.assertEqual(res["kpi_contract"]["calculation"], "SUM(gross_sales_amount)")

    def test_06_zero_secrets_exposure(self):
        """Neither load_kpi_contract nor execute_decision_analysis should leak secrets."""
        contract_data = load_kpi_contract()
        raw_contract_str = json.dumps(contract_data)
        self.assertNotIn("GEMINI_API_KEY", raw_contract_str)
        self.assertNotIn("AIzaSy", raw_contract_str)

        analysis_res = execute_decision_analysis({
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        })
        raw_res_str = json.dumps(analysis_res)
        self.assertNotIn("AIzaSy", raw_res_str)
        self.assertNotIn("GEMINI_API_KEY", raw_res_str)

    def test_07_frozen_core_preservation(self):
        """Analytical results for S003 showcase must remain exactly identical."""
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


if __name__ == "__main__":
    unittest.main()
