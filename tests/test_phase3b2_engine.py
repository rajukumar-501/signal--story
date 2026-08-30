"""
Integration tests for Phase 3B.2 Reasoning Engine, Pipeline Orchestrator, and Fallback Handling.
"""

import unittest
import json

from src.phase3b.engine import Phase3BReasoningEngine, run_phase3b_pipeline
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.llm_provider import LLMReasoningProvider, LLMConfig

class TestPhase3B2Engine(unittest.TestCase):
    """Integration test suite for Phase 3B Reasoning Pipeline."""

    def setUp(self):
        self.sample_established_payload = {
            "scenario": {
                "scenario_id": "S003_TEST",
                "market": "China",
                "product_code": "A2520150501",
                "category": "Electronics",
                "channel": "Retail",
                "kpi": "gross_sales",
                "date": "2021-05-01"
            },
            "event": {
                "kpi": "gross_sales",
                "current_value": 300000.0,
                "previous_month_value": 450000.0,
                "baseline_value": 470000.0,
                "mom_change_percent": -0.3333,
                "baseline_change_percent": -0.3617,
                "change_percent": -0.3617,
                "baseline_status": "SIGNIFICANT_DROP"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_03_MARKETING",
                    "rank": 1,
                    "score": 90.0,
                    "status": "STRONGLY_SUPPORTED",
                    "confidence": "HIGH",
                    "evidence": [
                        {
                            "source_dataset": "fact_marketing_monthly",
                            "record_id": None,
                            "metric": "spend",
                            "value": 1000.0,
                            "evidence_role": "SUPPORTING",
                            "temporal_alignment": "BEFORE"
                        }
                    ],
                    "contradictions": [],
                    "evidence_source_count": 1,
                    "supporting_source_count": 1,
                    "supporting_evidence_count": 1
                }
            ],
            "diagnosis": {
                "established_driver": "DRIVER_03_MARKETING",
                "overall_status": "STRONGLY_SUPPORTED",
                "reason": "Marketing budget slashed 80%.",
                "confidence": "HIGH"
            },
            "limitations": []
        }

        self.sample_uncertain_payload = {
            "scenario": {
                "scenario_id": "S008_TEST",
                "market": "Germany",
                "product_code": None,
                "category": None,
                "channel": None,
                "kpi": "gross_sales",
                "date": "2021-04-01"
            },
            "event": {
                "kpi": "gross_sales",
                "current_value": 500000.0,
                "previous_month_value": 600000.0,
                "baseline_value": 610000.0,
                "mom_change_percent": -0.1667,
                "baseline_change_percent": -0.1803,
                "change_percent": -0.1803,
                "baseline_status": "MODERATE_DROP"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_06_CUSTOMER",
                    "rank": 1,
                    "score": 40.0,
                    "status": "PLAUSIBLE",
                    "confidence": "MEDIUM",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "record_id": None,
                            "metric": "customer_count",
                            "value": 450.0,
                            "evidence_role": "CONTEXT",
                            "temporal_alignment": "DURING"
                        }
                    ],
                    "contradictions": [],
                    "evidence_source_count": 1,
                    "supporting_source_count": 0,
                    "supporting_evidence_count": 0
                }
            ],
            "diagnosis": {
                "established_driver": None,
                "overall_status": "NOT_ESTABLISHED",
                "reason": "Confounded by macro-market trends.",
                "confidence": "NONE"
            },
            "limitations": []
        }

    def test_pipeline_execution_with_mock_provider(self):
        """Verify standard end-to-end execution passes validation."""
        engine = Phase3BReasoningEngine(default_provider=MockReasoningProvider())
        report, val_res = engine.run(self.sample_established_payload)
        
        self.assertTrue(val_res.is_valid)
        self.assertEqual(report["validation_status"], "PASSED")
        self.assertEqual(report["diagnosis"]["driver"], "DRIVER_03_MARKETING")
        self.assertEqual(report["diagnosis"]["status"], "STRONGLY_SUPPORTED")
        self.assertIn("pipeline_latency_ms", report)

    def test_pipeline_execution_with_uncertainty(self):
        """Verify S008 uncertainty payload produces valid NOT_ESTABLISHED diagnosis."""
        engine = Phase3BReasoningEngine(default_provider=MockReasoningProvider())
        report, val_res = engine.run(self.sample_uncertain_payload)
        
        self.assertTrue(val_res.is_valid)
        self.assertEqual(report["validation_status"], "PASSED")
        self.assertIsNone(report["diagnosis"]["driver"])
        self.assertEqual(report["diagnosis"]["status"], "NOT_ESTABLISHED")

    def test_pipeline_fallback_on_invalid_driver(self):
        """Verify pipeline falls back safely if model outputs an unapproved driver ID."""
        bad_response = {
            "executive_summary": "Bad summary",
            "what_happened": "Sales dropped",
            "diagnosis": {
                "driver": "DRIVER_INVALID_ALIEN_INVASION",
                "status": "STRONGLY_SUPPORTED",
                "confidence": "HIGH"
            },
            "claims": [{"claim": "Alien invasion", "claim_type": "OBSERVATION", "evidence_ids": ["EVD-001"]}],
            "supporting_evidence": [{"evidence_id": "EVD-001", "source_dataset": "fact_marketing_monthly", "metric": "spend", "finding": "Cut"}],
            "contradictory_evidence": [],
            "uncertainties": [],
            "recommended_next_steps": [],
            "traceability": [{"evidence_id": "EVD-001", "source_dataset": "fact_marketing_monthly", "record_id": None}]
        }
        
        mock_bad_provider = MockReasoningProvider(custom_response=bad_response)
        engine = Phase3BReasoningEngine(default_provider=mock_bad_provider)
        report, val_res = engine.run(self.sample_established_payload)
        
        self.assertFalse(val_res.is_valid)
        self.assertEqual(report["validation_status"], "FALLBACK_PRESERVED")
        # Preserves Phase 3A deterministic diagnosis
        self.assertEqual(report["diagnosis"]["driver"], "DRIVER_03_MARKETING")
        self.assertIn("validation_errors", report)

    def test_pipeline_fallback_on_hallucinated_evidence_id(self):
        """Verify pipeline falls back safely if model cites non-existent evidence IDs."""
        bad_response = {
            "executive_summary": "Hallucinated citation",
            "what_happened": "Sales dropped",
            "diagnosis": {
                "driver": "DRIVER_03_MARKETING",
                "status": "STRONGLY_SUPPORTED",
                "confidence": "HIGH"
            },
            "claims": [{"claim": "Marketing drop", "claim_type": "OBSERVATION", "evidence_ids": ["EVD-999"]}],
            "supporting_evidence": [{"evidence_id": "EVD-999", "source_dataset": "fact_marketing_monthly", "metric": "spend", "finding": "Cut"}],
            "contradictory_evidence": [],
            "uncertainties": [],
            "recommended_next_steps": [],
            "traceability": [{"evidence_id": "EVD-999", "source_dataset": "fact_marketing_monthly", "record_id": None}]
        }
        
        mock_bad_provider = MockReasoningProvider(custom_response=bad_response)
        engine = Phase3BReasoningEngine(default_provider=mock_bad_provider)
        report, val_res = engine.run(self.sample_established_payload)
        
        self.assertFalse(val_res.is_valid)
        self.assertEqual(report["validation_status"], "FALLBACK_PRESERVED")
        self.assertEqual(report["diagnosis"]["driver"], "DRIVER_03_MARKETING")

    def test_run_phase3b_pipeline_convenience_function(self):
        """Verify run_phase3b_pipeline helper function."""
        report = run_phase3b_pipeline(self.sample_established_payload, provider=MockReasoningProvider())
        self.assertEqual(report["validation_status"], "PASSED")
        self.assertEqual(report["diagnosis"]["driver"], "DRIVER_03_MARKETING")

if __name__ == "__main__":
    unittest.main()
