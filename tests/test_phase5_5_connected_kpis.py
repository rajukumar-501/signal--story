"""
Tests for Phase 5.5 Connected KPI Evidence Layer.
Verifies multi-source connected KPI extraction, lineage, dimensional alignment,
grain preservation, cadence metadata, and epistemic guardrails.
"""

import unittest
import json
from pathlib import Path
from src.governance.connected_kpis import ConnectedKPIEngine
from src.analytics.data_model import AnalyticalDataModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase55ConnectedKPIs(unittest.TestCase):
    """Test suite for Connected KPI Evidence Layer."""

    def setUp(self):
        self.data_model = AnalyticalDataModel()
        self.engine = ConnectedKPIEngine(data_model=self.data_model)

    def test_01_returns_3_to_5_kpis_for_s003(self):
        """Verify that 3–5 connected KPIs are returned for Scenario S003."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        self.assertIn("connected_kpis", res)
        kpis = res["connected_kpis"]
        self.assertGreaterEqual(len(kpis), 3)
        self.assertLessEqual(len(kpis), 5)
        
        # Verify KPI IDs
        kpi_ids = [k["kpi_id"] for k in kpis]
        self.assertIn("gross_sales", kpi_ids)
        self.assertIn("marketing_spend", kpi_ids)
        self.assertIn("conversion_rate", kpi_ids)

    def test_02_all_kpis_have_real_source_lineage(self):
        """Verify that all connected KPIs have real source datasets and systems."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        for k in res["connected_kpis"]:
            self.assertIn("source_dataset", k)
            self.assertIn("source_system", k)
            self.assertTrue(k["source_dataset"].endswith(".csv"))
            self.assertIn(k["source_dataset"], ["fact_sales_monthly.csv", "fact_marketing_monthly.csv", "fact_competitor_pricing_monthly.csv", "fact_inventory_monthly.csv"])

    def test_03_alignment_uses_real_dimensions(self):
        """Verify dimensional alignment uses real dimensions (date, market, product_code)."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        self.assertEqual(res["alignment_keys"], ["date", "market", "product_code"])
        for k in res["connected_kpis"]:
            self.assertEqual(k["alignment_dimensions"], ["date", "market", "product_code"])

    def test_04_grain_and_cadence_metadata_preserved(self):
        """Verify that distinct grain and cadence metadata are preserved."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        self.assertIn("distinct_grains", res)
        self.assertIn("distinct_cadences", res)
        self.assertEqual(res["distinct_sources_count"], 2)
        
        # Check sales grain vs marketing grain
        sales_kpi = next(k for k in res["connected_kpis"] if k["kpi_id"] == "gross_sales")
        mktg_kpi = next(k for k in res["connected_kpis"] if k["kpi_id"] == "marketing_spend")
        
        self.assertIn("Customer", sales_kpi["grain"])
        self.assertIn("Campaign", mktg_kpi["grain"])
        self.assertIn("Batch ETL", sales_kpi["cadence"])
        self.assertIn("Telemetry", mktg_kpi["cadence"])

    def test_05_evidence_roles_correctly_classified(self):
        """Verify clear distinction of evidence roles."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        roles = {k["kpi_id"]: k["evidence_role"] for k in res["connected_kpis"]}
        self.assertEqual(roles["gross_sales"], "OUTCOME_KPI")
        self.assertEqual(roles["order_volume"], "CORROBORATING_KPI")
        self.assertEqual(roles["marketing_spend"], "DRIVER_SIGNAL")
        self.assertEqual(roles["conversion_rate"], "DRIVER_SIGNAL")

    def test_06_epistemic_guardrails_enforced_in_explanation(self):
        """Verify explanation avoids prohibited causal language and uses approved phrasing."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        exp = res["deterministic_explanation"].lower()
        self.assertNotIn("caused by", exp)
        self.assertNotIn("root cause proven", exp)
        self.assertNotIn("definitely caused", exp)
        
        self.assertTrue("evidence indicates" in exp or "aligned" in exp or "corroborating" in exp)

    def test_07_s003_values_remain_mathematically_exact(self):
        """Verify S003 actual and baseline values remain exact against warehouse ledger."""
        res = self.engine.get_connected_kpis(
            market="China",
            product_code="A2520150501",
            date_str="2021-04-01",
            scenario_id="S003"
        )
        sales_kpi = next(k for k in res["connected_kpis"] if k["kpi_id"] == "gross_sales")
        self.assertAlmostEqual(sales_kpi["current_value"], 994.25, places=2)
        self.assertAlmostEqual(sales_kpi["baseline_value"], 3558.03, places=2)
        self.assertAlmostEqual(sales_kpi["change_percent"], -72.06, places=1)

        mktg_kpi = next(k for k in res["connected_kpis"] if k["kpi_id"] == "marketing_spend")
        self.assertAlmostEqual(mktg_kpi["current_value"], 1641.07, places=2)
        self.assertAlmostEqual(mktg_kpi["baseline_value"], 994.94, places=2)
        self.assertAlmostEqual(mktg_kpi["change_percent"], 64.94, places=1)


if __name__ == "__main__":
    unittest.main()
