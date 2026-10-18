"""Chained LLM Provider with Circuit Breakers, Rate Smoothing, and Fallbacks.

Enforces provider chain:
  Gemini (15 RPM smoothed) -> Groq (Llama-3.3) -> Ollama (Local) -> Deterministic Rule Engine
Each generation is labeled with the provider tier used and reduced confidence if degraded.
"""

import asyncio
import logging
import time

from ..core.config import settings
from ..core.evidence_cache import (
    compute_evidence_hash,
    get_cached_evidence_analysis,
    store_cached_evidence_analysis,
)
from .base import LLMGenerationResult, LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider

logger = logging.getLogger("vera.ai.chain")


class CircuitBreaker:
    """In-memory circuit breaker per provider."""

    def __init__(self, failure_threshold: int = 3, recovery_time_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Circuit breaker OPEN (tripped after %d failures)", self.failure_count)

    def can_attempt(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time_sec:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN probe state")
                return True
            return False
        # HALF_OPEN
        return True


class DeterministicRuleEngineLLMProvider(LLMProvider):
    """Deterministic, rule-based fallback that generates structured JSON responses without any LLM."""

    @property
    def provider_name(self) -> str:
        return "deterministic_rule_engine"

    @property
    def model_name(self) -> str:
        return "vera-rules-v1"

    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        """Parses prompt with regex rules and produces structured output."""
        lower = prompt.lower()
        entities = []
        claims = []

        if "telegram" in lower or "whatsapp" in lower:
            entities.append({"type": "channel", "value": "Social Messaging Channel"})
        if "guarantee" in lower or "daily" in lower or "profit" in lower:
            claims.append({
                "claim_text": "Guaranteed returns advertised",
                "claim_type": "guaranteed_return",
                "confidence": 0.95,
            })
        if "sebi" in lower:
            claims.append({
                "claim_text": "Purported SEBI registration claim",
                "claim_type": "sebi_registered",
                "confidence": 0.85,
            })

        output_json = {
            "entities": entities,
            "claims": claims,
            "summary": "Rule-engine extracted key risk indicators and claims from evidence.",
            "is_rule_engine": True,
        }
        import json
        return LLMGenerationResult(
            provider="deterministic_rule_engine",
            model="vera-rules-v1",
            output_text=json.dumps(output_json),
            raw_response={"fallback": True},
            tokens_used=0,
            tier="deterministic_rule_engine",
            degraded=True,
            confidence_discount=0.25,
        )


class ChainedLLMProvider(LLMProvider):
    """Resilient orchestrator that chains Gemini -> Groq -> Ollama -> Deterministic Rule Engine."""

    def __init__(self):
        self._gemini = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        self._groq = GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
        self._ollama = OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
        self._rules = DeterministicRuleEngineLLMProvider()

        self._breakers = {
            "gemini": CircuitBreaker(failure_threshold=3, recovery_time_sec=60.0),
            "groq": CircuitBreaker(failure_threshold=3, recovery_time_sec=60.0),
            "ollama": CircuitBreaker(failure_threshold=2, recovery_time_sec=30.0),
        }
        self._last_gemini_call = 0.0
        self._gemini_min_interval = 4.0  # 15 RPM rate-smoothing (60s / 15 = 4.0s)

    @property
    def provider_name(self) -> str:
        return "chained_orchestrator"

    @property
    def model_name(self) -> str:
        return "gemini->groq->ollama->rules"

    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        # 1. Check evidence hash cache
        ev_hash = compute_evidence_hash("llm_prompt", prompt, {"sys": system_prompt or ""})
        cached = await get_cached_evidence_analysis(ev_hash)
        if cached:
            return LLMGenerationResult(
                provider=cached.get("provider", "cache"),
                model=cached.get("model", "cached"),
                output_text=cached.get("output_text", ""),
                tokens_used=0,
                tier="cache_hit",
                degraded=False,
                confidence_discount=0.0,
            )

        # 2. Tier 1: Gemini (with 15 RPM rate smoothing)
        if bool(settings.GEMINI_API_KEY) and self._breakers["gemini"].can_attempt():
            try:
                # Rate smoothing: ensure at least 4.0s elapsed
                elapsed = time.time() - self._last_gemini_call
                if elapsed < self._gemini_min_interval:
                    await asyncio.sleep(self._gemini_min_interval - elapsed)
                self._last_gemini_call = time.time()

                res = await self._gemini.generate(prompt, system_prompt)
                self._breakers["gemini"].record_success()
                res_obj = LLMGenerationResult(
                    provider=res.provider,
                    model=res.model,
                    output_text=res.output_text,
                    raw_response=res.raw_response,
                    tokens_used=res.tokens_used,
                    tier="gemini_primary",
                    degraded=False,
                    confidence_discount=0.0,
                )
                await store_cached_evidence_analysis(ev_hash, res_obj.model_dump())
                return res_obj
            except Exception as exc:
                logger.warning("Gemini tier failed: %s. Tripping circuit breaker.", exc)
                self._breakers["gemini"].record_failure()

        # 3. Tier 2: Groq Fallback
        if bool(settings.GROQ_API_KEY) and self._breakers["groq"].can_attempt():
            try:
                res = await self._groq.generate(prompt, system_prompt)
                self._breakers["groq"].record_success()
                res_obj = LLMGenerationResult(
                    provider=res.provider,
                    model=res.model,
                    output_text=res.output_text,
                    raw_response=res.raw_response,
                    tokens_used=res.tokens_used,
                    tier="groq_fallback",
                    degraded=True,
                    confidence_discount=0.05,
                )
                await store_cached_evidence_analysis(ev_hash, res_obj.model_dump())
                return res_obj
            except Exception as exc:
                logger.warning("Groq tier failed: %s.", exc)
                self._breakers["groq"].record_failure()

        # 4. Tier 3: Ollama Local Fallback
        if self._breakers["ollama"].can_attempt():
            try:
                res = await self._ollama.generate(prompt, system_prompt)
                self._breakers["ollama"].record_success()
                res_obj = LLMGenerationResult(
                    provider=res.provider,
                    model=res.model,
                    output_text=res.output_text,
                    raw_response=res.raw_response,
                    tokens_used=res.tokens_used,
                    tier="ollama_local",
                    degraded=True,
                    confidence_discount=0.10,
                )
                await store_cached_evidence_analysis(ev_hash, res_obj.model_dump())
                return res_obj
            except Exception as exc:
                logger.warning("Ollama tier failed: %s.", exc)
                self._breakers["ollama"].record_failure()

        # 5. Tier 4: Deterministic Rule Engine
        logger.info("All neural LLM providers unavailable; degrading to deterministic rule engine.")
        rule_res = await self._rules.generate(prompt, system_prompt)
        await store_cached_evidence_analysis(ev_hash, rule_res.model_dump())
        return rule_res
