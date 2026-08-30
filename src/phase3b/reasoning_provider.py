"""
Abstract Reasoning Provider Interface for Phase 3B.
Decouples evidence context construction and validation from any specific LLM provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from .evidence_context import EvidenceContext

class ReasoningProvider(ABC):
    """
    Abstract interface for reasoning providers.
    All providers ingest EvidenceContext and return a raw or structured diagnosis response.
    """

    @abstractmethod
    def generate_diagnosis(self, context: EvidenceContext) -> Union[Dict[str, Any], str]:
        """
        Generates a diagnostic reasoning response given the evidence context.
        """
        pass
