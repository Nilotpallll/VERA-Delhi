"""FastAPI Router for Veronica Floating Assistant."""

import os

from fastapi import APIRouter, HTTPException, status

from .budget import veronica_budget
from .schemas import (
    VeronicaChatRequest,
    VeronicaChatResponse,
    VeronicaHealthResponse,
)
from .service import VeronicaService

veronica_router = APIRouter(tags=["Veronica Assistant"])

VERONICA_ENABLED = os.getenv("VERONICA_ENABLED", "true").lower() == "true"


@veronica_router.post(
    "/chat",
    response_model=VeronicaChatResponse,
    summary="Process a chat turn with Veronica assistant",
)
async def veronica_chat_endpoint(request: VeronicaChatRequest) -> VeronicaChatResponse:
    """Processes user conversation with rate limiting, safety filters, and caching."""
    if not VERONICA_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Veronica assistant is temporarily disabled by configuration.",
        )
    return await VeronicaService.process_chat(request)


@veronica_router.get(
    "/health",
    response_model=VeronicaHealthResponse,
    summary="Health and rate-limit probe for Veronica assistant",
)
async def veronica_health_endpoint() -> VeronicaHealthResponse:
    """Returns Veronica status, active cache count, and available RPM quota."""
    return VeronicaHealthResponse(
        status="operational" if VERONICA_ENABLED else "disabled",
        enabled=VERONICA_ENABLED,
        provider="gemini-free-tier",
        budget_remaining=veronica_budget.get_remaining_global_rpm(),
        active_cache_size=veronica_budget.cache_size(),
    )


@veronica_router.get(
    "/faqs",
    summary="Get initial FAQ chips and welcome metadata for frontend",
)
async def veronica_faqs_endpoint(lang: str = "en") -> dict:
    """Returns starter question chips and welcome prompts for quick user onboarding."""
    if lang == "hi":
        return {
            "welcome": "नमस्ते! मैं वेरोनिका हूँ, VERA की एआई प्लेटफॉर्म गाइड। मैं डिजिटल निवेश घोटालों की पहचान और बचाव में आपकी सहायता कर सकती हूँ।",
            "chips": [
                "संदिग्ध व्हाट्सएप ग्रुप की जांच कैसे करें?",
                "क्या VERA सेबी (SEBI) रजिस्ट्रेशन चेक करता है?",
                "मैंने पैसे भेज दिए हैं, मुझे क्या करना चाहिए? 🚨",
                "VERA का रिस्क स्कोर कैसे काम करता है?",
            ],
        }
    return {
        "welcome": "Hello! I am Veronica, VERA's official AI platform guide. I can help you spot investment scams, check regulatory registrations, or navigate the scanner.",
        "chips": [
            "How do I check a suspicious WhatsApp group?",
            "How does VERA verify SEBI registration?",
            "I already sent money. What should I do? 🚨",
            "How does VERA calculate its risk score?",
        ],
    }
