"""Ollama Local LLM Provider implementation.

Architecture Rule 3: Models accessed through provider interfaces.
Architecture Rule 15: Local / self-hosted open-weights models.
"""

import httpx

from ..core.config import settings
from .base import LLMGenerationResult, LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            return LLMGenerationResult(
                provider=self.provider_name,
                model=self.model_name,
                output_text=data.get("response", ""),
                raw_response=data,
            )
