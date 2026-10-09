"""FastAPI dependencies injection for database, auth, and rate limiting."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.auth import AuthPrincipal, get_authenticated_principal, get_optional_principal
from ..core.database import get_db_session as _get_db_session
from ..core.rate_limit import RateLimiter, get_rate_limiter


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides async SQLAlchemy session with automatic commit/rollback."""
    async for session in _get_db_session():
        yield session


def get_current_user(principal: AuthPrincipal = Depends(get_authenticated_principal)) -> AuthPrincipal:
    """Requires authenticated API key or bearer token."""
    return principal


def get_optional_user(principal: AuthPrincipal | None = Depends(get_optional_principal)) -> AuthPrincipal | None:
    """Allows anonymous or authenticated caller."""
    return principal


def rate_limit(requests_per_minute: int = 60) -> RateLimiter:
    """Configures route rate limiter dependency."""
    return get_rate_limiter(requests_per_minute=requests_per_minute)
