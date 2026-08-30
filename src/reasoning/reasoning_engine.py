"""
Main Reasoning Engine for Phase 3B.
Orchestrates the pipeline: Phase 3A Output -> ReasoningContext -> Prompt -> LLM -> Validation -> Formatted Output.
"""

from typing import Dict, Any, Optional
from .input_contract import InputContractValidator
from .reasoning_context import ReasoningContextBuilder, ReasoningContext
from .prompt_builder import PromptBuilder
from .llm_client import LLMProvider, MockLLMProvider
from .response_validator import ResponseValidator, ValidationResult
from .output_formatter import OutputFormatter

class ReasoningEngine:
    """
    Phase 3B Evidence-Grounded Reasoning Engine.
    Operates strictly on frozen Phase 3A structured outputs and provides validated causal reasoning.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider if llm_provider is not None else MockLLMProvider()

    def analyze(self, phase3a_payload: Dict[str, Any], user_query: str = "Explain the business anomaly.") -> Dict[str, Any]:
        """
        Executes end-to-end evidence synthesis and validated reasoning.
        """
        # 1. Validate Phase 3A Input Payload Contract (Strict isolation against ground truth)
        InputContractValidator.validate(phase3a_payload)

        # 2. Build Structured Reasoning Context
        context: ReasoningContext = ReasoningContextBuilder.build(phase3a_payload, user_query=user_query)

        # 3. Build Grounded Prompt
        prompt = PromptBuilder.build_prompt(context)

        # 4. Invoke LLM Provider
        raw_response = self.llm_provider.generate(prompt)

        # 5. Validate Response against Schema & Evidence Constraints
        validation_result: ValidationResult = ResponseValidator.validate(raw_response, context)

        # 6. Return Validated Result or Structured Failure
        if not validation_result.is_valid:
            return {
                "validation_status": "FAILED",
                "errors": validation_result.errors,
                "raw_response": raw_response
            }

        return OutputFormatter.format_json(
            validated_data=validation_result.validated_data, # type: ignore
            validation_warnings=validation_result.warnings
        )
