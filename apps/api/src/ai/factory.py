"""Factory for resolving AI and LLM providers based on environment."""

from .base import LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider


async def get_active_llm_provider() -> LLMProvider:
    """Resolve the first available configured LLM provider according to precedence:

    1. Gemini Free Tier (cloud API)
    2. Local Ollama (offline / private)
    3. Groq Free Tier (optional fallback)
    """
    gemini = GeminiProvider()
    if await gemini.is_available():
        return gemini

    ollama = OllamaProvider()
    if await ollama.is_available():
        return ollama

    groq = GroqProvider()
    if await groq.is_available():
        return groq

    # Return Ollama by default for local development contract consistency
    return ollama
