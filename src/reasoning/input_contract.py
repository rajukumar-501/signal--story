"""
Phase 3B Input Contract & Ingestion Boundary.
Enforces strict segregation between Phase 3A deterministic output and forbidden oracle/ground-truth data.
"""

from typing import Dict, Any, List, Set

FORBIDDEN_GROUND_TRUTH_KEYS: Set[str] = {
    "true_root_cause",
    "root_cause_status",
    "expected_driver",
    "expected_established_driver",
    "expected_status",
    "scenario_truth",
    "ground_truth",
    "oracle_driver",
    "target_cause"
}

REQUIRED_PAYLOAD_KEYS: Set[str] = {
    "event",
    "candidate_hypotheses",
    "diagnosis"
}

class InputContractError(ValueError):
    """Raised when an input payload violates the Phase 3B ingestion contract."""
    pass

class InputContractValidator:
    """
    Validates that incoming payloads to Phase 3B conform to the Phase 3A output contract
    and do NOT contain any evaluation ground-truth data or oracle labels.
    """

    @classmethod
    def validate(cls, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise InputContractError("Phase 3B payload must be a dictionary.")

        # 1. Check for forbidden ground truth keys at top level
        for key in payload.keys():
            if key in FORBIDDEN_GROUND_TRUTH_KEYS:
                raise InputContractError(f"Forbidden ground-truth key detected in Phase 3B payload: '{key}'")

        # 2. Check for required top-level keys
        for req_key in REQUIRED_PAYLOAD_KEYS:
            if req_key not in payload:
                raise InputContractError(f"Missing required Phase 3A contract key: '{req_key}'")

        # 3. Check for forbidden keys inside nested structures
        cls._check_nested_for_ground_truth(payload)

    @classmethod
    def _check_nested_for_ground_truth(cls, data: Any, path: str = "root") -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                if k in FORBIDDEN_GROUND_TRUTH_KEYS:
                    raise InputContractError(f"Forbidden ground-truth key detected at {path}.{k}")
                cls._check_nested_for_ground_truth(v, f"{path}.{k}")
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                cls._check_nested_for_ground_truth(item, f"{path}[{idx}]")
