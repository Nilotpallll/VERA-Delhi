"""Security Headers Middleware — Block E.

Adds CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
Permissions-Policy to every response.

CORS is handled separately by FastAPI CORSMiddleware.
"""

from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import settings


# Content-Security-Policy: strict for API (no HTML served from API)
_API_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none';"
)

# CSP for Next.js frontend (referenced in docs only — enforced at CDN/Next level)
FRONTEND_CSP_REFERENCE = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}'; "
    "style-src 'self' 'unsafe-inline'; "  # required by tailwind in dev; tighten in prod
    "img-src 'self' data: blob:; "
    "connect-src 'self' https://*.supabase.co wss://*.supabase.co https://api.gemini.google.com https://api.groq.com; "
    "font-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self';"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers into every API response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Prevent content sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Block framing (clickjacking)
        response.headers["X-Frame-Options"] = "DENY"

        # Minimal CSP for pure-API responses
        response.headers["Content-Security-Policy"] = _API_CSP

        # Referrer policy — don't leak URL in cross-origin requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — disable all browser features we don't use
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), payment=(), usb=(), "
            "interest-cohort=()"
        )

        # HSTS — only set on HTTPS (production)
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Remove server version leak
        for header_to_remove in ("server", "x-powered-by"):
            try:
                del response.headers[header_to_remove]
            except (KeyError, AttributeError):
                pass

        return response
