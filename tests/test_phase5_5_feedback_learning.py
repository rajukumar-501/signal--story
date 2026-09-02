"""
Tests for Phase 5.5 Context-Aware Analyst Feedback Learning.
Verifies bounded adjustments, contextual isolation, persistence,
immutable evidence protection, and safety authority.
"""

import unittest
import json
import tempfile
from pathlib import Path
from src.governance.feedback_learning import FeedbackLearningEngine
from src.server import execute_decision_analysis

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestPhase55FeedbackLearning(unittest.TestCase):
    """Test suite for Context-Aware Analyst Feedback Learning Engine."""

    def setUp(self):
        # Use a temporary JSONL file for test isolation
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_feedback_file = Path(self.temp_dir.name) / "test_feedback.jsonl"
        self.engine = FeedbackLearningEngine(feedback_file=self.temp_feedback_file)
        self.context_s003 = {
            "market": "China",
            "product_code": "A2520150501",
            "category": "Mouse",
            "date": "2021-04-01",
            "kpi_context": "gross_sales"
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_zero_feedback_produces_zero_adjustment(self):
        """Verify that zero historical feedback produces zero score adjustments."""
        adjs = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(len(adjs), 0)

        # Test applying to candidate drivers
        raw_drivers = [
            {"driver": "DRIVER_03_MARKETING", "score": 6.0},
            {"driver": "DRIVER_02_PRICING", "score": 2.0}
        ]
        adj_drivers, meta = self.engine.apply_feedback_learning_to_drivers(raw_drivers, self.context_s003)
        self.assertFalse(meta["feedback_applied"])
        self.assertEqual(adj_drivers[0]["base_score"], 6.0)
        self.assertEqual(adj_drivers[0]["feedback_adjustment"], 0.0)
        self.assertEqual(adj_drivers[0]["feedback_adjusted_score"], 6.0)

    def test_02_approval_produces_bounded_positive_adjustment(self):
        """Verify approval produces a bounded positive boost (+0.08 default)."""
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="APPROVED",
            reviewer="Senior Analyst",
            reason="Confirmed marketing efficiency breakdown",
            context=self.context_s003
        )
        adjs = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs.get("DRIVER_03_MARKETING"), 0.08)

    def test_03_rejection_produces_bounded_negative_adjustment(self):
        """Verify rejection produces a bounded penalty (-0.10 default)."""
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="REJECTED",
            reviewer="Senior Analyst",
            reason="Telemetry does not show sufficient customer impact",
            context=self.context_s003
        )
        adjs = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs.get("DRIVER_03_MARKETING"), -0.10)

    def test_04_adjustment_never_exceeds_configured_maximum_bounds(self):
        """Verify cumulative feedback is strictly clamped to [-0.15, +0.15]."""
        # Record 5 consecutive approvals
        for _ in range(5):
            self.engine.record_feedback(
                scenario_id="S003",
                predicted_driver="DRIVER_03_MARKETING",
                analyst_decision="APPROVED",
                reviewer="Analyst",
                context=self.context_s003
            )
        adjs = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs.get("DRIVER_03_MARKETING"), 0.15)  # Clamped to max_adjustment

        # Record 5 consecutive rejections
        for _ in range(5):
            self.engine.record_feedback(
                scenario_id="S003",
                predicted_driver="DRIVER_02_PRICING",
                analyst_decision="REJECTED",
                reviewer="Analyst",
                context=self.context_s003
            )
        adjs2 = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs2.get("DRIVER_02_PRICING"), -0.15)  # Clamped to min_adjustment

    def test_05_rejected_driver_with_alternative_boosts_alternative(self):
        """Verify alternative driver is boosted when original is rejected."""
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="REJECTED",
            alternative_driver="DRIVER_02_PRICING",
            reviewer="Analyst",
            context=self.context_s003
        )
        adjs = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs.get("DRIVER_03_MARKETING"), -0.10)
        self.assertEqual(adjs.get("DRIVER_02_PRICING"), 0.08)

    def test_06_contextual_similarity_weights(self):
        """Verify contextual similarity decaying across market/product scopes."""
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="APPROVED",
            context=self.context_s003
        )

        # 1. Exact match (China, A2520150501) -> weight 1.0 -> boost = 0.08
        adj_exact = self.engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adj_exact.get("DRIVER_03_MARKETING"), 0.08)

        # 2. Same market & category, different product (China, A9999999999, Mouse) -> weight 0.6 -> boost = 0.048
        cat_ctx = {"market": "China", "product_code": "A9999999999", "category": "Mouse"}
        adj_cat = self.engine.get_feedback_adjustments_for_context(cat_ctx)
        self.assertAlmostEqual(adj_cat.get("DRIVER_03_MARKETING"), 0.048, places=3)

        # 3. Same market only, different category (China, Keyboard) -> weight 0.3 -> boost = 0.024
        mkt_ctx = {"market": "China", "product_code": "A8888888888", "category": "Keyboard"}
        adj_mkt = self.engine.get_feedback_adjustments_for_context(mkt_ctx)
        self.assertAlmostEqual(adj_mkt.get("DRIVER_03_MARKETING"), 0.024, places=3)

        # 4. Unrelated market (Germany) -> weight 0.0 -> boost = 0.0
        unrelated_ctx = {"market": "Germany", "product_code": "A2520150501", "category": "Mouse"}
        adj_unrelated = self.engine.get_feedback_adjustments_for_context(unrelated_ctx)
        self.assertEqual(len(adj_unrelated), 0)

    def test_07_underlying_evidence_scores_remain_immutable(self):
        """Verify feedback adjustment NEVER modifies underlying evidence scores."""
        raw_drivers = [
            {"driver": "DRIVER_03_MARKETING", "score": 6.0, "evidence": [{"metric": "spend", "value": 1641.07}]}
        ]
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="APPROVED",
            context=self.context_s003
        )
        adj_drivers, meta = self.engine.apply_feedback_learning_to_drivers(raw_drivers, self.context_s003)
        
        # Raw evidence score intact
        self.assertEqual(raw_drivers[0]["score"], 6.0)
        self.assertEqual(raw_drivers[0]["evidence"][0]["value"], 1641.07)
        self.assertEqual(adj_drivers[0]["base_score"], 6.0)
        self.assertEqual(adj_drivers[0]["feedback_adjustment"], 0.08)
        self.assertEqual(adj_drivers[0]["feedback_adjusted_score"], 6.08)

    def test_08_persistence_across_engine_reinstantiation(self):
        """Verify feedback events persist on disk in JSONL and reload on restart."""
        self.engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="APPROVED",
            reviewer="Analyst 1",
            context=self.context_s003
        )
        # Create a new engine instance pointing to the same file
        reloaded_engine = FeedbackLearningEngine(feedback_file=self.temp_feedback_file)
        adjs = reloaded_engine.get_feedback_adjustments_for_context(self.context_s003)
        self.assertEqual(adjs.get("DRIVER_03_MARKETING"), 0.08)
        self.assertEqual(len(reloaded_engine.get_all_feedback()), 1)

    def test_09_learning_summary_transparency_metrics(self):
        """Verify learning summary provides accurate transparency metrics."""
        self.engine.record_feedback("S003", "DRIVER_03_MARKETING", "APPROVED", context=self.context_s003)
        self.engine.record_feedback("S003", "DRIVER_01_INVENTORY", "REJECTED", alternative_driver="DRIVER_02_PRICING", context=self.context_s003)
        self.engine.record_feedback("S003", "DRIVER_04_RETURNS", "NEEDS_MORE_EVIDENCE", context=self.context_s003)

        summary = self.engine.get_learning_summary()
        self.assertEqual(summary["total_feedback_events"], 3)
        self.assertEqual(summary["approvals_count"], 1)
        self.assertEqual(summary["rejections_count"], 1)
        self.assertEqual(summary["needs_more_evidence_count"], 1)
        self.assertEqual(summary["max_permitted_adjustment"], 0.15)


if __name__ == "__main__":
    unittest.main()
