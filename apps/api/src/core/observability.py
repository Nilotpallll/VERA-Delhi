"""Structured observability: JSON logging, Sentry, request correlation IDs.

Architecture Rule 15: No paid dependencies. Sentry free tier is sufficient.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class StructuredFormatter(logging.Formatter):
    """Emit each log record as a single JSON object for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach correlation IDs if injected by middleware
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Any extra fields attached to the record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process",
                "message", "request_id", "trace_id", "taskName",
            ):
                if not key.startswith("_"):
                    log_entry[key] = value

        return json.dumps(log_entry, default=str)


# ── Module-level logger ───────────────────────────────────────────────────────
logger = logging.getLogger("vera")


def init_observability() -> None:
    """Initialize structured logging and Sentry if configured."""
    from .config import settings

    # Configure root vera logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    # Also suppress noisy uvicorn access logs in production
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                ],
                # Strip PII from events in prod
                send_default_pii=False,
                before_send=_before_send_sentry,
            )
            logger.info("Sentry telemetry initialized", extra={"dsn_configured": True})
        except ImportError:
            logger.warning("sentry-sdk not installed; skipping telemetry hook")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to initialize Sentry: %s", exc)
    else:
        logger.info("Sentry DSN unconfigured; proceeding in local logging mode")


def _before_send_sentry(event: dict, hint: dict) -> dict | None:
    """Scrub sensitive fields before sending events to Sentry."""
    sensitive_keys = {"password", "token", "api_key", "secret", "authorization"}

    def _scrub(obj: object) -> object:
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if k.lower() in sensitive_keys else _scrub(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(item) for item in obj]
        return obj

    event = _scrub(event)
    return event
