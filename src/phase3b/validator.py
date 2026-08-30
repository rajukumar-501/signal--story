"""
Deterministic Response Validator for Phase 3B.
Enforces schema compliance, driver catalog integrity, claim-level evidence citations,
traceability verification, and uncertainty gating without depending on an LLM.
"""

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from .evidence_context import EvidenceContext, EvidenceItem
from .input_adapter import Phase3BInputAdapter

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_data: Optional[Dict[str, Any]] = None

class Phase3BResponseValidator:
    """
    Deterministic Safety & Grounding Boundary for Phase 3B.
    Validates model diagnostic outputs against the authoritative EvidenceContext.
    """

    ALLOWED_CLAIM_TYPES = {
        "OBSERVATION",
        "INTERPRETATION",
        "CAUSAL_CONCLUSION",
        "RECOMMENDATION"
    }

    ALLOWED_STATUSES = {
        "STRONGLY_SUPPORTED",
        "PLAUSIBLE",
        "NOT_ESTABLISHED"
    }

    ALLOWED_CONFIDENCES = {
        "HIGH",
        "MEDIUM",
        "NONE"
    }

    REQUIRED_TOP_LEVEL_KEYS = [
        "executive_summary",
        "what_happened",
        "diagnosis",
        "supporting_evidence",
        "contradictory_evidence",
        "uncertainties",
        "recommended_next_steps",
        "traceability"
    ]

    @classmethod
    def validate(cls, raw_output: Union[Dict[str, Any], str], context: EvidenceContext) -> ValidationResult:
        """
        Executes full deterministic validation on the raw LLM response against the EvidenceContext.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Parse JSON / Dict
        data: Dict[str, Any] = {}
        if isinstance(raw_output, str):
            try:
                data = json.loads(raw_output)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"JSONDecodeError: Response is not valid JSON ({str(e)})"]
                )
        elif isinstance(raw_output, dict):
            data = raw_output
        else:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid response type: Expected dict or JSON string, got {type(raw_output).__name__}"]
            )

        # 2. Top-Level Keys Check
        for key in cls.REQUIRED_TOP_LEVEL_KEYS:
            if key not in data:
                errors.append(f"Missing required top-level key '{key}'.")

        # Claims / Reasoning check
        claims = data.get("claims", data.get("reasoning", []))
        if not isinstance(claims, list):
            errors.append("Key 'claims' (or 'reasoning') must be a list.")

        # 3. Diagnosis Block Validation
        diagnosis = data.get("diagnosis")
        if not isinstance(diagnosis, dict):
            errors.append("Key 'diagnosis' must be a dictionary.")
        else:
            driver = diagnosis.get("driver")
            status = diagnosis.get("status")
            confidence = diagnosis.get("confidence")

            if driver is not None and driver not in Phase3BInputAdapter.APPROVED_DRIVERS:
                errors.append(f"Invalid driver identifier '{driver}'. Must be one of approved 8 drivers or null.")

            if status not in cls.ALLOWED_STATUSES:
                errors.append(f"Invalid status '{status}'. Must be one of {sorted(cls.ALLOWED_STATUSES)}.")

            if confidence not in cls.ALLOWED_CONFIDENCES:
                errors.append(f"Invalid confidence '{confidence}'. Must be one of {sorted(cls.ALLOWED_CONFIDENCES)}.")

            # Uncertainty Gating Check: If Phase 3A deterministic status is NOT_ESTABLISHED, model must NOT establish driver
            if context.diagnosis.overall_status == "NOT_ESTABLISHED":
                if driver is not None:
                    errors.append(f"Gating violation: Phase 3A status is NOT_ESTABLISHED, but response established driver '{driver}'.")
                if status != "NOT_ESTABLISHED":
                    errors.append(f"Gating violation: Phase 3A status is NOT_ESTABLISHED, but response reported status '{status}'.")

        # 4. Build Context Evidence ID Map
        valid_evidence_ids = {e.evidence_id: e for e in context.all_evidence}

        # 5. Claim-Level Validation
        if isinstance(claims, list):
            for i, claim_item in enumerate(claims):
                if not isinstance(claim_item, dict):
                    errors.append(f"Claim at index {i} must be a dictionary.")
                    continue

                claim_text = claim_item.get("claim")
                claim_type = claim_item.get("claim_type", "INTERPRETATION")
                ev_ids = claim_item.get("evidence_ids", [])

                if not claim_text or not isinstance(claim_text, str):
                    errors.append(f"Claim at index {i} missing substantive 'claim' text.")

                if claim_type not in cls.ALLOWED_CLAIM_TYPES:
                    errors.append(f"Claim at index {i} has invalid claim_type '{claim_type}'. Must be one of {sorted(cls.ALLOWED_CLAIM_TYPES)}.")

                if not isinstance(ev_ids, list):
                    errors.append(f"Claim at index {i} 'evidence_ids' must be a list.")
                    continue

                # Causal & Observation claims MUST cite at least one valid evidence ID
                if claim_type in {"OBSERVATION", "CAUSAL_CONCLUSION"} and len(ev_ids) == 0:
                    errors.append(f"Claim at index {i} of type '{claim_type}' has 0 evidence citations (unsupported claim).")

                for eid in ev_ids:
                    if eid not in valid_evidence_ids:
                        errors.append(f"Claim at index {i} cites non-existent evidence_id '{eid}'.")

        # 6. Supporting & Contradictory Evidence Citations Check
        for list_name in ["supporting_evidence", "contradictory_evidence"]:
            ev_list = data.get(list_name, [])
            if isinstance(ev_list, list):
                for i, item in enumerate(ev_list):
                    if not isinstance(item, dict):
                        errors.append(f"{list_name}[{i}] must be a dict.")
                        continue
                    eid = item.get("evidence_id")
                    source = item.get("source_dataset")
                    
                    if not eid or eid not in valid_evidence_ids:
                        errors.append(f"{list_name}[{i}] cites invalid/non-existent evidence_id '{eid}'.")
                    else:
                        real_item = valid_evidence_ids[eid]
                        if source and source != real_item.source_dataset:
                            errors.append(f"{list_name}[{i}] source mismatch: cited '{source}' but {eid} belongs to '{real_item.source_dataset}'.")

        # 7. Traceability Check
        traceability = data.get("traceability", [])
        if isinstance(traceability, list):
            for i, t in enumerate(traceability):
                if isinstance(t, dict):
                    eid = t.get("evidence_id")
                    if eid and eid not in valid_evidence_ids:
                        errors.append(f"Traceability[{i}] references unknown evidence_id '{eid}'.")
                else:
                    errors.append(f"Traceability[{i}] must be a dict.")

        # 8. Optional Candidate Comparisons & Arbitration Fields Check
        candidate_comparisons = data.get("candidate_comparisons")
        if candidate_comparisons is not None:
            if not isinstance(candidate_comparisons, list):
                errors.append("Key 'candidate_comparisons' must be a list if provided.")
            else:
                for i, comp in enumerate(candidate_comparisons):
                    if not isinstance(comp, dict):
                        errors.append(f"candidate_comparisons[{i}] must be a dictionary.")
                        continue
                    c_driver = comp.get("driver")
                    if c_driver is not None and c_driver not in Phase3BInputAdapter.APPROVED_DRIVERS:
                        errors.append(f"candidate_comparisons[{i}] has invalid driver '{c_driver}'.")

        why_selected = data.get("why_selected")
        if why_selected is not None and not isinstance(why_selected, str):
            errors.append("Key 'why_selected' must be a string if provided.")

        why_alt = data.get("why_alternatives_rejected")
        if why_alt is not None and not isinstance(why_alt, list):
            errors.append("Key 'why_alternatives_rejected' must be a list if provided.")

        is_valid = (len(errors) == 0)
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=data if is_valid else None
        )


    @classmethod
    def get_safe_fallback(cls, context: EvidenceContext, reason: str = "Validation failed") -> Dict[str, Any]:
        """
        Constructs a deterministic, safe fallback payload that preserves Phase 3A diagnosis
        without inventing or hallucinating evidence.
        """
        established = context.diagnosis.established_driver
        status = context.diagnosis.overall_status
        confidence = context.diagnosis.confidence
        kpi = context.event.kpi

        traceability = []
        for e in context.all_evidence[:2]:
            traceability.append({
                "evidence_id": e.evidence_id,
                "source_dataset": e.source_dataset,
                "record_id": e.record_id
            })

        return {
            "executive_summary": f"Fallback diagnosis for {kpi}: {status} ({reason}).",
            "what_happened": f"{kpi} shifted by {context.event.change_percent * 100:.2f}% relative to baseline.",
            "diagnosis": {
                "driver": established,
                "status": status,
                "confidence": confidence
            },
            "claims": [
                {
                    "claim": f"Deterministic Phase 3A fallback preserved ({reason}).",
                    "claim_type": "OBSERVATION",
                    "evidence_ids": [e["evidence_id"] for e in traceability]
                }
            ],
            "supporting_evidence": [],
            "contradictory_evidence": [],
            "uncertainties": [
                "Automated LLM reasoning was unavailable or failed validation; fallback to deterministic baseline."
            ],
            "recommended_next_steps": [
                "Review deterministic telemetry and re-run analysis."
            ],
            "traceability": traceability,
            "validation_status": "FALLBACK_PRESERVED"
        }
