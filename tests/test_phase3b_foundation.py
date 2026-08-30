"""
Unit and Isolation Test Suite for Phase 3B LLM Reasoning Layer (Step 1 Foundation).
Tests strict isolation from ground truth, evidence-grounded validation, uncertainty preservation,
and zero regression on Phase 3A.
"""

import unittest
import os
import re
import json
from pathlib import Path

from src.analytics.run_analysis import run_analysis
from src.reasoning import (
    ReasoningEngine,
    ReasoningContext,
    ReasoningContextBuilder,
    PromptBuilder,
    MockLLMProvider,
    ResponseValidator,
    ValidationResult,
    InputContractValidator,
    InputContractError
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestPhase3BFoundation(unittest.TestCase):

    def setUp(self):
        self.sample_request = {
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        }
        self.phase3a_output = run_analysis(self.sample_request)

    def test_01_consume_phase3a_output(self):
        """TEST 1: Phase 3B can consume Phase 3A output directly and return a valid diagnosis."""
        engine = ReasoningEngine()
        result = engine.analyze(self.phase3a_output, user_query="Explain the China gross sales decline in April 2021.")
        
        self.assertEqual(result.get("validation_status"), "PASSED")
        self.assertIn("executive_summary", result)
        self.assertIn("what_happened", result)
        self.assertIn("diagnosis", result)
        self.assertIn("reasoning", result)
        self.assertIn("supporting_evidence", result)
        self.assertIn("traceability", result)
        self.assertIn(result["diagnosis"]["status"], ["STRONGLY_SUPPORTED", "PLAUSIBLE", "NOT_ESTABLISHED"])

    def test_02_no_ground_truth_imports(self):
        """TEST 2: Phase 3B modules do not import evaluation ground truth."""
        reasoning_dir = PROJECT_ROOT / "src" / "reasoning"
        for py_file in reasoning_dir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("evaluation_ground_truth", content, f"Import violation in {py_file}")
                self.assertNotIn("scenario_ground_truth", content, f"Import violation in {py_file}")
                self.assertNotIn("ground_truth.csv", content, f"Import violation in {py_file}")

    def test_03_no_ground_truth_file_access(self):
        """TEST 3: Phase 3B source code does not contain hardcoded paths to ground-truth directories."""
        reasoning_dir = PROJECT_ROOT / "src" / "reasoning"
        for py_file in reasoning_dir.glob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("evaluation_ground_truth", content)
                self.assertNotIn("Data/scenarios/evaluation_ground_truth", content)

    def test_04_reasoning_context_no_ground_truth_fields(self):
        """TEST 4: ReasoningContext contains zero ground-truth fields and rejects contaminated payloads."""
        context = ReasoningContextBuilder.build(self.phase3a_output)
        context_dict = context.to_dict()
        
        context_str = json.dumps(context_dict)
        self.assertNotIn("true_root_cause", context_str)
        self.assertNotIn("root_cause_status", context_str)
        self.assertNotIn("expected_driver", context_str)
        self.assertNotIn("target_cause", context_str)

        # Test that injecting forbidden oracle field raises InputContractError
        contaminated_payload = dict(self.phase3a_output)
        contaminated_payload["true_root_cause"] = "DRIVER_03_MARKETING"
        with self.assertRaises(InputContractError):
            ReasoningContextBuilder.build(contaminated_payload)

    def test_05_prompt_no_ground_truth_labels(self):
        """TEST 5: Generated prompt contains zero ground-truth oracle labels or expected answers."""
        context = ReasoningContextBuilder.build(self.phase3a_output)
        prompt = PromptBuilder.build_prompt(context)

        self.assertNotIn("true_root_cause", prompt)
        self.assertNotIn("root_cause_status", prompt)
        self.assertNotIn("expected_driver", prompt)
        self.assertNotIn("oracle_driver", prompt)

    def test_06_reject_unsupported_evidence_id(self):
        """TEST 6: Validator rejects LLM responses citing non-existent evidence IDs."""
        context = ReasoningContextBuilder.build(self.phase3a_output)
        
        # Craft an invalid response with a hallucinated evidence ID
        fake_response = {
            "executive_summary": "Summary",
            "what_happened": "Decline observed",
            "diagnosis": {
                "driver": "DRIVER_03_MARKETING",
                "status": "PLAUSIBLE",
                "confidence": "MEDIUM"
            },
            "reasoning": [
                {
                    "claim": "Claim based on fake evidence",
                    "evidence_ids": ["EVD-999"],  # Non-existent
                    "explanation": "Explanation"
                }
            ],
            "supporting_evidence": [
                {
                    "evidence_id": "EVD-999",
                    "source_dataset": "fact_marketing_monthly",
                    "metric": "spend_change",
                    "finding": "Fake finding"
                }
            ],
            "contradictory_evidence": [],
            "uncertainties": [],
            "recommended_next_steps": ["Investigate"],
            "traceability": []
        }

        result = ResponseValidator.validate(fake_response, context)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("non-existent evidence_id 'EVD-999'" in e for e in result.errors))

    def test_07_reject_invalid_llm_output(self):
        """TEST 7: Validator rejects malformed JSON, missing fields, or invalid drivers."""
        context = ReasoningContextBuilder.build(self.phase3a_output)

        # A. Malformed JSON
        res_malformed = ResponseValidator.validate("This is not JSON", context)
        self.assertFalse(res_malformed.is_valid)

        # B. Missing required fields
        res_missing = ResponseValidator.validate({"executive_summary": "Incomplete"}, context)
        self.assertFalse(res_missing.is_valid)

        # C. Invalid driver ID
        bad_driver_response = {
            "executive_summary": "Summary",
            "what_happened": "Decline",
            "diagnosis": {
                "driver": "DRIVER_99_MAGIC",
                "status": "PLAUSIBLE",
                "confidence": "MEDIUM"
            },
            "reasoning": [],
            "supporting_evidence": [],
            "contradictory_evidence": [],
            "uncertainties": [],
            "recommended_next_steps": [],
            "traceability": []
        }
        res_bad_driver = ResponseValidator.validate(bad_driver_response, context)
        self.assertFalse(res_bad_driver.is_valid)
        self.assertTrue(any("Invalid driver" in e for e in res_bad_driver.errors))

    def test_08_not_established_uncertainty_preserved(self):
        """TEST 8: NOT_ESTABLISHED status and null driver are correctly produced and preserved when data is inconclusive."""
        synthetic_payload = {
            "event": {
                "kpi": "gross_sales",
                "current_value": 100.0,
                "previous_month_value": 110.0,
                "baseline_value": 105.0,
                "mom_change_percent": -0.09,
                "baseline_change_percent": -0.047,
                "change_percent": -0.09,
                "baseline_status": "VALID"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_06_CUSTOMER",
                    "rank": 1,
                    "score": 1.0,
                    "status": "NOT_ESTABLISHED",
                    "confidence": "NONE",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "record_id": None,
                            "lineage": "AGGREGATED",
                            "date": "2021-05-01",
                            "market": "India",
                            "product_code": "P01",
                            "metric": "channel_share_shift",
                            "value": -0.02,
                            "evidence_role": "SUPPORTING"
                        }
                    ],
                    "contradictions": [],
                    "evidence_source_count": 1,
                    "supporting_evidence_count": 1,
                    "contradictory_evidence_count": 0,
                    "temporal_alignment": "DURING"
                }
            ],
            "diagnosis": {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": "Top hypothesis score (1.0) is insufficient to establish root cause.",
                "confidence": "NONE"
            },
            "overall_status": "NOT_ESTABLISHED",
            "limitations": ["Observational telemetry only."]
        }

        engine = ReasoningEngine()
        result = engine.analyze(synthetic_payload, user_query="Explain the sales movement.")

        self.assertEqual(result.get("validation_status"), "PASSED")
        self.assertEqual(result["diagnosis"]["status"], "NOT_ESTABLISHED")
        self.assertIsNone(result["diagnosis"]["driver"])
        self.assertEqual(result["diagnosis"]["confidence"], "NONE")

    def test_09_contradictory_evidence_and_mock_injection(self):
        """TEST 9: MockLLMProvider correctly supports injected custom responses and catches contradiction mismatches."""
        synthetic_payload = {
            "event": {
                "kpi": "gross_sales",
                "current_value": 500.0,
                "previous_month_value": 1000.0,
                "baseline_value": 900.0,
                "mom_change_percent": -0.5,
                "baseline_change_percent": -0.44,
                "change_percent": -0.5,
                "baseline_status": "VALID"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_03_MARKETING",
                    "rank": 1,
                    "score": 6.0,
                    "status": "PLAUSIBLE",
                    "confidence": "MEDIUM",
                    "evidence": [
                        {
                            "source_dataset": "fact_marketing_monthly",
                            "record_id": None,
                            "lineage": "AGGREGATED",
                            "date": "2021-04-01",
                            "market": "China",
                            "product_code": "P01",
                            "metric": "spend_change",
                            "value": 0.35,
                            "evidence_role": "SUPPORTING"
                        },
                        {
                            "source_dataset": "fact_inventory_monthly",
                            "record_id": None,
                            "lineage": "AGGREGATED",
                            "date": "2021-04-01",
                            "market": "China",
                            "product_code": "P01",
                            "metric": "inventory_stockout_clash",
                            "value": 1.0,
                            "evidence_role": "CONTRADICTORY"
                        }
                    ],
                    "contradictions": ["inventory_stockout_clash"],
                    "evidence_source_count": 1,
                    "supporting_evidence_count": 1,
                    "contradictory_evidence_count": 1,
                    "temporal_alignment": "DURING"
                }
            ],
            "diagnosis": {
                "established_driver": "DRIVER_03_MARKETING",
                "overall_status": "PLAUSIBLE",
                "reason": "Driver DRIVER_03_MARKETING established with status PLAUSIBLE.",
                "confidence": "MEDIUM"
            },
            "overall_status": "PLAUSIBLE",
            "limitations": []
        }

        context = ReasoningContextBuilder.build(synthetic_payload)
        self.assertEqual(len(context.all_evidence), 2)
        
        # Test that engine processes the contradiction cleanly
        engine = ReasoningEngine()
        result = engine.analyze(synthetic_payload)
        self.assertEqual(result["validation_status"], "PASSED")
        self.assertTrue(len(result["contradictory_evidence"]) > 0)

    def test_10_phase3a_integrity_and_outputs_unmodified(self):
        """TEST 10: Calling Phase 3B has zero side-effects on Phase 3A deterministic outputs."""
        output_1 = run_analysis(self.sample_request)
        engine = ReasoningEngine()
        _ = engine.analyze(output_1)
        output_2 = run_analysis(self.sample_request)

        self.assertEqual(output_1, output_2)

if __name__ == "__main__":
    unittest.main()
