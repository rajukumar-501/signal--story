"""
Phase 3B.4 Generalized Evidence-Arbitration & Causal Reasoning Test Suite.
Tests domain-agnostic causal arbitration principles (Tests A-J) and
synthetic generalization holdout configurations (zero scenario-specific overfitting).
"""

import unittest
from typing import Dict, Any, List
from datetime import datetime, timezone

from src.phase3b.input_adapter import (
    Phase3BInputContract,
    ScenarioRequest,
    AnomalyEvent,
    CandidateHypothesis,
    Phase3ADiagnosis
)
from src.phase3b.evidence_context import EvidenceContextBuilder, EvidenceItem
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.validator import Phase3BResponseValidator
from src.phase3b.engine import Phase3BReasoningEngine


def create_synthetic_contract(
    kpi: str = "gross_sales",
    market: str = "Synthetic_Market_Alpha",
    product_code: str = "PROD_999",
    category: str = "Peripherals",
    overall_status: str = "PLAUSIBLE",
    established_driver: str = "DRIVER_01_INVENTORY",
    hypotheses: List[Dict[str, Any]] = None
) -> Phase3BInputContract:
    """Helper to build synthetic test contracts for domain-agnostic reasoning tests."""
    req = ScenarioRequest(
        market=market,
        product_code=product_code,
        category=category,
        channel="Retailer",
        date="2022-01-01"
    )
    event = AnomalyEvent(
        kpi=kpi,
        current_value=100000.0,
        previous_month_value=150000.0,
        baseline_value=145000.0,
        mom_change_percent=-0.3333,
        baseline_change_percent=-0.3103,
        change_percent=-0.3333,
        baseline_status="CRITICAL_ANOMALY"
    )

    diag = Phase3ADiagnosis(
        established_driver=established_driver,
        overall_status=overall_status,
        reason="Synthetic diagnostic evaluation rule.",
        confidence="MEDIUM"
    )

    
    cand_objs = []
    for rank, h in enumerate(hypotheses or [], 1):
        cand_objs.append(CandidateHypothesis(
            driver=h["driver"],
            rank=rank,
            score=h["score"],
            status=h.get("status", "PLAUSIBLE"),
            confidence=h.get("confidence", "MEDIUM"),
            temporal_alignment=h.get("temporal_alignment", "DURING"),
            evidence=h.get("evidence", []),
            contradictions=h.get("contradictions", [])
        ))

    return Phase3BInputContract(
        schema_version="1.0.0",
        phase3a_baseline="3A.3-SYNTHETIC",
        timestamp=datetime.now(timezone.utc).isoformat(),
        request=req,
        event=event,
        candidate_hypotheses=cand_objs,
        diagnosis=diag,
        limitations=[]
    )


