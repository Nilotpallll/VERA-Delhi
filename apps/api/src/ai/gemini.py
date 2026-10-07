"""Gemini Free-Tier LLM Provider implementation.

Architecture Rule 3: Models accessed through provider interfaces.
Architecture Rule 15: Free-tier only.
"""

import httpx

from ..core.config import settings
from .base import LLMGenerationResult, LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self.model

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        if not await self.is_available():
            raise RuntimeError("Gemini provider is not configured. GEMINI_API_KEY is missing.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt}]
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            try:
                candidate = data["candidates"][0]
                text = candidate["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                text = ""

            return LLMGenerationResult(
                provider=self.provider_name,
                model=self.model_name,
                output_text=text,
                raw_response=data,
            )
