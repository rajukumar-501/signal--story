"""
Unit tests for Phase 3B.1 Isolation and Ground-Truth Boundary Protection.
"""

import unittest
import os
import sys
import inspect
from pathlib import Path

from src.analytics.run_analysis import run_analysis
from src.phase3b.input_adapter import Phase3BInputAdapter
from src.phase3b.evidence_context import EvidenceContextBuilder
import src.phase3b

class TestPhase3B1Isolation(unittest.TestCase):

    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.phase3b_dir = self.project_root / "src" / "phase3b"

    def test_a_filesystem_isolation(self):
        """Phase 3B source code files must not reference evaluation_ground_truth directory."""
        forbidden_patterns = [
            "evaluation_ground_truth",
            "ground_truth.csv",
            "scenario_ground_truth.json"
        ]
        
        for py_file in self.phase3b_dir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for pat in forbidden_patterns:
                    self.assertNotIn(
                        pat, 
                        content, 
                        f"Filesystem isolation violation: '{pat}' referenced in {py_file.name}"
                    )

    def test_b_import_isolation(self):
        """Phase 3B modules must not import any evaluation or ground-truth scripts."""
        for name, module in sys.modules.items():
            if name.startswith("src.phase3b"):
                source = inspect.getsource(module) if hasattr(module, "__file__") and module.__file__ else ""
                self.assertNotIn("evaluation_ground_truth", source)
                self.assertNotIn("test_phase3a3_accuracy", source)

    def test_c_context_isolation(self):
        """The constructed EvidenceContext must not contain oracle fields."""
        request = {
            "scenario_id": "S001",
            "market": "South Korea",
            "product_code": "A6519160401",
            "date": "2021-05-01",
            "kpi": "gross_sales"
        }
        phase3a_res = run_analysis(request)
        contract = Phase3BInputAdapter.validate_and_normalize(phase3a_res, request)
        context = EvidenceContextBuilder.build(contract)
        
        context_dict = context.to_dict()
        self._assert_no_oracle_keys(context_dict)

    def test_d_evidence_source_dataset_validity(self):
        """All evidence items must originate from canonical processed datasets or recognized telemetry."""
        canonical_datasets = {
            "fact_sales_monthly",
            "fact_inventory_monthly",
            "fact_competitor_pricing_monthly",
            "fact_marketing_monthly",
            "fact_support_tickets",
            "fact_crm_notes",
            "fact_sales_calls",
            "dim_product",
            "dim_customer",
            "dim_market",
            "derived_financial_telemetry"
        }
        
        request = {"market": "South Korea", "date": "2021-01-01", "kpi": "gross_sales"}
        phase3a_res = run_analysis(request)
        contract = Phase3BInputAdapter.validate_and_normalize(phase3a_res, request)
        context = EvidenceContextBuilder.build(contract)

        for ev in context.all_evidence:
            self.assertIn(
                ev.source_dataset,
                canonical_datasets,
                f"Unknown source dataset '{ev.source_dataset}' for evidence {ev.evidence_id}"
            )

    def test_e_no_derived_ground_truth_datasets_created(self):
        """Confirm that building context creates no persistent ground truth files."""
        eval_gt_dir = self.project_root / "Data" / "scenarios" / "evaluation_ground_truth"
        initial_file_count = len(list(eval_gt_dir.glob("*.csv")))
        
        request = {"market": "Indonesia", "date": "2020-03-01", "kpi": "gross_sales"}
        phase3a_res = run_analysis(request)
        contract = Phase3BInputAdapter.validate_and_normalize(phase3a_res, request)
        _ = EvidenceContextBuilder.build(contract)
        
        final_file_count = len(list(eval_gt_dir.glob("*.csv")))
        self.assertEqual(initial_file_count, final_file_count)

    def _assert_no_oracle_keys(self, data):
        forbidden = Phase3BInputAdapter.FORBIDDEN_ORACLE_KEYS
        if isinstance(data, dict):
            for k, v in data.items():
                self.assertNotIn(k, forbidden, f"Forbidden oracle key '{k}' found in context.")
                self._assert_no_oracle_keys(v)
        elif isinstance(data, list):
            for item in data:
                self._assert_no_oracle_keys(item)

if __name__ == "__main__":
    unittest.main()
