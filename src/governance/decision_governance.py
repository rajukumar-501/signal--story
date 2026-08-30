"""
Phase 5.2D — Decision Actionability, Operational Safety & Human Oversight Engine.
Provides deterministic action safety classification, operational risk scoring,
decision preconditions ("Before acting"), causal language precision,
and human-in-the-loop analyst review state management.
Completely outside the frozen analytical core.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTION_CONTRACT_PATH = PROJECT_ROOT / "Data" / "semantic" / "decision_action_contract.json"

# In-memory analyst review session store for prototype demonstration
_ANALYST_REVIEW_STORE: Dict[str, Dict[str, Any]] = {}


class DecisionGovernanceEngine:
    """
    Deterministic enterprise decision actionability and safety engine.
    Maps analytical diagnosis drivers to structured decision metadata,
    preconditions, operational risk tiers, and human review states.
    """

    def __init__(self, contract_path: Optional[Path] = None):
        self.contract_path = Path(contract_path) if contract_path else ACTION_CONTRACT_PATH
        self.contract = self._load_contract()

    def _load_contract(self) -> Dict[str, Any]:
        if self.contract_path.exists():
            try:
                return json.loads(self.contract_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def get_driver_governance(self, driver_id: Optional[str]) -> Dict[str, Any]:
        """Retrieves governance specification for a specific candidate driver."""
        driver_rules = self.contract.get("driver_governance", {})
        if not driver_id or driver_id == "UNCERTAIN" or driver_id == "DRIVER_08_INCONCLUSIVE":
            return driver_rules.get("DRIVER_08_INCONCLUSIVE", {})
        return driver_rules.get(driver_id, driver_rules.get("DRIVER_08_INCONCLUSIVE", {}))

    def evaluate_decision_governance(
        self,
        p3a_payload: Dict[str, Any],
        p3b_payload: Dict[str, Any],
        scenario_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates operational safety, risk level, preconditions, and human oversight
        for an analytical diagnosis result.
        """
        diag = p3b_payload.get("diagnosis", {}) if p3b_payload else {}
        diag_status = diag.get("status", "PLAUSIBLE")
        raw_driver = diag.get("driver")

        # Map to driver rule
        if diag_status == "NOT_ESTABLISHED" or not raw_driver:
            driver_rule = self.get_driver_governance("DRIVER_08_INCONCLUSIVE")
            is_inconclusive = True
        else:
            driver_rule = self.get_driver_governance(raw_driver)
            is_inconclusive = False

        # Precision Causal Language Statements
        driver_name = driver_rule.get("driver_name", "Primary Operational Driver")
        if is_inconclusive:
            finding_statement = "Diagnostic evaluation concludes no single internal operational driver accounts for the anomaly."
            why_it_matters = "Variance reflects broad external macroeconomic movements rather than localized operational failure."
            causal_class = "INCONCLUSIVE_OBSERVATION"
        else:
            finding_statement = f"{driver_name} is the strongest supported explanation for the observed performance anomaly."
            why_it_matters = "Multi-dataset evidence corroborates meaningful variance aligned with the anomaly window."
            causal_class = driver_rule.get("causal_language_class", "SUPPORTED_INFERENCE")

        # Retrieve or initialize human review state
        sec_key = scenario_id or "S003"
        human_review = _ANALYST_REVIEW_STORE.get(sec_key, {
            "status": "NOT_REVIEWED",
            "reviewer": None,
            "decision": None,
            "timestamp": None,
            "notes": None
        })

        return {
            "driver_id": driver_rule.get("driver_id", "DRIVER_08_INCONCLUSIVE"),
            "driver_name": driver_name,
            "recommended_action": driver_rule.get("recommended_action", "Conduct cross-functional operational review."),
            "expected_business_effect": driver_rule.get("expected_business_effect", "Maintain operational stability."),
            "safety_classification": driver_rule.get("safety_classification", "REQUIRES_HUMAN_APPROVAL"),
            "risk_level": driver_rule.get("risk_level", "MEDIUM"),
            "risk_rationale": driver_rule.get("risk_rationale", "Operational changes require domain validation."),
            "prerequisites": driver_rule.get("prerequisites", [
                "Confirm underlying anomaly metrics in source ERP",
                "Validate supporting evidence across peer tables",
                "Obtain domain owner approval before execution"
            ]),
            "operational_risks": driver_rule.get("operational_risks", [
                "Unintended revenue or customer experience disruption",
                "Resource misallocation if external factors shift"
            ]),
            "affected_business_area": driver_rule.get("affected_business_area", "Commercial Operations"),
            "reversibility": driver_rule.get("reversibility", "MEDIUM"),
            "required_owner": driver_rule.get("required_owner", "Commercial Operations Lead"),
            "approval_required": driver_rule.get("approval_required", True),
            "execution_status": driver_rule.get("execution_status", "Advisory Decision Support — Human Approval Required"),
            "causal_language_class": causal_class,
            "finding_statement": finding_statement,
            "why_it_matters": why_it_matters,
            "human_review": human_review,
            "governance_disclaimer": "Signal Story provides evidence-grounded decision support. Recommendations require appropriate business validation and do not constitute automatic execution."
        }

    def record_human_review(
        self,
        scenario_id: str,
        status: str,
        reviewer: str = "Lead Commercial Analyst",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records an analyst review decision in session memory."""
        valid_statuses = {"NOT_REVIEWED", "REVIEWED", "APPROVED", "REJECTED", "NEEDS_MORE_EVIDENCE"}
        clean_status = status.upper() if status.upper() in valid_statuses else "REVIEWED"

        record = {
            "status": clean_status,
            "reviewer": reviewer,
            "decision": clean_status,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "notes": notes or f"Analyst marked scenario {scenario_id} as {clean_status}."
        }
        _ANALYST_REVIEW_STORE[scenario_id] = record
        return record


# Singleton helper
_decision_governance_instance = None


def get_decision_governance_engine() -> DecisionGovernanceEngine:
    global _decision_governance_instance
    if _decision_governance_instance is None:
        _decision_governance_instance = DecisionGovernanceEngine()
    return _decision_governance_instance


def evaluate_decision_governance(
    p3a_payload: Dict[str, Any],
    p3b_payload: Dict[str, Any],
    scenario_id: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience helper to evaluate decision governance."""
    engine = get_decision_governance_engine()
    return engine.evaluate_decision_governance(p3a_payload, p3b_payload, scenario_id=scenario_id)


def record_analyst_review(
    scenario_id: str,
    status: str,
    reviewer: str = "Lead Commercial Analyst",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience helper to record human-in-the-loop review."""
    engine = get_decision_governance_engine()
    return engine.record_human_review(scenario_id, status, reviewer=reviewer, notes=notes)
