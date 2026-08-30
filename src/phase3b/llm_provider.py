"""
Live LLM Reasoning Provider and Configuration Module for Phase 3B.2.
Integrates with external or mock LLM providers using standard secure configuration,
zero-temperature structured JSON prompting, and automatic safe fallback handling.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Union, Callable
from dataclasses import dataclass

from .reasoning_provider import ReasoningProvider
from .mock_reasoning_provider import MockReasoningProvider
from .evidence_context import EvidenceContext
from .prompts import build_system_prompt, build_user_prompt, build_reasoning_prompt_payload
from .validator import Phase3BResponseValidator

logger = logging.getLogger(__name__)

class ProviderError(RuntimeError):
    """Raised when an unrecoverable provider execution or configuration error occurs."""
    pass

@dataclass
class LLMConfig:
    """Configuration container for LLM Provider settings."""
    provider: str = "mock"
    model: str = "mock-reasoner-v1"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.0
    timeout_seconds: float = 30.0
    enable_safe_fallback: bool = True

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Loads configuration securely from environment variables."""
        provider = os.getenv("LLM_PROVIDER", "mock").lower()
        model = os.getenv("LLM_MODEL", "gemini-1.5-flash" if provider == "gemini" else "gpt-4o-mini" if provider == "openai" else "mock-reasoner-v1")
        
        # Check standard key or provider-specific keys
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            if provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
        
        base_url = os.getenv("LLM_BASE_URL")
        try:
            temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
        except ValueError:
            temperature = 0.0
            
        try:
            timeout_seconds = float(os.getenv("LLM_TIMEOUT", "30.0"))
        except ValueError:
            timeout_seconds = 30.0

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            enable_safe_fallback=True
        )

def _extract_json(text: str) -> Dict[str, Any]:
    """Extracts and parses JSON from raw LLM output text, handling markdown fences."""
    clean_text = text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    elif clean_text.startswith("```"):
        clean_text = clean_text[3:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
    clean_text = clean_text.strip()
    return json.loads(clean_text)

class LLMReasoningProvider(ReasoningProvider):
    """
    Production-ready LLM Reasoning Provider supporting Gemini, OpenAI, Generic HTTP,
    and Mock endpoints with strict JSON extraction and deterministic fallbacks.
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        custom_http_client: Optional[Callable[[str, Dict[str, str], bytes, float], bytes]] = None
    ):
        self.config = config or LLMConfig.from_env()
        self.custom_http_client = custom_http_client
        self.mock_fallback = MockReasoningProvider()

    def generate_diagnosis(self, context: EvidenceContext) -> Dict[str, Any]:
        """
        Executes reasoning over EvidenceContext. Returns structured JSON dictionary.
        """
        # If configured for mock or no API key is provided for a live service, use mock provider
        if self.config.provider in {"mock", "offline"}:
            return self.mock_fallback.generate_diagnosis(context)

        if not self.config.api_key and not self.custom_http_client:
            logger.warning("No LLM_API_KEY configured for provider '%s'. Triggering safe fallback.", self.config.provider)
            if self.config.enable_safe_fallback:
                return Phase3BResponseValidator.get_safe_fallback(context, reason=f"API key missing for {self.config.provider}")
            raise ProviderError(f"API key missing for provider '{self.config.provider}'.")

        payload = build_reasoning_prompt_payload(context)
        system_prompt = payload["system_prompt"]
        user_prompt = payload["user_prompt"]

        try:
            raw_response_text = self._call_llm_api(system_prompt, user_prompt)
            parsed_json = _extract_json(raw_response_text)
            return parsed_json
        except Exception as e:
            logger.error("LLM Provider call failed (%s): %s", self.config.provider, str(e))
            if self.config.enable_safe_fallback:
                return Phase3BResponseValidator.get_safe_fallback(context, reason=f"LLM API Error: {type(e).__name__}")
            raise ProviderError(f"LLM Provider execution failed: {str(e)}") from e

    def _call_llm_api(self, system_prompt: str, user_prompt: str) -> str:
        """Dispatches request to configured LLM endpoint."""
        provider = self.config.provider

        if provider == "openai" or provider == "generic_http":
            return self._call_openai_compatible_api(system_prompt, user_prompt)
        elif provider == "gemini":
            return self._call_gemini_api(system_prompt, user_prompt)
        elif provider == "anthropic":
            return self._call_anthropic_api(system_prompt, user_prompt)
        else:
            raise ProviderError(f"Unsupported LLM provider '{provider}'.")

    def _call_openai_compatible_api(self, system_prompt: str, user_prompt: str) -> str:
        """Invokes an OpenAI-compatible /v1/chat/completions endpoint."""
        url = self.config.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key or ''}"
        }
        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"}
        }

        resp_bytes = self._execute_http_post(url, headers, json.dumps(body).encode("utf-8"))
        data = json.loads(resp_bytes.decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> str:
        """Invokes Google Gemini REST API endpoint."""
        model = self.config.model or "gemini-1.5-flash"
        base = self.config.base_url or "https://generativelanguage.googleapis.com/v1beta/models"
        url = f"{base}/{model}:generateContent?key={self.config.api_key or ''}"
        
        headers = {"Content-Type": "application/json"}
        body = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "temperature": self.config.temperature,
                "response_mime_type": "application/json"
            }
        }

        resp_bytes = self._execute_http_post(url, headers, json.dumps(body).encode("utf-8"))
        data = json.loads(resp_bytes.decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_anthropic_api(self, system_prompt: str, user_prompt: str) -> str:
        """Invokes Anthropic Messages REST API endpoint."""
        url = self.config.base_url or "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01"
        }
        body = {
            "model": self.config.model or "claude-3-5-sonnet-20240620",
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096,
            "temperature": self.config.temperature
        }

        resp_bytes = self._execute_http_post(url, headers, json.dumps(body).encode("utf-8"))
        data = json.loads(resp_bytes.decode("utf-8"))
        return data["content"][0]["text"]

    def _execute_http_post(self, url: str, headers: Dict[str, str], body_bytes: bytes) -> bytes:
        """Executes HTTP POST using custom client or standard urllib."""
        if self.custom_http_client:
            return self.custom_http_client(url, headers, body_bytes, self.config.timeout_seconds)

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
            return response.read()
