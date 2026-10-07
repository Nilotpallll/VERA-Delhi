"""Observability setup for Sentry and structured logging.

Architecture Rule 15: No paid dependencies. Sentry free tier supported.
"""

import logging

from .config import settings

logger = logging.getLogger("vera")


def init_observability() -> None:
    """Initialize logging and Sentry if configured."""
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            )
            logger.info("Sentry telemetry initialized successfully")
        except ImportError:
            logger.warning("sentry-sdk not installed; skipping telemetry hook")
        except Exception as e:
            logger.error("Failed to initialize Sentry: %s", e)
    else:
        logger.info("Sentry DSN unconfigured; proceeding in local logging mode")
