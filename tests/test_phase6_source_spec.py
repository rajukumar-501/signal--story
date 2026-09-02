"""
Unit Tests for Phase 6A: Source Integration Specification.
Verifies machine-readable specification, schema compliance,
dataset attributes, and reconciliation keys across 10 canonical files and 5 domains.
"""

import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = PROJECT_ROOT / "Data" / "semantic" / "source_integration_spec.json"


class TestPhase6SourceSpec(unittest.TestCase):
    """Tests for the Source Integration Specification."""

    def setUp(self):
        self.assertTrue(SPEC_PATH.exists(), f"Source integration spec missing at {SPEC_PATH}")
        with open(SPEC_PATH, "r", encoding="utf-8") as f:
            self.spec = json.load(f)

    def test_top_level_metadata(self):
        """Verifies top-level specification schema and governance standards."""
        self.assertEqual(self.spec.get("spec_version"), "1.0.0")
        self.assertEqual(self.spec.get("total_canonical_datasets"), 10)
        self.assertEqual(self.spec.get("total_business_domains"), 5)
        self.assertEqual(self.spec.get("default_refresh_cadence"), "Monthly batch ETL (T+1 calendar close)")
        self.assertIn("date", self.spec.get("primary_reconciliation_keys", []))
        self.assertIn("market", self.spec.get("primary_reconciliation_keys", []))
        self.assertIn("product_code", self.spec.get("primary_reconciliation_keys", []))

    def test_domains_and_datasets_completeness(self):
        """Verifies all 5 canonical business domains and 10 datasets are documented."""
        domains = self.spec.get("domains", [])
        self.assertEqual(len(domains), 5)

        domain_ids = [d["domain_id"] for d in domains]
        self.assertIn("COMMERCIAL_SALES", domain_ids)
        self.assertIn("DIGITAL_MARKETING", domain_ids)
        self.assertIn("MARKET_INTELLIGENCE", domain_ids)
        self.assertIn("SUPPLY_CHAIN", domain_ids)
        self.assertIn("CUSTOMER_MASTER", domain_ids)

        all_datasets = []
        for dom in domains:
            for ds in dom.get("datasets", []):
                all_datasets.append(ds)

        self.assertEqual(len(all_datasets), 10)
        canonical_files = [ds["canonical_file"] for ds in all_datasets]
        expected_files = [
            "fact_sales_monthly.csv",
            "fact_gross_price.csv",
            "fact_post_invoice_deductions.csv",
            "fact_pre_invoice_deductions.csv",
            "fact_marketing_monthly.csv",
            "fact_competitor_pricing_monthly.csv",
            "fact_inventory_monthly.csv",
            "fact_manufacturing_cost.csv",
            "dim_customer.csv",
            "dim_product.csv"
        ]
        for ef in expected_files:
            self.assertIn(ef, canonical_files)

    def test_dataset_attributes(self):
        """Verifies each dataset exposes grain, refresh cadence, and lineage path."""
        for dom in self.spec.get("domains", []):
            for ds in dom.get("datasets", []):
                self.assertTrue(ds.get("dataset_id"))
                self.assertTrue(ds.get("canonical_file"))
                self.assertGreater(ds.get("row_count", 0), 0)
                self.assertTrue(ds.get("grain"))
                self.assertTrue(ds.get("refresh_cadence"))
                self.assertTrue(ds.get("lineage_reference"))
                self.assertTrue(ds.get("semantic_role"))


if __name__ == "__main__":
    unittest.main()
