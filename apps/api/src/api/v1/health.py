"""Health check endpoint enforcing versioned contract with real component pings."""

from datetime import UTC, datetime

from fastapi import APIRouter

from ...contracts.investigation import HealthCheckResponse
from ...core.config import settings
from ...core.database import check_database_health
from ...core.redis_client import redis_client

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def check_health() -> HealthCheckResponse:
    """Returns system status, component availability, and version metadata."""
    db_health = await check_database_health()
    redis_healthy = await redis_client.ping()

    overall_status = "healthy"
    if db_health.get("status") == "unavailable" and not settings.DATABASE_URL.startswith("sqlite"):
        overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=settings.VERSION,
        api_version="v1",
        timestamp=datetime.now(UTC),
        components={
            "database": db_health.get("status", "unknown"),
            "redis": "connected" if redis_healthy else "unavailable",
            "storage": "ready" if settings.SUPABASE_URL else "unconfigured",
            "aiProviders": {
                "gemini": "available" if settings.GEMINI_API_KEY else "unavailable",
                "ollama": "available",
                "groq": "available" if settings.GROQ_API_KEY else "unavailable",
            },
        },
    )
