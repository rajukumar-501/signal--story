"""
Unit tests for Phase 3B.1 Deterministic Response Validator.
"""

import unittest
import json

from src.analytics.run_analysis import run_analysis
from src.phase3b.input_adapter import Phase3BInputAdapter
from src.phase3b.evidence_context import EvidenceContextBuilder
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.validator import Phase3BResponseValidator, ValidationResult

class TestPhase3B1Validation(unittest.TestCase):

    def setUp(self):
        # Scenario S003 (China marketing anomaly)
        self.req_s003 = {
            "scenario_id": "S003",
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        }
        res_s003 = run_analysis(self.req_s003)
        self.contract_s003 = Phase3BInputAdapter.validate_and_normalize(res_s003, self.req_s003)
        self.context_s003 = EvidenceContextBuilder.build(self.contract_s003)

        # Scenario S008 (Germany uncertainty anomaly)
        self.req_s008 = {
            "scenario_id": "S008",
            "market": "Germany",
            "date": "2020-03-01",
            "kpi": "gross_sales"
        }
        res_s008 = run_analysis(self.req_s008)
        self.contract_s008 = Phase3BInputAdapter.validate_and_normalize(res_s008, self.req_s008)
        self.context_s008 = EvidenceContextBuilder.build(self.contract_s008)

        self.mock_provider = MockReasoningProvider()

    def test_valid_mock_response_passes(self):
        output = self.mock_provider.generate_diagnosis(self.context_s003)
        val_res = Phase3BResponseValidator.validate(output, self.context_s003)
        self.assertTrue(val_res.is_valid, f"Validation failed with errors: {val_res.errors}")
        self.assertEqual(len(val_res.errors), 0)

    def test_rejection_of_invalid_driver_id(self):
        output = self.mock_provider.generate_diagnosis(self.context_s003)
        output["diagnosis"]["driver"] = "DRIVER_99_FICTIONAL"
        
        val_res = Phase3BResponseValidator.validate(output, self.context_s003)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any("Invalid driver identifier 'DRIVER_99_FICTIONAL'" in e for e in val_res.errors))

    def test_rejection_of_nonexistent_evidence_id(self):
        output = self.mock_provider.generate_diagnosis(self.context_s003)
        output["claims"].append({
            "claim": "Hallucinated claim with fake evidence.",
            "claim_type": "OBSERVATION",
            "evidence_ids": ["EVD-999"]
        })
        
        val_res = Phase3BResponseValidator.validate(output, self.context_s003)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any("EVD-999" in e for e in val_res.errors))

    def test_rejection_of_unsupported_observation_claim(self):
        output = self.mock_provider.generate_diagnosis(self.context_s003)
        output["claims"].append({
            "claim": "Unsupported observation with no evidence citations.",
            "claim_type": "OBSERVATION",
            "evidence_ids": []
        })
        
        val_res = Phase3BResponseValidator.validate(output, self.context_s003)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any("unsupported claim" in e for e in val_res.errors))

    def test_rejection_of_source_dataset_mismatch(self):
        output = self.mock_provider.generate_diagnosis(self.context_s003)
        # Point to valid EVD-001 but claim it came from wrong dataset
        valid_ev = self.context_s003.all_evidence[0]
        output["supporting_evidence"] = [{
            "evidence_id": valid_ev.evidence_id,
            "source_dataset": "fact_fake_dataset_wrong",
            "metric": valid_ev.metric,
            "finding": "Mismatched dataset finding."
        }]
        
        val_res = Phase3BResponseValidator.validate(output, self.context_s003)
        self.assertFalse(val_res.is_valid)
        self.assertTrue(any("source mismatch" in e for e in val_res.errors))

    def test_uncertainty_preservation_in_s008(self):
        # Valid uncertainty response passes
        valid_unc_output = self.mock_provider.generate_diagnosis(self.context_s008)
        val_res = Phase3BResponseValidator.validate(valid_unc_output, self.context_s008)
        self.assertTrue(val_res.is_valid, f"Validation failed with errors: {val_res.errors}")

        # Invalid overconfident response in S008 is rejected
        invalid_overconfident = dict(valid_unc_output)
        invalid_overconfident["diagnosis"] = {
            "driver": "DRIVER_06_CUSTOMER",
            "status": "STRONGLY_SUPPORTED",
            "confidence": "HIGH"
        }
        val_res_bad = Phase3BResponseValidator.validate(invalid_overconfident, self.context_s008)
        self.assertFalse(val_res_bad.is_valid)
        self.assertTrue(any("Gating violation" in e for e in val_res_bad.errors))

    def test_deterministic_fallback_generation(self):
        fallback = Phase3BResponseValidator.get_safe_fallback(self.context_s003, "API Timeout")
        self.assertEqual(fallback["validation_status"], "FALLBACK_PRESERVED")
        self.assertEqual(fallback["diagnosis"]["driver"], self.context_s003.diagnosis.established_driver)
        self.assertEqual(fallback["diagnosis"]["status"], self.context_s003.diagnosis.overall_status)

if __name__ == "__main__":
    unittest.main()
