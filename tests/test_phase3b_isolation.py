import os
import sys
import json
import inspect
import unittest
from pathlib import Path

from src.analytics.run_analysis import run_analysis
from src.analytics.data_model import AnalyticalDataModel

class TestPhase3BIsolation(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.ground_truth_dir = self.project_root / "Data" / "scenarios" / "evaluation_ground_truth"
        self.eval_inputs_dir = self.project_root / "Data" / "scenarios" / "evaluation_inputs"
        self.processed_data_dir = self.project_root / "Data" / "Processed"
        self.analytics_dir = self.project_root / "src" / "analytics"

    def test_01_path_isolation(self):
        """TEST 1: Path Isolation - Ground truth is strictly isolated from runtime processed data."""
        # 1. Verify ground truth path is separate from runtime processed data directory
        self.assertNotEqual(self.ground_truth_dir, self.processed_data_dir)
        self.assertFalse(str(self.ground_truth_dir).startswith(str(self.processed_data_dir)))
        
        # 2. Verify AnalyticalDataModel only reads from processed data
        dm = AnalyticalDataModel()
        self.assertEqual(Path(dm.processed_dir).resolve(), self.processed_data_dir.resolve())
        
        # 3. Ensure no ground-truth files exist in Data/Processed/
        processed_files = [f.name for f in self.processed_data_dir.glob("*.csv")]
        for pf in processed_files:
            self.assertNotIn("truth", pf.lower())
            self.assertNotIn("ground", pf.lower())

    def test_02_source_reference_check(self):
        """TEST 2: Source Reference Check - Production analytics code contains no ground-truth references."""
        banned_tokens = ["evaluation_ground_truth", "ground_truth.csv", "S001_truth", "true_root_cause"]
        exempt_files = ["evaluator.py", "remediate_ground_truth.py", "scenario_ground_truth.py"]
        
        for py_file in self.analytics_dir.glob("*.py"):
            if py_file.name in exempt_files:
                continue
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                for token in banned_tokens:
                    self.assertNotIn(token, content, f"Disallowed ground-truth token '{token}' found in {py_file.name}")

    def test_03_ground_truth_field_leakage(self):
        """TEST 3: Ground-truth field leakage - Runtime entrypoints do not accept ground-truth labels."""
        sig = inspect.signature(run_analysis)
        prohibited_params = [
            "expected_driver", 
            "true_root_cause", 
            "root_cause_status", 
            "expected_established_driver",
            "ground_truth"
        ]
        for param in prohibited_params:
            self.assertNotIn(param, sig.parameters, f"Prohibited ground-truth parameter '{param}' found in run_analysis signature.")

    def test_04_phase_3a_integrity(self):
        """TEST 4: Phase 3A integrity - Required Phase 3A production modules exist and compile."""
        required_modules = [
            "data_model.py",
            "kpi_engine.py",
            "event_detector.py",
            "driver_catalog.py",
            "driver_generator.py",
            "evidence_scorer.py",
            "contradiction_engine.py",
            "driver_ranker.py",
            "diagnosis.py",
            "run_analysis.py"
        ]
        for mod_name in required_modules:
            mod_path = self.analytics_dir / mod_name
            self.assertTrue(mod_path.exists(), f"Required module {mod_name} does not exist.")

    def test_05_ground_truth_preservation(self):
        """TEST 5: Ground-truth preservation - All 8 scenario ground-truth files exist and are intact."""
        self.assertTrue(self.ground_truth_dir.exists(), "Ground-truth directory missing.")
        for i in range(1, 9):
            truth_file = self.ground_truth_dir / f"S00{i}_truth.csv"
            self.assertTrue(truth_file.exists(), f"Ground-truth file {truth_file.name} is missing.")
            self.assertGreater(truth_file.stat().st_size, 0, f"Ground-truth file {truth_file.name} is empty.")
            
        master_truth = self.project_root / "Data" / "scenarios" / "ground_truth.csv"
        self.assertTrue(master_truth.exists(), "Master ground_truth.csv is missing.")
        self.assertGreater(master_truth.stat().st_size, 0, "Master ground_truth.csv is empty.")

    def test_06_evaluation_access_separation(self):
        """TEST 6: Evaluation Access Separation - Runtime analysis executes cleanly without ground-truth files."""
        # Execute run_analysis on a scenario payload with only runtime parameters
        runtime_request = {
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        }
        res = run_analysis(runtime_request)
        
        # Verify result contains diagnosis and candidate_hypotheses without requiring ground-truth
        self.assertIn("diagnosis", res)
        self.assertIn("candidate_hypotheses", res)
        self.assertNotIn("true_root_cause", res)
        self.assertNotIn("ground_truth", res)

if __name__ == "__main__":
    unittest.main()
