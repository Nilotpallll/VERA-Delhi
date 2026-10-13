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


@router.get("/ready")
async def check_ready() -> dict:
    """Readiness probe checking DB, Redis, and AI availability. Returns HTTP 503 if unready."""
    import uuid
    from fastapi.responses import JSONResponse
    from ...queue.qstash import qstash_client

    db_health = await check_database_health()
    redis_healthy = await redis_client.ping()

    is_db_ready = db_health.get("status") == "connected"
    is_redis_ready = redis_healthy
    is_qstash_ready = qstash_client.is_configured or not settings.is_production
    has_llm = bool(settings.GEMINI_API_KEY or settings.GROQ_API_KEY or not settings.is_production)

    ready = is_db_ready and is_redis_ready and is_qstash_ready and has_llm

    db_stat = db_health.get("status", "unknown")
    db_display = "db paused/unreachable" if db_stat == "paused_or_unreachable" else db_stat

    checks = {
        "database": db_display,
        "redis": "connected" if redis_healthy else "unavailable",
        "qstash": "configured" if qstash_client.is_configured else ("mock" if not settings.is_production else "unavailable"),
        "ai": "available" if has_llm else "unavailable",
    }

    if not ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "message": "Core infrastructure components are not ready.",
                "request_id": str(uuid.uuid4()),
                "checks": checks,
            },
        )

    return {
        "status": "ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }
