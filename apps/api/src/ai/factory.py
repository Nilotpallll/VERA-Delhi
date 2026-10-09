"""Factory for resolving AI and LLM providers based on configuration.

Provider is selected ONLY through configuration (settings.LLM_PROVIDER).
Never hard-code a provider in business logic.
"""

from ..core.config import settings
from .base import LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Instantiate provider by configured name.
    
    Supported: 'gemini', 'ollama', 'groq'.
    """
    selected = (provider_name or settings.LLM_PROVIDER or "gemini").lower().strip()
    if selected == "gemini":
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    elif selected == "ollama":
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
    elif selected == "groq":
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    else:
        raise ValueError(
            f"Unsupported LLM provider '{selected}'. Supported: 'gemini', 'ollama', 'groq'."
        )


async def get_active_llm_provider() -> LLMProvider:
    """Resolve the configured LLM provider and check availability."""
    provider = get_llm_provider()
    return provider
