"""Groq Optional Fast LLM Provider implementation.

Architecture Rule 3: Models accessed through provider interfaces.
Architecture Rule 15: Free-tier / Optional acceleration.
"""

import httpx

from ..core.config import settings
from .base import LLMGenerationResult, LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self.model

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMGenerationResult:
        if not await self.is_available():
            raise RuntimeError("Groq provider is unconfigured. GROQ_API_KEY is missing.")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            output_text = data["choices"][0]["message"]["content"]
            return LLMGenerationResult(
                provider=self.provider_name,
                model=self.model_name,
                output_text=output_text,
                raw_response=data,
            )
