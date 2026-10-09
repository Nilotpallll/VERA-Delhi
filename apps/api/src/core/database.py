"""SQLAlchemy async engine, session factory, and base model.

Architecture Rule 14: Single service; no unnecessary microservices.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings
from .observability import logger


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# ── Engine ────────────────────────────────────────────────────────────────────
_engine = None
_async_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,      # validates connections before handing out
            pool_recycle=3600,       # recycle connections after 1 hour
        )
    return _engine


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession | None, None]:
    """FastAPI dependency that yields a managed async DB session or None if DB is offline."""
    try:
        session_factory = _get_session_factory()
    except Exception as exc:
        logger.warning("DB session factory unavailable: %s", exc)
        yield None
        return

    try:
        async with session_factory() as session:
            try:
                yield session
                if session.is_active:
                    await session.commit()
            except Exception:
                if session.is_active:
                    await session.rollback()
                raise
            finally:
                await session.close()
    except Exception as exc:
        logger.warning("DB session failed or disconnected: %s", exc)
        yield None



async def check_database_health() -> dict[str, str]:
    """Ping the database and return a health status dict."""
    try:
        from sqlalchemy import text
        engine = _get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "connected", "driver": engine.dialect.name}
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return {"status": "unavailable", "error": str(exc)}


async def create_all_tables() -> None:
    """Create all tables (used in tests; production uses Alembic)."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """Drop all tables (used in tests only)."""
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def dispose_engine() -> None:
    """Gracefully close all pooled connections on shutdown."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database engine disposed")
