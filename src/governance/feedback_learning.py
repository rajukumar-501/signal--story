"""
Context-Aware Analyst Feedback Learning Engine for Accenture Decision Intelligence Platform.
Implements bounded, deterministic, context-aware analyst feedback adjustments for driver prioritization.
Underlying evidence scores and frozen analytical core remain strictly immutable.
"""

import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
FEEDBACK_DIR = DATA_DIR / "feedback"
FEEDBACK_FILE = FEEDBACK_DIR / "analyst_feedback.jsonl"
SEMANTIC_DIR = DATA_DIR / "semantic"
CONTRACT_PATH = SEMANTIC_DIR / "feedback_learning_contract.json"


class FeedbackLearningEngine:
    """
    Manages analyst feedback collection, persistence in JSONL, contextual similarity matching,
    and bounded score adjustments for driver prioritization ranking.
    """
    def __init__(
        self,
        feedback_file: Optional[Path] = None,
        contract_path: Optional[Path] = None
    ):
        self.feedback_file = Path(feedback_file) if feedback_file else FEEDBACK_FILE
        self.contract_path = Path(contract_path) if contract_path else CONTRACT_PATH
        self._ensure_storage()
        self.contract = self._load_contract()
        self.params = self.contract.get("parameters", {
            "max_adjustment": 0.15,
            "min_adjustment": -0.15,
            "approval_boost": 0.08,
            "rejection_penalty": -0.10,
            "alternative_driver_boost": 0.08,
            "needs_more_evidence_adjustment": 0.0,
            "similarity_weights": {
                "exact_market_and_product": 1.0,
                "exact_market_and_category": 0.6,
                "exact_market_only": 0.3,
                "unrelated_context": 0.0
            }
        })

    def _ensure_storage(self):
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.feedback_file.exists():
            self.feedback_file.touch()

    def _load_contract(self) -> Dict[str, Any]:
        if self.contract_path.exists():
            try:
                with open(self.contract_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Reads all feedback events from JSONL store."""
        if not self.feedback_file.exists():
            return []
        records = []
        with open(self.feedback_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def record_feedback(
        self,
        scenario_id: str,
        predicted_driver: str,
        analyst_decision: str,
        reviewer: str = "Analyst",
        reason: str = "",
        alternative_driver: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Appends an analyst feedback event to the JSONL store.
        """
        analyst_decision = analyst_decision.upper().strip()
        if analyst_decision not in ["APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"]:
            raise ValueError(f"Invalid analyst decision: {analyst_decision}. Must be APPROVED, REJECTED, or NEEDS_MORE_EVIDENCE.")

        feedback_id = f"FB-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        event = {
            "feedback_id": feedback_id,
            "scenario_id": scenario_id,
            "predicted_driver": predicted_driver,
            "analyst_decision": analyst_decision,
            "alternative_driver": alternative_driver if analyst_decision == "REJECTED" else None,
            "reason": reason.strip(),
            "reviewer": reviewer.strip(),
            "timestamp": timestamp,
            "context": context or {}
        }

        # Write to JSONL
        with open(self.feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        return event

    def compute_contextual_similarity(
        self,
        target_context: Dict[str, Any],
        historical_context: Dict[str, Any]
    ) -> float:
        """
        Evaluates contextual similarity weight between target request and historical feedback event.
        - Exact market & product -> 1.0
        - Exact market & category -> 0.6
        - Exact market only -> 0.3
        - Unrelated context -> 0.0
        """
        t_mkt = target_context.get("market")
        h_mkt = historical_context.get("market")
        if not t_mkt or not h_mkt or t_mkt.lower() != h_mkt.lower():
            return 0.0

        t_prod = target_context.get("product_code")
        h_prod = historical_context.get("product_code")
        if t_prod and h_prod and t_prod == h_prod:
            return float(self.params["similarity_weights"].get("exact_market_and_product", 1.0))

        t_cat = target_context.get("category")
        h_cat = historical_context.get("category")
        if t_cat and h_cat and t_cat.lower() == h_cat.lower():
            return float(self.params["similarity_weights"].get("exact_market_and_category", 0.6))

        return float(self.params["similarity_weights"].get("exact_market_only", 0.3))

    def get_feedback_adjustments_for_context(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculates bounded cumulative adjustments for all drivers given the target context.
        """
        all_feedback = self.get_all_feedback()
        if not all_feedback:
            return {}

        driver_deltas: Dict[str, float] = {}

        for fb in all_feedback:
            hist_ctx = fb.get("context", {})
            sim_weight = self.compute_contextual_similarity(context, hist_ctx)
            if sim_weight <= 0.0:
                continue

            decision = fb.get("analyst_decision")
            pred_driver = fb.get("predicted_driver")
            alt_driver = fb.get("alternative_driver")

            if decision == "APPROVED" and pred_driver:
                boost = float(self.params.get("approval_boost", 0.08)) * sim_weight
                driver_deltas[pred_driver] = driver_deltas.get(pred_driver, 0.0) + boost

            elif decision == "REJECTED" and pred_driver:
                penalty = float(self.params.get("rejection_penalty", -0.10)) * sim_weight
                driver_deltas[pred_driver] = driver_deltas.get(pred_driver, 0.0) + penalty

                if alt_driver:
                    alt_boost = float(self.params.get("alternative_driver_boost", 0.08)) * sim_weight
                    driver_deltas[alt_driver] = driver_deltas.get(alt_driver, 0.0) + alt_boost

        # Clamp all adjustments strictly to [min_adjustment, max_adjustment]
        max_adj = float(self.params.get("max_adjustment", 0.15))
        min_adj = float(self.params.get("min_adjustment", -0.15))

        clamped_adjustments = {}
        for d, delta in driver_deltas.items():
            clamped = max(min(delta, max_adj), min_adj)
            clamped_adjustments[d] = round(clamped, 4)

        return clamped_adjustments

    def apply_feedback_learning_to_drivers(
        self,
        candidate_drivers: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Applies context-aware bounded adjustments to candidate drivers for prioritization ranking.
        Never modifies raw evidence scores.
        """
        adjustments = self.get_feedback_adjustments_for_context(context)
        adjusted_drivers = []

        for d in candidate_drivers:
            d_copy = dict(d)
            driver_name = d_copy.get("name") or d_copy.get("driver") or d_copy.get("driver_id")
            
            # Find adjustment matching driver name or ID
            adj = adjustments.get(driver_name, 0.0)
            if adj == 0.0 and d_copy.get("driver_id"):
                adj = adjustments.get(d_copy["driver_id"], 0.0)
            if adj == 0.0 and d_copy.get("driver"):
                adj = adjustments.get(d_copy["driver"], 0.0)

            # Safely parse numeric base score
            raw_val = d_copy.get("score") if d_copy.get("score") is not None else d_copy.get("composite_score", 0.0)
            try:
                base_score = float(raw_val)
            except (ValueError, TypeError):
                base_score = 0.0

            adjusted_score = max(min(base_score + adj, 100.0), 0.0)

            d_copy["base_score"] = round(base_score, 4)
            d_copy["feedback_adjustment"] = round(adj, 4)
            d_copy["feedback_adjusted_score"] = round(adjusted_score, 4)
            d_copy["score"] = round(adjusted_score, 4)  # For sorting prioritization
            adjusted_drivers.append(d_copy)

        # Sort by feedback_adjusted_score descending
        adjusted_drivers.sort(key=lambda x: x.get("feedback_adjusted_score", 0.0), reverse=True)

        learning_metadata = {
            "feedback_applied": len(adjustments) > 0,
            "active_adjustments_count": len(adjustments),
            "max_permitted_adjustment": self.params.get("max_adjustment", 0.15),
            "context_evaluated": context,
            "adjustments": adjustments,
            "governance_notice": "Analyst feedback influences driver prioritization ranking. Underlying evidence scores remain strictly immutable."
        }

        return adjusted_drivers, learning_metadata

    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Provides learning transparency view metrics.
        """
        all_feedback = self.get_all_feedback()
        approvals = sum(1 for fb in all_feedback if fb.get("analyst_decision") == "APPROVED")
        rejections = sum(1 for fb in all_feedback if fb.get("analyst_decision") == "REJECTED")
        needs_more = sum(1 for fb in all_feedback if fb.get("analyst_decision") == "NEEDS_MORE_EVIDENCE")

        reinforced_counts: Dict[str, int] = {}
        penalized_counts: Dict[str, int] = {}

        for fb in all_feedback:
            dec = fb.get("analyst_decision")
            pred = fb.get("predicted_driver")
            alt = fb.get("alternative_driver")
            if dec == "APPROVED" and pred:
                reinforced_counts[pred] = reinforced_counts.get(pred, 0) + 1
            elif dec == "REJECTED":
                if pred:
                    penalized_counts[pred] = penalized_counts.get(pred, 0) + 1
                if alt:
                    reinforced_counts[alt] = reinforced_counts.get(alt, 0) + 1

        top_reinforced = sorted(reinforced_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_penalized = sorted(penalized_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        total_events = len(all_feedback)
        validated_events = approvals + rejections
        acceptance_rate = round((approvals / max(1, validated_events)) * 100, 1) if validated_events > 0 else 100.0
        validation_rate = round((validated_events / max(1, total_events)) * 100, 1) if total_events > 0 else 100.0
        agreement_rate = round((approvals / max(1, total_events)) * 100, 1) if total_events > 0 else 100.0

        return {
            "total_feedback_events": total_events,
            "approvals_count": approvals,
            "rejections_count": rejections,
            "needs_more_evidence_count": needs_more,
            "historical_acceptance_rate_pct": acceptance_rate,
            "recommendation_validation_rate_pct": validation_rate,
            "driver_agreement_rate_pct": agreement_rate,
            "most_reinforced_drivers": [{"driver": k, "count": v} for k, v in top_reinforced],
            "most_penalized_drivers": [{"driver": k, "count": v} for k, v in top_penalized],
            "max_permitted_adjustment": float(self.params.get("max_adjustment", 0.15)),
            "min_permitted_adjustment": float(self.params.get("min_adjustment", -0.15)),
            "evidence_immutability_status": "LOCKED_UNCHANGED",
            "governance_rule": "Feedback only modifies driver prioritization ranking within ±0.15 bounds."
        }
