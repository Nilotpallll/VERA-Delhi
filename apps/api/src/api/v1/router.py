"""API v1 Router aggregation."""

from fastapi import APIRouter

from .deepfake import router as deepfake_router
from .health import router as health_router
from .image_check import router as image_check_router
from .investigations import router as investigations_router
from .privacy import router as privacy_router
from .uploads import router as uploads_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(investigations_router)
api_v1_router.include_router(uploads_router)
api_v1_router.include_router(privacy_router)
api_v1_router.include_router(deepfake_router)
api_v1_router.include_router(image_check_router)

