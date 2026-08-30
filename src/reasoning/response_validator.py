"""
Response Validator for Phase 3B LLM Output.
Validates structural conformance, evidence citation integrity, anti-hallucination constraints,
and uncertainty preservation.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from .reasoning_context import ReasoningContext

ALLOWED_STATUSES: Set[str] = {"STRONGLY_SUPPORTED", "PLAUSIBLE", "NOT_ESTABLISHED"}
ALLOWED_CONFIDENCES: Set[str] = {"HIGH", "MEDIUM", "NONE"}

VALID_DRIVERS: Set[str] = {
    "DRIVER_01_INVENTORY",
    "DRIVER_02_PRICING",
    "DRIVER_03_MARKETING",
    "DRIVER_04_RETURNS",
    "DRIVER_05_SUPPORT",
    "DRIVER_06_CUSTOMER",
    "DRIVER_07_MARKET",
    "DRIVER_08_PRODUCT_MIX",
    "DRIVER_09_UNEXPLAINED"
}

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None

class ResponseValidator:
    """
    Validates LLM-generated reasoning output against schemas and evidence constraints.
    """

    @classmethod
    def validate(cls, raw_response: Any, context: ReasoningContext) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Parse JSON if string
        data: Dict[str, Any] = {}
        if isinstance(raw_response, str):
            clean_str = raw_response.strip()
            # Strip markdown codeblocks if present
            if clean_str.startswith("```json"):
                clean_str = clean_str[7:]
            elif clean_str.startswith("```"):
                clean_str = clean_str[3:]
            if clean_str.endswith("```"):
                clean_str = clean_str[:-3]
            clean_str = clean_str.strip()

            try:
                data = json.loads(clean_str)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Failed to parse JSON response: {str(e)}"],
                    validated_data=None
                )
        elif isinstance(raw_response, dict):
            data = raw_response
        else:
            return ValidationResult(
                is_valid=False,
                errors=["LLM response must be a JSON string or dict."],
                validated_data=None
            )

        # 2. Required Top-Level Fields
        required_fields = [
            "executive_summary",
            "what_happened",
            "diagnosis",
            "reasoning",
            "supporting_evidence",
            "contradictory_evidence",
            "uncertainties",
            "recommended_next_steps",
            "traceability"
        ]

        for req in required_fields:
            if req not in data:
                errors.append(f"Missing required response field: '{req}'")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, validated_data=None)

        # 3. Validate Diagnosis Structure
        diag = data.get("diagnosis", {})
        if not isinstance(diag, dict):
            errors.append("'diagnosis' field must be a dictionary.")
        else:
            driver = diag.get("driver")
            status = diag.get("status")
            confidence = diag.get("confidence")

            if driver is not None and driver not in VALID_DRIVERS:
                errors.append(f"Invalid driver '{driver}' in diagnosis.")

            if status not in ALLOWED_STATUSES:
                errors.append(f"Invalid status '{status}' in diagnosis. Must be one of {ALLOWED_STATUSES}")

            if confidence not in ALLOWED_CONFIDENCES:
                errors.append(f"Invalid confidence '{confidence}' in diagnosis. Must be one of {ALLOWED_CONFIDENCES}")

            # Uncertainty rule: if driver is null or status is NOT_ESTABLISHED, driver should be None
            if status == "NOT_ESTABLISHED" and driver is not None:
                errors.append("When status is 'NOT_ESTABLISHED', driver must be null (None).")

        # 4. Validate Evidence IDs & Traceability
        valid_evidence_ids = set(context.all_evidence.keys())
        cited_evidence_ids: Set[str] = set()

        # Check reasoning list
        reasoning_list = data.get("reasoning", [])
        if not isinstance(reasoning_list, list):
            errors.append("'reasoning' must be a list of reasoning items.")
        else:
            for idx, r_item in enumerate(reasoning_list):
                if not isinstance(r_item, dict):
                    errors.append(f"reasoning[{idx}] must be a dictionary.")
                    continue
                if "claim" not in r_item or "explanation" not in r_item:
                    errors.append(f"reasoning[{idx}] must contain 'claim' and 'explanation'.")
                ev_ids = r_item.get("evidence_ids", [])
                if not isinstance(ev_ids, list):
                    errors.append(f"reasoning[{idx}].evidence_ids must be a list.")
                else:
                    for eid in ev_ids:
                        cited_evidence_ids.add(eid)
                        if eid not in valid_evidence_ids:
                            errors.append(f"reasoning[{idx}] cites non-existent evidence_id '{eid}'.")

        # Check supporting evidence
        sup_ev_list = data.get("supporting_evidence", [])
        if not isinstance(sup_ev_list, list):
            errors.append("'supporting_evidence' must be a list.")
        else:
            for idx, ev in enumerate(sup_ev_list):
                if not isinstance(ev, dict):
                    errors.append(f"supporting_evidence[{idx}] must be a dict.")
                    continue
                eid = ev.get("evidence_id")
                if not eid or eid not in valid_evidence_ids:
                    errors.append(f"supporting_evidence[{idx}] cites non-existent evidence_id '{eid}'.")
                else:
                    cited_evidence_ids.add(eid)
                    actual_item = context.all_evidence[eid]
                    if ev.get("source_dataset") and ev.get("source_dataset") != actual_item.source_dataset:
                        errors.append(f"supporting_evidence[{idx}] dataset mismatch: cited '{ev.get('source_dataset')}', actual is '{actual_item.source_dataset}'.")

        # Check contradictory evidence
        con_ev_list = data.get("contradictory_evidence", [])
        if not isinstance(con_ev_list, list):
            errors.append("'contradictory_evidence' must be a list.")
        else:
            for idx, ev in enumerate(con_ev_list):
                if not isinstance(ev, dict):
                    errors.append(f"contradictory_evidence[{idx}] must be a dict.")
                    continue
                eid = ev.get("evidence_id")
                if not eid or eid not in valid_evidence_ids:
                    errors.append(f"contradictory_evidence[{idx}] cites non-existent evidence_id '{eid}'.")
                else:
                    cited_evidence_ids.add(eid)

        # Check traceability
        trace_list = data.get("traceability", [])
        if not isinstance(trace_list, list):
            errors.append("'traceability' must be a list.")
        else:
            for idx, tr in enumerate(trace_list):
                if not isinstance(tr, dict):
                    errors.append(f"traceability[{idx}] must be a dict.")
                    continue
                eid = tr.get("evidence_id")
                if not eid or eid not in valid_evidence_ids:
                    errors.append(f"traceability[{idx}] cites non-existent evidence_id '{eid}'.")
                else:
                    cited_evidence_ids.add(eid)

        # 5. Deterministic Gating Preservation Rule
        # If deterministic diagnosis was NOT_ESTABLISHED due to baseline failure or 0 score,
        # LLM must not fabricate certainty unless valid multi-source evidence is present in candidates
        det_status = context.deterministic_diagnosis.overall_status
        if det_status == "NOT_ESTABLISHED" and context.event.baseline_status != "VALID":
            if diag.get("status") != "NOT_ESTABLISHED":
                errors.append("Cannot establish a root cause when baseline_status is invalid.")

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=data if is_valid else None
        )
