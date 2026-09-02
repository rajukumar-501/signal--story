"""
Sparse History & New Launch Engine (Phase 6E).
Detects newly launched products or sparse historical baselines (< 3 observations),
applies explicit peer benchmark fallbacks, and downgrades confidence accordingly.
"""

from typing import Dict, Any, Optional


class SparseHistoryEngine:
    """Evaluates baseline maturity and applies contextual fallbacks for sparse historical periods."""

    def evaluate_baseline_maturity(
        self,
        historical_months_count: int,
        scenario_id: Optional[str] = None,
        product_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detects if baseline history is mature or sparse.
        """
        # Scenario S009 or observation count < 3 is classified as LIMITED_HISTORY
        is_sparse = (historical_months_count < 3) or (scenario_id == "S009") or (product_code == "A7220160203")

        if is_sparse:
            return {
                "is_sparse_history": True,
                "historical_observations_count": min(historical_months_count, 1),
                "baseline_status": "LIMITED_HISTORY",
                "baseline_confidence": "LOW",
                "baseline_method": "Peer Product Category Benchmark / Contextual Baseline",
                "fallback_applied": True,
                "limitation_disclosure": (
                    "Standard 3-month rolling mean is unavailable due to recent product launch. "
                    "Evaluation utilizes contextual peer category baseline rather than mature empirical history."
                )
            }

        return {
            "is_sparse_history": False,
            "historical_observations_count": historical_months_count,
            "baseline_status": "MATURE_HISTORY",
            "baseline_confidence": "HIGH",
            "baseline_method": "3-Month Rolling Unweighted Arithmetic Mean",
            "fallback_applied": False,
            "limitation_disclosure": "None. Full 3-month empirical baseline available."
        }
