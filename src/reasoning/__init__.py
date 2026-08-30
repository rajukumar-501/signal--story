"""
Accenture Decision Intelligence - Phase 3B Reasoning Layer.
"""

from .input_contract import InputContractValidator, InputContractError
from .reasoning_context import (
    EvidenceItem,
    CandidateHypothesis,
    EventInfo,
    Phase3ADiagnosis,
    ReasoningContext,
    ReasoningContextBuilder
)
from .prompt_builder import PromptBuilder
from .llm_client import LLMProvider, MockLLMProvider
from .response_validator import ResponseValidator, ValidationResult
from .output_formatter import OutputFormatter
from .reasoning_engine import ReasoningEngine

__all__ = [
    "InputContractValidator",
    "InputContractError",
    "EvidenceItem",
    "CandidateHypothesis",
    "EventInfo",
    "Phase3ADiagnosis",
    "ReasoningContext",
    "ReasoningContextBuilder",
    "PromptBuilder",
    "LLMProvider",
    "MockLLMProvider",
    "ResponseValidator",
    "ValidationResult",
    "OutputFormatter",
    "ReasoningEngine"
]
