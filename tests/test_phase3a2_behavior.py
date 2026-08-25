import unittest
import pandas as pd
import numpy as np
from pathlib import Path
from dateutil.relativedelta import relativedelta

from src.analytics.data_model import AnalyticalDataModel
from src.analytics.event_detector import EventDetector
from src.analytics.driver_generator import DriverGenerator
from src.analytics.evidence_scorer import EvidenceScorer
from src.analytics.contradiction_engine import ContradictionEngine
from src.analytics.driver_ranker import DriverRanker
from src.analytics.run_analysis import run_analysis

class TestPhase3A2Behavior(unittest.TestCase):
    def setUp(self):
        self.dm = AnalyticalDataModel()

    def test_01_global_decline_alone_no_market_cause(self):
        """TEST 1: Global decline alone does not establish market cause."""
        # Query S008 Germany where the entire company declined similarly
        request = {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"}
        result = run_analysis(request)
        
        # Verify DRIVER_07_MARKET is not supported/plausible
        market_cands = [c for c in result["candidate_drivers"] if c["driver"] == "DRIVER_07_MARKET"]
        if market_cands:
            self.assertIn(market_cands[0]["status"], ["NOT_ESTABLISHED"])

    def test_02_market_specific_underperformance(self):
        """TEST 2: Market-specific underperformance can establish a market candidate."""
        # Find a case where a market underperformed compared to rest of company.
        # We can construct a mock evaluation payload or verify if S002/S003 behavior maps.
        # S002 South Korea 2021-01-01 or S005 Indonesia 2020-03-01
        # Let's test the generator's _generate_market_candidate directly with custom event data
        detector = EventDetector(self.dm)
        # South Korea gross sales in Jan 2021 declined compared to flat/stable rest of company
        event = {
            "request": {"market": "South Korea", "date": "2021-01-01", "kpi": "gross_sales"},
            "current_value": 2407142.76,
            "rolling_3m_baseline": 4725995.53,
            "baseline_status": "VALID",
            "kpi": "gross_sales"
        }
        generator = DriverGenerator(self.dm)
        cand = generator._generate_market_candidate(event)
        self.assertIsNotNone(cand)
        # Since South Korea dropped significantly relative to peers, it should trigger signal
        self.assertNotEqual(cand["temporal_alignment"], "NO_CLEAR_ALIGNMENT")

    def test_03_category_request_filters_category(self):
        """TEST 3: Category request actually filters category."""
        sales = self.dm.get_joined_sales()
        request = {"market": "India", "category": "Processors", "date": "2020-03-01", "kpi": "gross_sales"}
        
        # Apply scope filtering
        scoped_sales = self.dm.apply_scope(sales, request)
        
        # Verify all rows belong to category Processors and market India
        categories = scoped_sales["category"].dropna().unique()
        markets = scoped_sales["market"].dropna().unique()
        
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], "Processors")
        self.assertEqual(len(markets), 1)
        self.assertEqual(markets[0], "India")

    def test_04_product_request_filters_product(self):
        """TEST 4: Product request actually filters product."""
        sales = self.dm.get_joined_sales()
        request = {"market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales"}
        
        # Apply scope filtering
        scoped_sales = self.dm.apply_scope(sales, request)
        
        # Verify all rows belong to product_code A2520150501
        products = scoped_sales["product_code"].dropna().unique()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], "A2520150501")

    def test_05_outcome_evidence_alone_cannot_produce_strongly_supported(self):
        """TEST 5: Outcome evidence alone cannot produce STRONGLY_SUPPORTED."""
        # Create a candidate with only outcome evidence
        cand = {
            "driver": "DRIVER_01_INVENTORY",
            "driver_change_pct": 0.5,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_sales_monthly", "evidence_role": "OUTCOME", "metric": "gross_sales", "value": 1000.0}
            ]
        }
        
        scored = EvidenceScorer.score_candidates([cand])
        ranked = DriverRanker.rank_candidates(scored)
        
        self.assertEqual(ranked[0]["status"], "NOT_ESTABLISHED")

    def test_06_contradictory_evidence_reduces_confidence(self):
        """TEST 6: Contradictory evidence reduces driver confidence."""
        # Pricing candidate with high signal but Cheaper pricing contradiction
        cand = {
            "driver": "DRIVER_02_PRICING",
            "driver_change_pct": 0.3,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_competitor_pricing_monthly", "evidence_role": "SUPPORTING", "metric": "price_gap_percent", "value": 0.08},
                {"source_dataset": "fact_competitor_pricing_monthly", "evidence_role": "CONTRADICTORY", "metric": "price_gap_percent", "value": -0.02}
            ]
        }
        
        scored = EvidenceScorer.score_candidates([cand])
        contradictor = ContradictionEngine(self.dm)
        # Run contradiction engine to apply penalties
        resolved = contradictor.evaluate_contradictions(scored, {"request": {"date": "2021-01-01"}})
        ranked = DriverRanker.rank_candidates(resolved)
        
        self.assertEqual(ranked[0]["status"], "NOT_ESTABLISHED")

    def test_07_multiple_independent_datasets_increase_corroboration(self):
        """TEST 7: Multiple independent datasets increase corroboration."""
        # Candidate with 1 source
        cand1 = {
            "driver": "DRIVER_05_SUPPORT",
            "driver_change_pct": 0.3,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "ticket_volume", "value": 10}
            ]
        }
        
        # Candidate with 2 independent sources
        cand2 = {
            "driver": "DRIVER_05_SUPPORT",
            "driver_change_pct": 0.3,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "ticket_volume", "value": 10},
                {"source_dataset": "fact_crm_notes", "evidence_role": "SUPPORTING", "metric": "crm_note_complaint", "value": 2}
            ]
        }
        
        scored = EvidenceScorer.score_candidates([cand1, cand2])
        
        self.assertGreater(scored[1]["base_score"], scored[0]["base_score"])
        self.assertEqual(scored[1]["evidence_source_count"], 2)

    def test_08_multiple_rows_same_dataset_no_corroboration_double_count(self):
        """TEST 8: Multiple rows from the same dataset do not count as multiple independent sources."""
        cand = {
            "driver": "DRIVER_05_SUPPORT",
            "driver_change_pct": 0.3,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "sentiment_negative", "value": 1.0},
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "sentiment_negative", "value": 1.0},
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "ticket_volume", "value": 15.0}
            ]
        }
        
        scored = EvidenceScorer.score_candidates([cand])
        
        # source count should be exactly 1
        self.assertEqual(scored[0]["evidence_source_count"], 1)

    def test_09_post_event_evidence_no_causal_support(self):
        """TEST 9: Post-event evidence does not receive strong causal support."""
        cand = {
            "driver": "DRIVER_01_INVENTORY",
            "driver_change_pct": 0.5,
            "temporal_alignment": "AFTER",
            "evidence": [
                {"source_dataset": "fact_inventory_monthly", "evidence_role": "SUPPORTING", "metric": "stockout_flag", "value": 1.0}
            ]
        }
        
        scored = EvidenceScorer.score_candidates([cand])
        ranked = DriverRanker.rank_candidates(scored)
        
        self.assertEqual(ranked[0]["status"], "NOT_ESTABLISHED")
        self.assertEqual(ranked[0]["final_score"], 0.0)

    def test_10_no_driver_specific_evidence_returns_not_established(self):
        """TEST 10: No driver-specific evidence returns NOT_ESTABLISHED."""
        request = {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"}
        result = run_analysis(request)
        
        # Since S008 has no driver-specific anomalies, overall status must be NOT_ESTABLISHED
        self.assertEqual(result["overall_status"], "NOT_ESTABLISHED")

if __name__ == "__main__":
    unittest.main()