class TestPhase3B4ReasoningArbitration(unittest.TestCase):
    """
    Generalized unit tests verifying cross-source evidence arbitration principles (Tests A through J).
    """

    def setUp(self):
        self.provider = MockReasoningProvider()
        self.engine = Phase3BReasoningEngine(default_provider=self.provider)

    def test_a_stronger_candidate_beats_weaker_candidate(self):
        """Test A: A candidate with exact scope, leading timing, and multi-source corroboration outranks a weaker candidate."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_03_MARKETING",
                    "score": 10.0,
                    "temporal_alignment": "AFTER",
                    "evidence": [
                        {
                            "source_dataset": "fact_marketing_monthly",
                            "metric": "spend_drop",
                            "value": -15.0,
                            "temporal_alignment": "AFTER",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": None
                        }
                    ]
                },
                {
                    "driver": "DRIVER_04_RETURNS",
                    "score": 8.0,
                    "temporal_alignment": "BEFORE",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "return_rate",
                            "value": 25.0,
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        },
                        {
                            "source_dataset": "fact_support_tickets",
                            "metric": "return_complaints",
                            "value": "Defective units returned in mass",
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        val = Phase3BResponseValidator.validate(res, context)
        self.assertTrue(val.is_valid, f"Validation failed: {val.errors}")

        # Returns should win over Marketing due to exact scope, BEFORE timing, and 2 distinct datasets
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_04_RETURNS")
        self.assertEqual(res["diagnosis"]["status"], "STRONGLY_SUPPORTED")
        self.assertIn("DRIVER_04_RETURNS was selected", res["why_selected"])

    def test_b_same_source_duplication_does_not_create_false_corroboration(self):
        """Test B: 10 records from the same dataset must equal 1 independent source, not 10 independent sources."""
        many_same_source = [
            {
                "source_dataset": "fact_sales_monthly",
                "metric": f"metric_{i}",
                "value": float(i * 10),
                "temporal_alignment": "DURING",
                "evidence_role": "SUPPORTING",
                "market": "AlphaMarket",
                "product_code": "SKU_100"
            }
            for i in range(10)
        ]
        two_different_sources = [
            {
                "source_dataset": "fact_sales_monthly",
                "metric": "metric_a",
                "value": 10.0,
                "temporal_alignment": "DURING",
                "evidence_role": "SUPPORTING",
                "market": "AlphaMarket",
                "product_code": "SKU_100"
            },
            {
                "source_dataset": "fact_support_tickets",
                "metric": "metric_b",
                "value": "Outage reported",
                "temporal_alignment": "DURING",
                "evidence_role": "SUPPORTING",
                "market": "AlphaMarket",
                "product_code": "SKU_100"
            }
        ]

        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_01_INVENTORY",
                    "score": 9.0,
                    "evidence": many_same_source
                },
                {
                    "driver": "DRIVER_05_SUPPORT",
                    "score": 9.0,
                    "evidence": two_different_sources
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        
        # Candidate comparisons must reflect distinct dataset counts: 1 vs 2
        inv_comp = next(c for c in res["candidate_comparisons"] if c["driver"] == "DRIVER_01_INVENTORY")
        sup_comp = next(c for c in res["candidate_comparisons"] if c["driver"] == "DRIVER_05_SUPPORT")
        self.assertEqual(inv_comp["independent_source_count"], 1)
        self.assertEqual(sup_comp["independent_source_count"], 2)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_05_SUPPORT")

    def test_c_post_event_evidence_is_penalized(self):
        """Test C: Evidence occurring AFTER the outcome cannot be treated as a primary cause."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_02_PRICING",
                    "score": 10.0,
                    "temporal_alignment": "AFTER",
                    "evidence": [
                        {
                            "source_dataset": "fact_competitor_pricing_monthly",
                            "metric": "discount_after_drop",
                            "value": -20.0,
                            "temporal_alignment": "AFTER",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                },
                {
                    "driver": "DRIVER_08_PRODUCT_MIX",
                    "score": 8.0,
                    "temporal_alignment": "BEFORE",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "mix_shift",
                            "value": -15.0,
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_08_PRODUCT_MIX")

    def test_d_global_movement_does_not_establish_local_market_cause(self):
        """Test D: When evidence indicates broad global market movement without internal operational drivers, status must be NOT_ESTABLISHED."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            overall_status="NOT_ESTABLISHED",
            established_driver=None,
            hypotheses=[
                {
                    "driver": "DRIVER_07_MARKET",
                    "score": 5.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "global_market_drop",
                            "value": -10.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "Global",
                            "product_code": None
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertIsNone(res["diagnosis"]["driver"])
        self.assertEqual(res["diagnosis"]["status"], "NOT_ESTABLISHED")

    def test_e_scope_mismatch_is_penalized(self):
        """Test E: Evidence from another unrelated product or market must be penalized."""
        contract = create_synthetic_contract(
            market="TargetMarket",
            product_code="TargetSKU",
            hypotheses=[
                {
                    "driver": "DRIVER_01_INVENTORY",
                    "score": 10.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "stockout",
                            "value": 100.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "DifferentMarket",
                            "product_code": "DifferentSKU"
                        }
                    ]
                },
                {
                    "driver": "DRIVER_02_PRICING",
                    "score": 8.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_competitor_pricing_monthly",
                            "metric": "price_gap",
                            "value": 15.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "TargetMarket",
                            "product_code": "TargetSKU"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_02_PRICING")

    def test_f_contradictory_evidence_reduces_confidence(self):
        """Test F: A hypothesis with contradictory evidence records loses score and confidence."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_03_MARKETING",
                    "score": 12.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_marketing_monthly",
                            "metric": "campaign_spend",
                            "value": -10.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        },
                        {
                            "source_dataset": "fact_marketing_monthly",
                            "metric": "impressions_growth",
                            "value": 45.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "CONTRADICTORY",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ],
                    "contradictions": ["Positive impression growth contradicts marketing collapse."]
                },
                {
                    "driver": "DRIVER_04_RETURNS",
                    "score": 8.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "return_rate",
                            "value": 30.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_04_RETURNS")

    def test_g_magnitude_matters(self):
        """Test G: Significant anomaly signal is properly captured and explained."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_05_SUPPORT",
                    "score": 15.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_support_tickets",
                            "metric": "ticket_surge",
                            "value": 450.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_05_SUPPORT")
        self.assertTrue(len(res["supporting_evidence"]) > 0)

    def test_h_independent_corroboration_matters(self):
        """Test H: Multi-dataset corroboration increases confidence to STRONGLY_SUPPORTED."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_06_CUSTOMER",
                    "score": 10.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_crm_notes",
                            "metric": "dispute_note",
                            "value": "Major customer contract dispute",
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        },
                        {
                            "source_dataset": "fact_support_tickets",
                            "metric": "customer_escalation",
                            "value": "Tier 1 customer cancelled order",
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_06_CUSTOMER")
        self.assertEqual(res["diagnosis"]["status"], "STRONGLY_SUPPORTED")
        self.assertEqual(res["diagnosis"]["confidence"], "HIGH")

    def test_i_insufficient_evidence_means_uncertainty(self):
        """Test I: When evidence is insufficient or diagnosis is NOT_ESTABLISHED, model returns null driver and NOT_ESTABLISHED status."""
        contract = create_synthetic_contract(
            market="Uncertain_Market",
            overall_status="NOT_ESTABLISHED",
            established_driver=None,
            hypotheses=[]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        val = Phase3BResponseValidator.validate(res, context)
        self.assertTrue(val.is_valid)
        self.assertIsNone(res["diagnosis"]["driver"])
        self.assertEqual(res["diagnosis"]["status"], "NOT_ESTABLISHED")

    def test_j_candidate_comparison_is_explicit(self):
        """Test J: Output response includes candidate_comparisons, why_selected, and why_alternatives_rejected."""
        contract = create_synthetic_contract(
            market="AlphaMarket",
            product_code="SKU_100",
            hypotheses=[
                {
                    "driver": "DRIVER_01_INVENTORY",
                    "score": 10.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "stockout",
                            "value": 5.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                },
                {
                    "driver": "DRIVER_02_PRICING",
                    "score": 8.0,
                    "evidence": [
                        {
                            "source_dataset": "fact_competitor_pricing_monthly",
                            "metric": "competitor_undercut",
                            "value": -15.0,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "AlphaMarket",
                            "product_code": "SKU_100"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        self.assertIn("candidate_comparisons", res)
        self.assertGreater(len(res["candidate_comparisons"]), 0)
        self.assertIn("why_selected", res)
        self.assertIn("why_alternatives_rejected", res)


class TestPhase3B4GeneralizationHoldout(unittest.TestCase):
    """
    GENERALIZATION TEST SUITE:
    Evaluates synthetic holdout scenarios not present in official S001-S008 benchmarks.
    Verifies that reasoning arbitration functions reliably on unseen scopes and data profiles.
    """

    def setUp(self):
        self.provider = MockReasoningProvider()

    def test_generalization_holdout_1_cross_channel_conflict(self):
        """[GENERALIZATION TEST] E-commerce vs Retailer channel dispute."""
        contract = create_synthetic_contract(
            kpi="gross_sales",
            market="Japan",
            category="Displays",
            product_code="DSP_400",
            hypotheses=[
                {
                    "driver": "DRIVER_02_PRICING",
                    "score": 11.0,
                    "temporal_alignment": "AFTER",
                    "evidence": [
                        {
                            "source_dataset": "fact_competitor_pricing_monthly",
                            "metric": "price_change_late",
                            "value": -5.0,
                            "temporal_alignment": "AFTER",
                            "evidence_role": "SUPPORTING",
                            "market": "Japan",
                            "product_code": "DSP_400"
                        }
                    ]
                },
                {
                    "driver": "DRIVER_05_SUPPORT",
                    "score": 9.0,
                    "temporal_alignment": "BEFORE",
                    "evidence": [
                        {
                            "source_dataset": "fact_support_tickets",
                            "metric": "firmware_ticket_surge",
                            "value": "Major firmware bug crashing displays",
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "Japan",
                            "product_code": "DSP_400"
                        },
                        {
                            "source_dataset": "fact_sales_calls",
                            "metric": "retailer_complaint",
                            "value": "Retailer refusing to take more stock due to firmware",
                            "temporal_alignment": "BEFORE",
                            "evidence_role": "SUPPORTING",
                            "market": "Japan",
                            "product_code": "DSP_400"
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        val = Phase3BResponseValidator.validate(res, context)
        self.assertTrue(val.is_valid)
        self.assertEqual(res["diagnosis"]["driver"], "DRIVER_05_SUPPORT")
        self.assertEqual(res["diagnosis"]["status"], "STRONGLY_SUPPORTED")

    def test_generalization_holdout_2_macro_recession_inconclusive(self):
        """[GENERALIZATION TEST] Multi-category macro slump with zero localized operational signals."""
        contract = create_synthetic_contract(
            kpi="gross_sales",
            market="United Kingdom",
            category="Laptops",
            overall_status="NOT_ESTABLISHED",
            established_driver=None,
            hypotheses=[
                {
                    "driver": "DRIVER_07_MARKET",
                    "score": 4.0,
                    "temporal_alignment": "DURING",
                    "evidence": [
                        {
                            "source_dataset": "fact_sales_monthly",
                            "metric": "macro_gdp_slowdown",
                            "value": -2.5,
                            "temporal_alignment": "DURING",
                            "evidence_role": "SUPPORTING",
                            "market": "Global",
                            "product_code": None
                        }
                    ]
                }
            ]
        )
        context = EvidenceContextBuilder.build(contract)
        res = self.provider.generate_diagnosis(context)
        val = Phase3BResponseValidator.validate(res, context)
        self.assertTrue(val.is_valid)
        self.assertIsNone(res["diagnosis"]["driver"])
        self.assertEqual(res["diagnosis"]["status"], "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
