"""
Phase 5.2B — Data Quality, Freshness & Trust Control Layer Test Suite.
Tests deterministic data quality evaluation, negative fixtures (missing files,
missing columns, null-heavy fields, duplicates, invalid dates, stale coverage),
API contract integration, secret protection, and analytical core preservation.
"""

import unittest
import json
from pathlib import Path
import sys
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.governance.data_quality import DataQualityEngine, evaluate_data_trust
from src.server import execute_decision_analysis


class TestPhase52BDataQuality(unittest.TestCase):
    """Deterministic data quality and trust suite for Phase 5.2B."""

    def setUp(self):
        self.engine = DataQualityEngine()

    def test_01_canonical_warehouse_healthy(self):
        """Standard canonical warehouse must achieve TRUSTED status with score >= 95.0%."""
        res = self.engine.evaluate_all(target_date="2021-04-01")
        self.assertEqual(res["overall_status"], "TRUSTED")
        self.assertGreaterEqual(res["overall_score"], 95.0)
        self.assertEqual(res["coverage_status"], "COMPLETE")
        self.assertEqual(res["latest_available_date"], "2021-08-01")
        self.assertGreaterEqual(res["dataset_count"], 9)
        self.assertGreater(res["quality_checks_passed"], 0)

    def test_02_negative_missing_dataset(self):
        """Missing dataset must trigger BLOCKED status and score 0.0."""
        res = self.engine.evaluate_dataset("non_existent_file.csv")
        self.assertEqual(res["status"], "BLOCKED")
        self.assertEqual(res["quality_score"], 0.0)
        self.assertIn("Missing required", res["warnings"][0])

    def test_03_negative_missing_required_column(self):
        """Dataset missing critical required columns must fail schema check and yield BLOCKED."""
        bad_df = pd.DataFrame({
            "date": ["2021-04-01"],
            "product_code": ["A2520150501"]
            # Missing customer_code, gross_sales_amount, signed_sales_amount, etc.
        })
        res = self.engine.evaluate_dataset("fact_sales_monthly.csv", df=bad_df)
        self.assertEqual(res["status"], "BLOCKED")
        self.assertLess(res["quality_score"], 60.0)
        missing_chk = next(c for c in res["checks"] if c["name"] == "required_columns")
        self.assertEqual(missing_chk["status"], "FAIL")

    def test_04_negative_null_heavy_field(self):
        """Field with excessive nulls exceeding tolerance must fail null-rate check."""
        bad_df = pd.DataFrame({
            "campaign_id": [f"C{i}" for i in range(100)],
            "date": ["2021-04-01"] * 100,
            "product_code": ["A2520150501"] * 100,
            "market": ["China"] * 100,
            "spend": [None] * 50 + [100.0] * 50,  # 50% nulls on spend
            "impressions": [1000] * 100,
            "clicks": [100] * 100,
            "conversions": [10] * 100
        })
        res = self.engine.evaluate_dataset("fact_marketing_monthly.csv", df=bad_df)
        self.assertIn(res["status"], {"DEGRADED", "BLOCKED"})
        self.assertLess(res["quality_score"], 95.0)
        null_chk = next(c for c in res["checks"] if c["name"] == "null_rate_tolerance")
        self.assertEqual(null_chk["status"], "FAIL")

    def test_05_negative_duplicate_natural_keys(self):
        """Dataset with duplicate natural keys must fail key uniqueness check."""
        dup_df = pd.DataFrame({
            "date": ["2021-04-01", "2021-04-01"],
            "product_code": ["P001", "P001"],  # Duplicate on date + product + market
            "market": ["China", "China"],
            "opening_stock_units": [100, 100],
            "received_units": [50, 50],
            "closing_stock_units": [150, 150],
            "stockout_flag": [0, 0],
            "stockout_hours": [0, 0]
        })
        res = self.engine.evaluate_dataset("fact_inventory_monthly.csv", df=dup_df)
        self.assertLess(res["quality_score"], 100.0)
        dup_chk = next(c for c in res["checks"] if c["name"] == "natural_key_uniqueness")
        self.assertEqual(dup_chk["status"], "FAIL")

    def test_06_negative_invalid_dates(self):
        """Dataset containing unparseable dates must fail date parsing check."""
        bad_df = pd.DataFrame({
            "date": ["2021-04-01", "INVALID_DATE_STRING", "9999-99-99"],
            "product_code": ["P1", "P2", "P3"],
            "market": ["China", "China", "China"],
            "our_price": [10.0, 10.0, 10.0],
            "average_competitor_price": [9.0, 9.0, 9.0],
            "price_gap_percent": [0.1, 0.1, 0.1]
        })
        res = self.engine.evaluate_dataset("fact_competitor_pricing_monthly.csv", df=bad_df)
        date_chk = next(c for c in res["checks"] if c["name"] == "date_parsing")
        self.assertEqual(date_chk["status"], "FAIL")

    def test_07_negative_empty_dataset(self):
        """Empty dataframe with 0 records must fail non-empty rows check."""
        empty_df = pd.DataFrame(columns=["ticket_id", "date", "customer_code", "product_code", "market", "sentiment", "priority"])
        res = self.engine.evaluate_dataset("fact_support_tickets.csv", df=empty_df)
        self.assertEqual(res["status"], "BLOCKED")
        empty_chk = next(c for c in res["checks"] if c["name"] == "non_empty_rows")
        self.assertEqual(empty_chk["status"], "FAIL")

    def test_08_temporal_coverage_future_stale_data(self):
        """Target date beyond available warehouse data must return STALE_DATA coverage."""
        res = self.engine.evaluate_all(target_date="2025-01-01")
        self.assertEqual(res["coverage_status"], "STALE_DATA")
        self.assertIn(res["overall_status"], {"DEGRADED", "BLOCKED"})
        self.assertTrue(any("beyond latest warehouse coverage" in w for w in res["warnings"]))

    def test_09_api_analyze_embeds_data_trust(self):
        """POST /api/analyze response must include data_trust report without breaking contract."""
        req = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "provider_mode": "mock"
        }
        res = execute_decision_analysis(req)
        self.assertIn("data_trust", res)
        dt = res["data_trust"]
        self.assertEqual(dt["overall_status"], "TRUSTED")
        self.assertGreaterEqual(dt["overall_score"], 95.0)
        self.assertEqual(dt["coverage_status"], "COMPLETE")
        self.assertEqual(dt["requested_period"], "2021-04-01")

    def test_10_zero_secrets_exposure(self):
        """Data trust output must not contain any API keys or secrets."""
        dt = evaluate_data_trust(target_date="2021-04-01")
        dt_str = json.dumps(dt)
        self.assertNotIn("GEMINI_API_KEY", dt_str)
        self.assertNotIn("AIzaSy", dt_str)

    def test_11_s003_analytical_outcome_immutability(self):
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


if __name__ == "__main__":
    unittest.main()
