"""
Unit tests for Phase 3B.2 Prompt Construction and Anti-Leakage Rules.
"""

import unittest
import json

from src.phase3b.input_adapter import Phase3BInputAdapter
from src.phase3b.evidence_context import EvidenceContextBuilder
from src.phase3b.prompts import (
    build_system_prompt,
    build_user_prompt,
    build_reasoning_prompt_payload
)

class TestPhase3B2Prompts(unittest.TestCase):
    """Test suite for prompt builder and grounding rules."""

    def setUp(self):
        self.sample_payload = {
            "scenario": {
                "scenario_id": "TEST_SCENARIO_100",
                "market": "China",
                "product_code": "P_99812",
                "category": "Appliances",
                "channel": "Retail",
                "kpi": "gross_sales",
                "date": "2021-05-01"
            },
            "event": {
                "kpi": "gross_sales",
                "current_value": 450000.0,
                "previous_month_value": 600000.0,
                "baseline_value": 620000.0,
                "mom_change_percent": -0.25,
                "baseline_change_percent": -0.2742,
                "change_percent": -0.2742,
                "baseline_status": "SIGNIFICANT_DROP"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_03_MARKETING",
                    "rank": 1,
                    "score": 88.0,
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
                        },
                        {
                            "source_dataset": "fact_crm_notes",
                            "record_id": "CRM-5542",
                            "metric": "customer_sentiment",
                            "value": "Customers noted lack of campaign discounts.",
                            "evidence_role": "SUPPORTING",
                            "temporal_alignment": "DURING"
                        }
                    ],
                    "contradictions": [],
                    "evidence_source_count": 2,
                    "supporting_source_count": 2,
                    "supporting_evidence_count": 2
                }
            ],
            "diagnosis": {
                "established_driver": "DRIVER_03_MARKETING",
                "overall_status": "STRONGLY_SUPPORTED",
                "reason": "Marketing budget cut 75% preceding the drop.",
                "confidence": "HIGH"
            },
            "limitations": []
        }
        self.contract = Phase3BInputAdapter.from_phase3a_output(self.sample_payload)
        self.context = EvidenceContextBuilder.build_context(self.contract)

    def test_system_prompt_grounding_rules(self):
        """Verify system prompt contains all mandatory safety and evidence rules."""
        sys_prompt = build_system_prompt()
        
        # Check required grounding terms
        self.assertIn("EVIDENCE GROUNDING & LINEAGE", sys_prompt)
        self.assertIn("COMPETING-HYPOTHESIS ARBITRATION", sys_prompt)
        self.assertIn("CLAIM CLASSIFICATION", sys_prompt)
        self.assertIn("OBSERVATION", sys_prompt)
        self.assertIn("INTERPRETATION", sys_prompt)
        self.assertIn("CAUSAL_CONCLUSION", sys_prompt)
        self.assertIn("RECOMMENDATION", sys_prompt)
        self.assertIn("UNCERTAINTY & GATING", sys_prompt)
        self.assertIn("NOT_ESTABLISHED", sys_prompt)
        self.assertIn("UNTRUSTED DATA SANDBOXING", sys_prompt)
        self.assertIn("<UNTRUSTED_EVIDENCE_RECORD>", sys_prompt)

    def test_user_prompt_contains_evidence_catalog_and_sandboxing(self):
        """Verify user prompt correctly formats telemetry and sandboxes CRM text."""
        user_prompt = build_user_prompt(self.context)
        
        self.assertIn("## 1. OBSERVED BUSINESS EVENT", user_prompt)
        self.assertIn("## 2. INVESTIGATED CANDIDATE HYPOTHESES", user_prompt)
        self.assertIn("## 3. EVIDENCE CATALOG", user_prompt)
        self.assertIn("EVD-001", user_prompt)
        self.assertIn("EVD-002", user_prompt)
        
        # Verify untrusted text is sandboxed
        self.assertIn('<UNTRUSTED_EVIDENCE_RECORD evidence_id="EVD-002" source="fact_crm_notes" classification="DATA_NOT_INSTRUCTION">', user_prompt)
        self.assertIn("Customers noted lack of campaign discounts.", user_prompt)

    def test_zero_scenario_tuning_in_prompts(self):
        """Verify prompt templates do NOT contain hardcoded S001-S008 answer keys or scenario mappings."""
        sys_prompt = build_system_prompt()
        user_prompt = build_user_prompt(self.context)
        
        forbidden_strings = [
            "S001 = returns",
            "S002 = customer",
            "S003 = marketing",
            "S004 = pricing",
            "S005 = support",
            "S006 = mix",
            "S007 = mix",
            "S008 = not_established",
            "expected_driver",
            "ground_truth.csv",
            "evaluation_ground_truth"
        ]

        for s in forbidden_strings:
            self.assertNotIn(s.lower(), sys_prompt.lower())
            self.assertNotIn(s.lower(), user_prompt.lower())

    def test_build_reasoning_prompt_payload_structure(self):
        """Verify inspectable prompt payload structure."""
        payload = build_reasoning_prompt_payload(self.context)
        
        self.assertIn("system_prompt", payload)
        self.assertIn("user_prompt", payload)
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(len(payload["approved_drivers"]), 8)

if __name__ == "__main__":
    unittest.main()
