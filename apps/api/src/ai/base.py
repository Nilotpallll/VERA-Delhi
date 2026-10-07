"""LLM Provider abstraction.

Architecture Rule 3: Models are accessed through provider interfaces.
Architecture Rule 7: LLMs cannot directly assign final risk scores.
Architecture Rule 15: Zero paid dependencies (free-tier / local only).
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMGenerationResult(BaseModel):
    provider: str
    model: str
    output_text: str
    raw_response: dict[str, Any] = {}
    tokens_used: int = 0


class LLMProvider(ABC):
    """Abstract interface for all LLM backends."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'ollama', 'groq')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier (e.g. 'gemini-1.5-flash', 'llama3.2')."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Verify whether provider is configured and reachable."""
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        """Generate text from a prompt.

        NOTE: Per Architecture Rule 7, results must be used strictly for
        summaries, feature extraction, entity parsing, or chain-of-thought traces,
        never for direct final risk scores.
        """
        pass


class EmbeddingProvider(ABC):
    """Abstract interface for dense semantic embeddings (e.g. BGE-M3)."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        pass
