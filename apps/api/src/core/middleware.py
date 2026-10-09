"""Request middleware: request IDs, structured access logging, timing.

Injects X-Request-ID and X-Correlation-ID into every response.
"""

import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .observability import logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Injects unique request ID and correlation ID into every request/response cycle.

    - Reads ``X-Request-ID`` and ``X-Correlation-ID`` from incoming request if present.
    - Falls back to a freshly generated UUID4 hex string.
    - Stores the ID as ``request.state.request_id`` for downstream use.
    - Echoes both back in response headers.
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or request.headers.get(self.header_name) or uuid.uuid4().hex
        correlation_id = request.headers.get("x-correlation-id") or request_id

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["x-request-id"] = request_id
        response.headers["x-correlation-id"] = correlation_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Structured access log
        logger.info(
            "HTTP %s %s → %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": _get_client_ip(request),
                "user_agent": request.headers.get("User-Agent", ""),
            },
        )
        return response


RequestIDMiddleware = RequestContextMiddleware



def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting common reverse-proxy headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"
