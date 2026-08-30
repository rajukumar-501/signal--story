"""
Phase 3B Reasoning Pipeline Orchestrator.
Coordinates Input Adapter -> Evidence Context Builder -> Reasoning Provider -> Response Validator
to produce fully validated, evidence-grounded decision intelligence reports.
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple

from .input_adapter import Phase3BInputAdapter, Phase3BInputContract
from .evidence_context import EvidenceContextBuilder, EvidenceContext
from .reasoning_provider import ReasoningProvider
from .mock_reasoning_provider import MockReasoningProvider
from .llm_provider import LLMReasoningProvider
from .validator import Phase3BResponseValidator, ValidationResult

logger = logging.getLogger(__name__)

class Phase3BReasoningEngine:
    """
    Main orchestration engine for Phase 3B.
    Executes the complete end-to-end reasoning pipeline with strict validation gating.
    """

    def __init__(self, default_provider: Optional[ReasoningProvider] = None):
        self.default_provider = default_provider or LLMReasoningProvider()

    def run(
        self,
        phase3a_payload: Dict[str, Any],
        provider: Optional[ReasoningProvider] = None
    ) -> Tuple[Dict[str, Any], ValidationResult]:
        """
        Executes the Phase 3B reasoning pipeline on a Phase 3A output payload.
        Returns:
            Tuple of (final_report_dict, validation_result)
        """
        active_provider = provider or self.default_provider
        start_time = time.time()

        # Step 1: Input Adaptation & Anti-Oracle Validation
        contract: Phase3BInputContract = Phase3BInputAdapter.from_phase3a_output(phase3a_payload)

        # Step 2: Evidence Context Construction & Indexing
        context: EvidenceContext = EvidenceContextBuilder.build_context(contract)

        # Step 3: Provider Diagnostic Reasoning Generation
        try:
            raw_response = active_provider.generate_diagnosis(context)
        except Exception as e:
            logger.warning("Provider generation failed with exception: %s. Using safe fallback.", str(e))
            fallback = Phase3BResponseValidator.get_safe_fallback(context, reason=f"Provider Exception: {type(e).__name__}")
            fallback["pipeline_latency_ms"] = round((time.time() - start_time) * 1000, 2)
            return fallback, ValidationResult(is_valid=False, errors=[str(e)])

        # Step 4: Deterministic 10-Step Safety Validation
        validation = Phase3BResponseValidator.validate(raw_response, context)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        if validation.is_valid and validation.validated_data:
            report = dict(validation.validated_data)
            if isinstance(raw_response, dict) and raw_response.get("validation_status") == "FALLBACK_PRESERVED":
                report["validation_status"] = "FALLBACK_PRESERVED"
            else:
                report["validation_status"] = "PASSED"
            report["pipeline_latency_ms"] = latency_ms
            return report, validation

        else:
            # Deterministic Safe Fallback on validation failure
            err_summary = "; ".join(validation.errors[:3])
            logger.info("Validation rejected model output (%s). Applying deterministic fallback.", err_summary)
            fallback = Phase3BResponseValidator.get_safe_fallback(context, reason=f"Validation failed: {err_summary}")
            fallback["pipeline_latency_ms"] = latency_ms
            fallback["validation_errors"] = validation.errors
            return fallback, validation

def run_phase3b_pipeline(
    phase3a_payload: Dict[str, Any],
    provider: Optional[ReasoningProvider] = None
) -> Dict[str, Any]:
    """
    Convenience function executing the complete Phase 3B reasoning pipeline.
    """
    engine = Phase3BReasoningEngine(default_provider=provider)
    report, _ = engine.run(phase3a_payload, provider=provider)
    return report
