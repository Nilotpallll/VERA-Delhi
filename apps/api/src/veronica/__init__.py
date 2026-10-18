"""Veronica Floating Assistant - Backend Module.

Fully isolated, additive assistant service for VERA.
Provides intelligent platform guidance, FAQ resolution, and emergency fraud triage
while strictly protecting Gemini free-tier rate limits and adhering to safety policies.
"""

from .router import veronica_router

__all__ = ["veronica_router"]
