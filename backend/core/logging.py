"""Structured logging configuration with per-request correlation ID support."""

import logging
import sys
import uuid
from contextvars import ContextVar

# Per-request correlation ID stored in a context variable so it is
# automatically propagated through async and sync code in the same request.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class CorrelationIDFilter(logging.Filter):
    """Inject the current request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def configure_logging(level: str = "INFO") -> None:
    """Set up root logger with a structured format."""
    fmt = "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationIDFilter())
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%SZ"))

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Remove any handlers added by uvicorn/FastAPI before we attach ours.
    root.handlers.clear()
    root.addHandler(handler)
