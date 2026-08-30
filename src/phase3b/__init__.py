"""
Phase 3B: Safe Evidence-Grounded Reasoning & Validation Package.
"""

from .input_adapter import (
    Phase3BInputAdapter,
    Phase3BInputContract,
    ScenarioRequest,
    AnomalyEvent,
    CandidateHypothesis,
    Phase3ADiagnosis,
    InputContractError
)
from .evidence_context import (
    EvidenceContextBuilder,
    EvidenceContext,
    EvidenceItem,
    ContextHypothesisSummary
)
from .reasoning_provider import ReasoningProvider
from .mock_reasoning_provider import MockReasoningProvider
from .llm_provider import (
    LLMReasoningProvider,
    LLMConfig,
    ProviderError
)
from .prompts import (
    build_system_prompt,
    build_user_prompt,
    build_reasoning_prompt_payload
)
from .validator import (
    Phase3BResponseValidator,
    ValidationResult
)
from .engine import (
    Phase3BReasoningEngine,
    run_phase3b_pipeline
)

__all__ = [
    "Phase3BInputAdapter",
    "Phase3BInputContract",
    "ScenarioRequest",
    "AnomalyEvent",
    "CandidateHypothesis",
    "Phase3ADiagnosis",
    "InputContractError",
    "EvidenceContextBuilder",
    "EvidenceContext",
    "EvidenceItem",
    "ContextHypothesisSummary",
    "ReasoningProvider",
    "MockReasoningProvider",
    "LLMReasoningProvider",
    "LLMConfig",
    "ProviderError",
    "build_system_prompt",
    "build_user_prompt",
    "build_reasoning_prompt_payload",
    "Phase3BResponseValidator",
    "ValidationResult",
    "Phase3BReasoningEngine",
    "run_phase3b_pipeline"
]


