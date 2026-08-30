import unittest
import pandas as pd
from dateutil.relativedelta import relativedelta

from src.analytics.data_model import AnalyticalDataModel
from src.analytics.event_detector import EventDetector
from src.analytics.driver_generator import DriverGenerator
from src.analytics.evidence_scorer import EvidenceScorer
from src.analytics.contradiction_engine import ContradictionEngine
from src.analytics.driver_ranker import DriverRanker
from src.analytics.diagnosis import DiagnosisGate, DiagnosisFormatter
from src.analytics.run_analysis import run_analysis

class TestPhase3A3DiagnosisContract(unittest.TestCase):
    def setUp(self):
        self.dm = AnalyticalDataModel()

    def test_01_weak_candidate_not_established_diagnosis(self):
        """TEST 1: Weak candidate != established diagnosis."""
        weak_cand = {
            "driver": "DRIVER_06_CUSTOMER",
            "score": 1.0,
            "final_score": 1.0,
            "status": "NOT_ESTABLISHED",
            "confidence": "NONE",
            "supporting_evidence_count": 1,
            "contradictory_evidence_count": 0,
            "temporal_alignment": "DURING",
            "evidence": []
        }
        event = {"baseline_status": "VALID", "kpi": "gross_sales"}
        diagnosis = DiagnosisGate.evaluate(event, [weak_cand])
        
        self.assertIsNone(diagnosis["established_driver"])
        self.assertEqual(diagnosis["overall_status"], "NOT_ESTABLISHED")
        self.assertEqual(diagnosis["confidence"], "NONE")

    def test_02_outcome_evidence_alone_cannot_establish_driver(self):
        """TEST 2: Outcome evidence alone cannot establish a driver."""
        outcome_cand = {
            "driver": "DRIVER_01_INVENTORY",
            "driver_change_pct": 0.5,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_sales_monthly", "evidence_role": "OUTCOME", "metric": "gross_sales", "value": 1000.0}
            ]
        }
        scored = EvidenceScorer.score_candidates([outcome_cand])
        ranked = DriverRanker.rank_candidates(scored)
        event = {"baseline_status": "VALID", "kpi": "gross_sales"}
        diagnosis = DiagnosisGate.evaluate(event, ranked)
        
        self.assertIsNone(diagnosis["established_driver"])
        self.assertEqual(diagnosis["overall_status"], "NOT_ESTABLISHED")

    def test_03_s008_produces_null_established_driver(self):
        """TEST 3: S008 produces established_driver = null, overall_status = NOT_ESTABLISHED."""
        request = {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"}
        res = run_analysis(request)
        
        self.assertIn("diagnosis", res)
        self.assertIn("candidate_hypotheses", res)
        self.assertIsNone(res["diagnosis"]["established_driver"])
        self.assertEqual(res["diagnosis"]["overall_status"], "NOT_ESTABLISHED")
        self.assertGreater(len(res["candidate_hypotheses"]), 0)

    def test_04_strong_driver_specific_candidate_established(self):
        """TEST 4: A strong driver-specific candidate can become established."""
        strong_cand = {
            "driver": "DRIVER_03_MARKETING",
            "score": 6.0,
            "final_score": 6.0,
            "status": "PLAUSIBLE",
            "confidence": "MEDIUM",
            "supporting_evidence_count": 2,
            "contradictory_evidence_count": 0,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_marketing_monthly", "evidence_role": "SUPPORTING", "metric": "spend_change", "value": 0.3}
            ]
        }
        event = {"baseline_status": "VALID", "kpi": "gross_sales"}
        diagnosis = DiagnosisGate.evaluate(event, [strong_cand])
        
        self.assertEqual(diagnosis["established_driver"], "DRIVER_03_MARKETING")
        self.assertEqual(diagnosis["overall_status"], "PLAUSIBLE")
        self.assertEqual(diagnosis["confidence"], "MEDIUM")

    def test_05_contradictions_prevent_unsupported_establishment(self):
        """TEST 5: Contradictions prevent unsupported establishment."""
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
        resolved = contradictor.evaluate_contradictions(scored, {"request": {"date": "2021-01-01"}})
        ranked = DriverRanker.rank_candidates(resolved)
        event = {"baseline_status": "VALID", "kpi": "gross_sales"}
        diagnosis = DiagnosisGate.evaluate(event, ranked)
        
        self.assertIsNone(diagnosis["established_driver"])
        self.assertEqual(diagnosis["overall_status"], "NOT_ESTABLISHED")

    def test_06_after_only_evidence_cannot_establish_causality(self):
        """TEST 6: AFTER-only evidence cannot establish causality."""
        after_cand = {
            "driver": "DRIVER_01_INVENTORY",
            "driver_change_pct": 0.5,
            "temporal_alignment": "AFTER",
            "evidence": [
                {"source_dataset": "fact_inventory_monthly", "evidence_role": "SUPPORTING", "metric": "stockout_flag", "value": 1.0}
            ]
        }
        scored = EvidenceScorer.score_candidates([after_cand])
        ranked = DriverRanker.rank_candidates(scored)
        event = {"baseline_status": "VALID", "kpi": "gross_sales"}
        diagnosis = DiagnosisGate.evaluate(event, ranked)
        
        self.assertIsNone(diagnosis["established_driver"])
        self.assertEqual(diagnosis["overall_status"], "NOT_ESTABLISHED")

    def test_07_two_independent_datasets_increase_corroboration(self):
        """TEST 7: Two independent datasets can increase corroboration."""
        cand1 = {
            "driver": "DRIVER_05_SUPPORT",
            "driver_change_pct": 0.3,
            "temporal_alignment": "DURING",
            "evidence": [
                {"source_dataset": "fact_support_tickets", "evidence_role": "SUPPORTING", "metric": "ticket_volume", "value": 10}
            ]
        }
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

    def test_08_repeated_records_same_dataset_no_source_inflation(self):
        """TEST 8: Repeated records from one dataset do not increase independent source count."""
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
        self.assertEqual(scored[0]["evidence_source_count"], 1)

    def test_09_category_scope_respected(self):
        """TEST 9: Category scope remains respected."""
        sales = self.dm.get_joined_sales()
        request = {"market": "India", "category": "Processors", "date": "2020-03-01", "kpi": "gross_sales"}
        scoped_sales = self.dm.apply_scope(sales, request)
        
        categories = scoped_sales["category"].dropna().unique()
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], "Processors")

    def test_10_product_scope_respected(self):
        """TEST 10: Product scope remains respected."""
        sales = self.dm.get_joined_sales()
        request = {"market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales"}
        scoped_sales = self.dm.apply_scope(sales, request)
        
        products = scoped_sales["product_code"].dropna().unique()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0], "A2520150501")

    def test_11_market_peer_comparison_respected(self):
        """TEST 11: Market peer comparison remains respected."""
        generator = DriverGenerator(self.dm)
        # Germany 2020-03-01 where rest of company dropped equally
        event = {
            "request": {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"},
            "current_value": 38357.61,
            "rolling_3m_baseline": 423842.74,
            "baseline_status": "VALID",
            "kpi": "gross_sales"
        }
        cand = generator._generate_market_candidate(event)
        # Because rest of company also dropped ~86%, Germany is not market driver
        self.assertEqual(cand["temporal_alignment"], "NO_CLEAR_ALIGNMENT")

    def test_12_engine_remains_deterministic(self):
        """TEST 12: Engine remains deterministic."""
        request = {"market": "Germany", "date": "2020-03-01", "kpi": "gross_sales"}
        res1 = run_analysis(request)
        res2 = run_analysis(request)
        self.assertEqual(res1, res2)

if __name__ == "__main__":
    unittest.main()
