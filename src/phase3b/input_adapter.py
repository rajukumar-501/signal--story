"""
Phase 3B Input Adapter and Versioned Contract.
Establishes the clean, isolated boundary between Phase 3A deterministic output
and Phase 3B evidence-grounded reasoning.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

class InputContractError(ValueError):
    """Raised when Phase 3A input payload violates schema or isolation boundaries."""
    pass

@dataclass
class ScenarioRequest:
    scenario_id: Optional[str] = None
    market: Optional[str] = None
    product_code: Optional[str] = None
    category: Optional[str] = None
    channel: Optional[str] = None
    kpi: str = "gross_sales"
    date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "market": self.market,
            "product_code": self.product_code,
            "category": self.category,
            "channel": self.channel,
            "kpi": self.kpi,
            "date": self.date
        }

@dataclass
class AnomalyEvent:
    kpi: str
    current_value: float
    previous_month_value: float
    baseline_value: float
    mom_change_percent: float
    baseline_change_percent: float
    change_percent: float
    baseline_status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi": self.kpi,
            "current_value": self.current_value,
            "previous_month_value": self.previous_month_value,
            "baseline_value": self.baseline_value,
            "mom_change_percent": self.mom_change_percent,
            "baseline_change_percent": self.baseline_change_percent,
            "change_percent": self.change_percent,
            "baseline_status": self.baseline_status
        }

@dataclass
class CandidateHypothesis:
    driver: str
    rank: int
    score: float
    status: str
    confidence: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    evidence_source_count: int = 0
    supporting_source_count: int = 0
    supporting_evidence_count: int = 0
    outcome_evidence_count: int = 0
    contradictory_evidence_count: int = 0
    temporal_alignment: str = "NO_CLEAR_ALIGNMENT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "driver": self.driver,
            "rank": self.rank,
            "score": self.score,
            "status": self.status,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "contradictions": self.contradictions,
            "evidence_source_count": self.evidence_source_count,
            "supporting_source_count": self.supporting_source_count,
            "supporting_evidence_count": self.supporting_evidence_count,
            "outcome_evidence_count": self.outcome_evidence_count,
            "contradictory_evidence_count": self.contradictory_evidence_count,
            "temporal_alignment": self.temporal_alignment
        }

@dataclass
class Phase3ADiagnosis:
    established_driver: Optional[str]
    overall_status: str
    reason: str
    confidence: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "established_driver": self.established_driver,
            "overall_status": self.overall_status,
            "reason": self.reason,
            "confidence": self.confidence
        }

@dataclass
class Phase3BInputContract:
    schema_version: str
    phase3a_baseline: str
    timestamp: str
    request: ScenarioRequest
    event: AnomalyEvent
    candidate_hypotheses: List[CandidateHypothesis]
    diagnosis: Phase3ADiagnosis
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase3a_baseline": self.phase3a_baseline,
            "timestamp": self.timestamp,
            "request": self.request.to_dict(),
            "event": self.event.to_dict(),
            "candidate_hypotheses": [h.to_dict() for h in self.candidate_hypotheses],
            "diagnosis": self.diagnosis.to_dict(),
            "limitations": list(self.limitations)
        }

class Phase3BInputAdapter:
    """
    Validates Phase 3A deterministic output payloads and normalizes them
    into the versioned Phase 3B Input Contract. Strictly rejects oracle fields.
    """

    SCHEMA_VERSION = "1.0.0"
    PHASE3A_BASELINE = "3A.3"
    
    FORBIDDEN_ORACLE_KEYS = {
        "true_root_cause",
        "root_cause_status",
        "expected_driver",
        "expected_established_driver",
        "oracle_driver",
        "target_cause",
        "scenario_truth"
    }

    APPROVED_DRIVERS = {
        "DRIVER_01_INVENTORY",
        "DRIVER_02_PRICING",
        "DRIVER_03_MARKETING",
        "DRIVER_04_RETURNS",
        "DRIVER_05_SUPPORT",
        "DRIVER_06_CUSTOMER",
        "DRIVER_07_MARKET",
        "DRIVER_08_PRODUCT_MIX"
    }

    @classmethod
    def validate_and_normalize(
        cls, 
        phase3a_payload: Dict[str, Any], 
        request: Optional[Dict[str, Any]] = None
    ) -> Phase3BInputContract:
        """
        Validates the raw Phase 3A payload and normalizes it into Phase3BInputContract.
        """
        if not isinstance(phase3a_payload, dict):
            raise InputContractError(f"Input payload must be a dict, got {type(phase3a_payload).__name__}")

        # 1. Strict Isolation Check - Reject forbidden oracle/ground-truth keys
        cls._check_for_oracle_keys(phase3a_payload)
        if request:
            cls._check_for_oracle_keys(request)

        # 2. Check Required Top-Level Keys
        required_keys = ["event", "diagnosis"]
        for k in required_keys:
            if k not in phase3a_payload:
                raise InputContractError(f"Missing required top-level key '{k}' in Phase 3A payload.")

        # candidate_hypotheses can be 'candidate_hypotheses' or legacy alias 'candidate_drivers'
        raw_hypotheses = phase3a_payload.get("candidate_hypotheses", phase3a_payload.get("candidate_drivers"))
        if raw_hypotheses is None:
            raise InputContractError("Missing 'candidate_hypotheses' list in Phase 3A payload.")

        # 3. Parse Event
        raw_event = phase3a_payload["event"]
        if not isinstance(raw_event, dict):
            raise InputContractError("Key 'event' must be a dictionary.")
        
        event_obj = AnomalyEvent(
            kpi=str(raw_event.get("kpi", "gross_sales")),
            current_value=float(raw_event.get("current_value", 0.0)),
            previous_month_value=float(raw_event.get("previous_month_value", 0.0)),
            baseline_value=float(raw_event.get("baseline_value", 0.0)),
            mom_change_percent=float(raw_event.get("mom_change_percent", raw_event.get("change_percent", 0.0))),
            baseline_change_percent=float(raw_event.get("baseline_change_percent", 0.0)),
            change_percent=float(raw_event.get("change_percent", 0.0)),
            baseline_status=str(raw_event.get("baseline_status", "VALID"))
        )

        # 4. Parse Request
        req_dict = request or phase3a_payload.get("scenario") or phase3a_payload.get("request") or {}
        req_obj = ScenarioRequest(
            scenario_id=req_dict.get("scenario_id"),
            market=req_dict.get("market"),
            product_code=req_dict.get("product_code"),
            category=req_dict.get("category"),
            channel=req_dict.get("channel"),
            kpi=str(req_dict.get("kpi", event_obj.kpi)),
            date=req_dict.get("date")
        )

        # 5. Parse Candidate Hypotheses
        hypotheses_objs: List[CandidateHypothesis] = []
        for idx, h in enumerate(raw_hypotheses):
            if not isinstance(h, dict):
                raise InputContractError(f"Candidate hypothesis at index {idx} must be a dict.")
            
            driver_name = h.get("driver")
            if driver_name and driver_name not in cls.APPROVED_DRIVERS:
                raise InputContractError(f"Unknown driver identifier '{driver_name}' in candidate list.")
            
            hypotheses_objs.append(CandidateHypothesis(
                driver=str(driver_name),
                rank=int(h.get("rank", idx + 1)),
                score=float(h.get("score", h.get("final_score", 0.0))),
                status=str(h.get("status", "NOT_ESTABLISHED")),
                confidence=str(h.get("confidence", "NONE")),
                evidence=list(h.get("evidence", [])),
                contradictions=list(h.get("contradictions", [])),
                evidence_source_count=int(h.get("evidence_source_count", 0)),
                supporting_source_count=int(h.get("supporting_source_count", h.get("evidence_source_count", 0))),
                supporting_evidence_count=int(h.get("supporting_evidence_count", 0)),
                outcome_evidence_count=int(h.get("outcome_evidence_count", 0)),
                contradictory_evidence_count=int(h.get("contradictory_evidence_count", 0)),
                temporal_alignment=str(h.get("temporal_alignment", "NO_CLEAR_ALIGNMENT"))
            ))

        # 6. Parse Diagnosis
        raw_diag = phase3a_payload["diagnosis"]
        if not isinstance(raw_diag, dict):
            raise InputContractError("Key 'diagnosis' must be a dictionary.")
        
        diag_driver = raw_diag.get("established_driver")
        if diag_driver and diag_driver not in cls.APPROVED_DRIVERS:
            raise InputContractError(f"Unknown established_driver '{diag_driver}' in diagnosis.")
        
        diag_obj = Phase3ADiagnosis(
            established_driver=diag_driver,
            overall_status=str(raw_diag.get("overall_status", "NOT_ESTABLISHED")),
            reason=str(raw_diag.get("reason", "")),
            confidence=str(raw_diag.get("confidence", "NONE"))
        )

        # 7. Build Versioned Contract
        return Phase3BInputContract(
            schema_version=cls.SCHEMA_VERSION,
            phase3a_baseline=cls.PHASE3A_BASELINE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request=req_obj,
            event=event_obj,
            candidate_hypotheses=hypotheses_objs,
            diagnosis=diag_obj,
            limitations=list(phase3a_payload.get("limitations", []))
        )

    @classmethod
    def from_phase3a_output(
        cls,
        phase3a_payload: Dict[str, Any],
        request: Optional[Dict[str, Any]] = None
    ) -> Phase3BInputContract:
        """Alias for validate_and_normalize."""
        return cls.validate_and_normalize(phase3a_payload, request=request)

    @classmethod
    def _check_for_oracle_keys(cls, data: Any, path: str = "") -> None:
        """Recursively checks and rejects any payload containing forbidden oracle keys."""
        if isinstance(data, dict):
            for k, v in data.items():
                if k in cls.FORBIDDEN_ORACLE_KEYS:
                    raise InputContractError(f"Isolation violation: Forbidden oracle key '{k}' found at path '{path}'.")
                cls._check_for_oracle_keys(v, f"{path}.{k}" if path else k)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                cls._check_for_oracle_keys(item, f"{path}[{i}]")
