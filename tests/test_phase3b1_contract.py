"""
Unit tests for Phase 3B.1 Input Adapter and Contract Normalization.
"""

import unittest
from typing import Dict, Any

from src.analytics.run_analysis import run_analysis
from src.phase3b.input_adapter import (
    Phase3BInputAdapter,
    Phase3BInputContract,
    InputContractError,
    ScenarioRequest
)

class TestPhase3B1Contract(unittest.TestCase):

    def setUp(self):
        self.sample_request = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        }
        self.phase3a_output = run_analysis(self.sample_request)

    def test_successful_normalization(self):
        contract = Phase3BInputAdapter.validate_and_normalize(self.phase3a_output, self.sample_request)
        self.assertIsInstance(contract, Phase3BInputContract)
        self.assertEqual(contract.schema_version, "1.0.0")
        self.assertEqual(contract.phase3a_baseline, "3A.3")
        self.assertEqual(contract.request.scenario_id, "S003")
        self.assertEqual(contract.request.market, "China")
        self.assertEqual(contract.event.kpi, "gross_sales")
        self.assertGreater(len(contract.candidate_hypotheses), 0)
        self.assertIsNotNone(contract.diagnosis.overall_status)

    def test_preserves_candidate_scores_and_statuses(self):
        contract = Phase3BInputAdapter.validate_and_normalize(self.phase3a_output, self.sample_request)
        raw_hyps = self.phase3a_output.get("candidate_hypotheses", self.phase3a_output.get("candidate_drivers"))
        
        self.assertEqual(len(contract.candidate_hypotheses), len(raw_hyps))
        for raw_h, norm_h in zip(raw_hyps, contract.candidate_hypotheses):
            self.assertEqual(raw_h["driver"], norm_h.driver)
            self.assertAlmostEqual(raw_h["score"], norm_h.score)
            self.assertEqual(raw_h["status"], norm_h.status)
            self.assertEqual(raw_h.get("temporal_alignment", "NO_CLEAR_ALIGNMENT"), norm_h.temporal_alignment)

    def test_rejection_of_missing_event(self):
        corrupted = dict(self.phase3a_output)
        del corrupted["event"]
        with self.assertRaises(InputContractError) as ctx:
            Phase3BInputAdapter.validate_and_normalize(corrupted, self.sample_request)
        self.assertIn("Missing required top-level key 'event'", str(ctx.exception))

    def test_rejection_of_missing_diagnosis(self):
        corrupted = dict(self.phase3a_output)
        del corrupted["diagnosis"]
        with self.assertRaises(InputContractError) as ctx:
            Phase3BInputAdapter.validate_and_normalize(corrupted, self.sample_request)
        self.assertIn("Missing required top-level key 'diagnosis'", str(ctx.exception))

    def test_rejection_of_oracle_fields_in_payload(self):
        oracle_payload = dict(self.phase3a_output)
        oracle_payload["true_root_cause"] = "DRIVER_03_MARKETING"
        
        with self.assertRaises(InputContractError) as ctx:
            Phase3BInputAdapter.validate_and_normalize(oracle_payload, self.sample_request)
        self.assertIn("Forbidden oracle key 'true_root_cause'", str(ctx.exception))

    def test_rejection_of_oracle_fields_in_request(self):
        oracle_req = dict(self.sample_request)
        oracle_req["expected_driver"] = "DRIVER_03_MARKETING"
        
        with self.assertRaises(InputContractError) as ctx:
            Phase3BInputAdapter.validate_and_normalize(self.phase3a_output, oracle_req)
        self.assertIn("Forbidden oracle key 'expected_driver'", str(ctx.exception))

    def test_contract_to_dict_serialization(self):
        contract = Phase3BInputAdapter.validate_and_normalize(self.phase3a_output, self.sample_request)
        contract_dict = contract.to_dict()
        self.assertIsInstance(contract_dict, dict)
        self.assertEqual(contract_dict["schema_version"], "1.0.0")
        self.assertEqual(contract_dict["phase3a_baseline"], "3A.3")
        self.assertIn("request", contract_dict)
        self.assertIn("event", contract_dict)
        self.assertIn("candidate_hypotheses", contract_dict)
        self.assertIn("diagnosis", contract_dict)

if __name__ == "__main__":
    unittest.main()
