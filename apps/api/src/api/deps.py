"""FastAPI dependencies injection."""

from collections.abc import AsyncGenerator


async def get_db_session() -> AsyncGenerator[None, None]:
    """Placeholder dependency for SQLAlchemy async session in Phase 0."""
    yield None
