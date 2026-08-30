"""
Internal Reasoning Context & Data Structures.
Defines typed, immutable internal objects representing the structured analytical context
approved for consumption by the LLM reasoning layer.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .input_contract import InputContractValidator

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_dataset: str
    record_id: Optional[str]
    lineage: str
    date: str
    market: Optional[str]
    product_code: Optional[str]
    category: Optional[str]
    channel: Optional[str]
    metric: str
    value: Any
    evidence_role: str
    temporal_alignment: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_dataset": self.source_dataset,
            "record_id": self.record_id,
            "lineage": self.lineage,
            "date": self.date,
            "market": self.market,
            "product_code": self.product_code,
            "category": self.category,
            "channel": self.channel,
            "metric": self.metric,
            "value": self.value,
            "evidence_role": self.evidence_role,
            "temporal_alignment": self.temporal_alignment
        }

@dataclass(frozen=True)
class CandidateHypothesis:
    driver: str
    rank: int
    score: float
    status: str
    confidence: str
    evidence_ids: List[str]
    contradictions: List[str]
    evidence_source_count: int
    supporting_evidence_count: int
    contradictory_evidence_count: int
    temporal_alignment: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "driver": self.driver,
            "rank": self.rank,
            "score": self.score,
            "status": self.status,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "contradictions": list(self.contradictions),
            "evidence_source_count": self.evidence_source_count,
            "supporting_evidence_count": self.supporting_evidence_count,
            "contradictory_evidence_count": self.contradictory_evidence_count,
            "temporal_alignment": self.temporal_alignment
        }

@dataclass(frozen=True)
class EventInfo:
    kpi: str
    current_value: Optional[float]
    previous_month_value: Optional[float]
    baseline_value: Optional[float]
    mom_change_percent: Optional[float]
    baseline_change_percent: Optional[float]
    change_percent: Optional[float]
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

@dataclass(frozen=True)
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

@dataclass(frozen=True)
class ReasoningContext:
    user_query: str
    event: EventInfo
    candidate_hypotheses: List[CandidateHypothesis]
    all_evidence: Dict[str, EvidenceItem]
    deterministic_diagnosis: Phase3ADiagnosis
    limitations: List[str] = field(default_factory=list)

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        return self.all_evidence.get(evidence_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_query": self.user_query,
            "event": self.event.to_dict(),
            "candidate_hypotheses": [h.to_dict() for h in self.candidate_hypotheses],
            "all_evidence": {eid: e.to_dict() for eid, e in self.all_evidence.items()},
            "deterministic_diagnosis": self.deterministic_diagnosis.to_dict(),
            "limitations": list(self.limitations)
        }

class ReasoningContextBuilder:
    """
    Constructs a validated ReasoningContext from a Phase 3A deterministic output payload.
    Assigns globally unique, traceable evidence identifiers (e.g., 'EVD-001').
    """

    @classmethod
    def build(cls, phase3a_payload: Dict[str, Any], user_query: str = "Explain the business anomaly.") -> ReasoningContext:
        # Validate against ground truth leakage and structure
        InputContractValidator.validate(phase3a_payload)

        # 1. Parse Event
        raw_event = phase3a_payload.get("event", {})
        event_info = EventInfo(
            kpi=str(raw_event.get("kpi", "unknown")),
            current_value=raw_event.get("current_value"),
            previous_month_value=raw_event.get("previous_month_value"),
            baseline_value=raw_event.get("baseline_value"),
            mom_change_percent=raw_event.get("mom_change_percent"),
            baseline_change_percent=raw_event.get("baseline_change_percent"),
            change_percent=raw_event.get("change_percent"),
            baseline_status=str(raw_event.get("baseline_status", "UNKNOWN"))
        )

        # 2. Parse and Index Evidence Across Hypotheses
        all_evidence: Dict[str, EvidenceItem] = {}
        evidence_signature_map: Dict[str, str] = {}
        counter = 1

        def get_evidence_sig(ev: Dict[str, Any]) -> str:
            return (
                f"{ev.get('source_dataset')}|{ev.get('record_id')}|{ev.get('metric')}|"
                f"{ev.get('date')}|{ev.get('market')}|{ev.get('product_code')}|"
                f"{ev.get('value')}|{ev.get('evidence_role')}"
            )

        # 3. Parse Hypotheses
        raw_hypotheses = phase3a_payload.get("candidate_hypotheses", [])
        parsed_hypotheses: List[CandidateHypothesis] = []

        for hyp in raw_hypotheses:
            hyp_evidence_ids: List[str] = []
            hyp_temporal = str(hyp.get("temporal_alignment", "NO_CLEAR_ALIGNMENT"))

            for ev in hyp.get("evidence", []):
                sig = get_evidence_sig(ev)
                if sig not in evidence_signature_map:
                    eid = f"EVD-{counter:03d}"
                    evidence_signature_map[sig] = eid
                    item = EvidenceItem(
                        evidence_id=eid,
                        source_dataset=str(ev.get("source_dataset", "unknown")),
                        record_id=ev.get("record_id"),
                        lineage=str(ev.get("lineage", "UNKNOWN")),
                        date=str(ev.get("date", "")),
                        market=ev.get("market"),
                        product_code=ev.get("product_code"),
                        category=ev.get("category"),
                        channel=ev.get("channel"),
                        metric=str(ev.get("metric", "unknown")),
                        value=ev.get("value"),
                        evidence_role=str(ev.get("evidence_role", "CONTEXT")),
                        temporal_alignment=hyp_temporal
                    )
                    all_evidence[eid] = item
                    counter += 1
                else:
                    eid = evidence_signature_map[sig]

                if eid not in hyp_evidence_ids:
                    hyp_evidence_ids.append(eid)

            parsed_hypotheses.append(
                CandidateHypothesis(
                    driver=str(hyp.get("driver", "UNKNOWN")),
                    rank=int(hyp.get("rank", 0)),
                    score=float(hyp.get("score", 0.0)),
                    status=str(hyp.get("status", "NOT_ESTABLISHED")),
                    confidence=str(hyp.get("confidence", "NONE")),
                    evidence_ids=hyp_evidence_ids,
                    contradictions=list(hyp.get("contradictions", [])),
                    evidence_source_count=int(hyp.get("evidence_source_count", 0)),
                    supporting_evidence_count=int(hyp.get("supporting_evidence_count", 0)),
                    contradictory_evidence_count=int(hyp.get("contradictory_evidence_count", 0)),
                    temporal_alignment=hyp_temporal
                )
            )

        # 4. Parse Diagnosis
        raw_diag = phase3a_payload.get("diagnosis", {})
        diagnosis_info = Phase3ADiagnosis(
            established_driver=raw_diag.get("established_driver"),
            overall_status=str(raw_diag.get("overall_status", "NOT_ESTABLISHED")),
            reason=str(raw_diag.get("reason", "")),
            confidence=str(raw_diag.get("confidence", "NONE"))
        )

        limitations = list(phase3a_payload.get("limitations", []))

        return ReasoningContext(
            user_query=user_query,
            event=event_info,
            candidate_hypotheses=parsed_hypotheses,
            all_evidence=all_evidence,
            deterministic_diagnosis=diagnosis_info,
            limitations=limitations
        )
