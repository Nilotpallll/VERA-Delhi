"""VERA Investment-Fraud Investigation Platform - FastAPI Entrypoint.

Architecture Rule 1: Frontend communicates only through API contracts.
Architecture Rule 2: API contracts are versioned.
Architecture Rule 14: Do not introduce unnecessary microservices.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_v1_router
from .contracts.investigation import HealthCheckResponse
from .core.config import settings
from .core.observability import init_observability, logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    init_observability()
    logger.info("Starting %s v%s in %s mode", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MNC-grade agentic platform for multi-modal investment fraud analysis and deterministic risk scoring.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Versioned API (Architecture Rule 2)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# Root health alias for load balancers and orchestrators
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def root_health():
    from .api.v1.health import check_health
    return await check_health()


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api": settings.API_V1_STR,
        "status": "operational",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.src.main:app", host="0.0.0.0", port=8000, reload=True)
