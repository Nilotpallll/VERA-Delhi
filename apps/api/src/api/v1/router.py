"""API v1 Router aggregation."""

from fastapi import APIRouter

from .health import router as health_router
from .investigations import router as investigations_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(investigations_router)
