"""Health check endpoint enforcing versioned contract."""

from datetime import UTC, datetime

from fastapi import APIRouter

from ...contracts.investigation import HealthCheckResponse
from ...core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def check_health() -> HealthCheckResponse:
    """Returns system status, component availability, and version metadata."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.VERSION,
        api_version="v1",
        timestamp=datetime.now(UTC),
        components={
            "database": "connected" if settings.DATABASE_URL else "unconfigured",
            "redis": "connected" if settings.UPSTASH_REDIS_REST_URL else "unconfigured",
            "storage": "ready" if settings.SUPABASE_URL else "unconfigured",
            "aiProviders": {
                "gemini": "available" if settings.GEMINI_API_KEY else "unavailable",
                "ollama": "available",
                "groq": "available" if settings.GROQ_API_KEY else "unavailable",
            },
        },
    )
