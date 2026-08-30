"""
Unit tests for Phase 3B.2 LLM Provider Abstraction, Configuration, and Fallback Behavior.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock

from src.phase3b.reasoning_provider import ReasoningProvider
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.llm_provider import (
    LLMReasoningProvider,
    LLMConfig,
    ProviderError,
    _extract_json
)
from src.phase3b.input_adapter import Phase3BInputAdapter
from src.phase3b.evidence_context import EvidenceContextBuilder

class TestPhase3B2Provider(unittest.TestCase):
    """Test suite for Phase 3B.2 provider abstraction."""

    def setUp(self):
        self.sample_3a_payload = {
            "scenario": {
                "scenario_id": "S001_TEST",
                "market": "South Korea",
                "product_code": "A6519160401",
                "category": "Electronics",
                "channel": "Online",
                "kpi": "gross_sales",
                "date": "2021-06-01"
            },
            "event": {
                "kpi": "gross_sales",
                "current_value": 150000.0,
                "previous_month_value": 200000.0,
                "baseline_value": 210000.0,
                "mom_change_percent": -0.25,
                "baseline_change_percent": -0.2857,
                "change_percent": -0.2857,
                "baseline_status": "SIGNIFICANT_DROP"
            },
            "candidate_hypotheses": [
                {
                    "driver": "DRIVER_04_RETURNS",
                    "rank": 1,
                    "score": 85.0,
                    "status": "STRONGLY_SUPPORTED",
                    "confidence": "HIGH",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "record_id": None,
                            "metric": "return_rate",
                            "value": 0.35,
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
                "established_driver": "DRIVER_04_RETURNS",
                "overall_status": "STRONGLY_SUPPORTED",
                "reason": "Elevated return rate observed.",
                "confidence": "HIGH"
            },
            "limitations": []
        }
        contract = Phase3BInputAdapter.from_phase3a_output(self.sample_3a_payload)
        self.context = EvidenceContextBuilder.build_context(contract)

    def test_provider_interface_polymorphism(self):
        """Verify that MockReasoningProvider and LLMReasoningProvider implement ReasoningProvider."""
        mock_p = MockReasoningProvider()
        llm_p = LLMReasoningProvider(LLMConfig(provider="mock"))
        
        self.assertIsInstance(mock_p, ReasoningProvider)
        self.assertIsInstance(llm_p, ReasoningProvider)

    def test_mock_provider_execution(self):
        """Verify MockReasoningProvider generates grounded, valid payload."""
        provider = MockReasoningProvider()
        output = provider.generate_diagnosis(self.context)
        
        self.assertIsInstance(output, dict)
        self.assertEqual(output["diagnosis"]["driver"], "DRIVER_04_RETURNS")
        self.assertEqual(output["diagnosis"]["status"], "STRONGLY_SUPPORTED")
        self.assertIn("claims", output)
        self.assertTrue(len(output["claims"]) > 0)
        self.assertEqual(output["claims"][0]["evidence_ids"], ["EVD-001"])

    def test_llm_config_env_defaults(self):
        """Verify LLMConfig correctly reads environment variables with safe defaults."""
        with patch.dict(os.environ, {
            "LLM_PROVIDER": "gemini",
            "LLM_MODEL": "gemini-1.5-pro",
            "GEMINI_API_KEY": "test-key-12345",
            "LLM_TEMPERATURE": "0.2"
        }, clear=True):
            cfg = LLMConfig.from_env()
            self.assertEqual(cfg.provider, "gemini")
            self.assertEqual(cfg.model, "gemini-1.5-pro")
            self.assertEqual(cfg.api_key, "test-key-12345")
            self.assertEqual(cfg.temperature, 0.2)
            self.assertEqual(cfg.timeout_seconds, 30.0)

    def test_missing_api_key_safe_fallback(self):
        """Verify that live provider with missing API key triggers deterministic fallback."""
        cfg = LLMConfig(provider="openai", api_key=None, enable_safe_fallback=True)
        provider = LLMReasoningProvider(config=cfg)
        
        output = provider.generate_diagnosis(self.context)
        self.assertIsInstance(output, dict)
        self.assertEqual(output["validation_status"], "FALLBACK_PRESERVED")
        self.assertEqual(output["diagnosis"]["driver"], "DRIVER_04_RETURNS")

    def test_missing_api_key_strict_error(self):
        """Verify that live provider with missing API key raises ProviderError when fallback disabled."""
        cfg = LLMConfig(provider="openai", api_key=None, enable_safe_fallback=False)
        provider = LLMReasoningProvider(config=cfg)
        
        with self.assertRaises(ProviderError):
            provider.generate_diagnosis(self.context)

    def test_custom_http_client_openai_invocation(self):
        """Verify custom HTTP caller receives properly formatted OpenAI-compatible request."""
        mock_response_json = json.dumps({
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "executive_summary": "Test summary",
                        "what_happened": "Sales dropped by 28%",
                        "diagnosis": {
                            "driver": "DRIVER_04_RETURNS",
                            "status": "STRONGLY_SUPPORTED",
                            "confidence": "HIGH"
                        },
                        "claims": [{
                            "claim": "Returns increased.",
                            "claim_type": "OBSERVATION",
                            "evidence_ids": ["EVD-001"]
                        }],
                        "supporting_evidence": [{
                            "evidence_id": "EVD-001",
                            "source_dataset": "fact_sales_monthly",
                            "metric": "return_rate",
                            "finding": "Elevated returns"
                        }],
                        "contradictory_evidence": [],
                        "uncertainties": [],
                        "recommended_next_steps": ["Inspect returns"],
                        "traceability": [{
                            "evidence_id": "EVD-001",
                            "source_dataset": "fact_sales_monthly",
                            "record_id": None
                        }]
                    })
                }
            }]
        }).encode("utf-8")

        captured_request = {}

        def mock_client(url, headers, body, timeout):
            captured_request["url"] = url
            captured_request["headers"] = headers
            captured_request["body"] = json.loads(body.decode("utf-8"))
            return mock_response_json

        cfg = LLMConfig(provider="openai", api_key="sk-test-key", model="gpt-4o")
        provider = LLMReasoningProvider(config=cfg, custom_http_client=mock_client)
        
        output = provider.generate_diagnosis(self.context)
        
        self.assertEqual(captured_request["url"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(captured_request["headers"]["Authorization"], "Bearer sk-test-key")
        self.assertEqual(captured_request["body"]["model"], "gpt-4o")
        self.assertEqual(captured_request["body"]["temperature"], 0.0)
        self.assertEqual(output["diagnosis"]["driver"], "DRIVER_04_RETURNS")

    def test_json_extractor_with_markdown_fences(self):
        """Verify _extract_json parses markdown-fenced codeblocks."""
        raw_md = "```json\n{\"test_key\": \"test_val\"}\n```"
        extracted = _extract_json(raw_md)
        self.assertEqual(extracted, {"test_key": "test_val"})

        raw_plain = "{\"test_key\": \"test_val2\"}"
        self.assertEqual(_extract_json(raw_plain), {"test_key": "test_val2"})

if __name__ == "__main__":
    unittest.main()
