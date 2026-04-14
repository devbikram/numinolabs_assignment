import asyncio
import logging
import random
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from api.v1.router import v1_router
from config.database import SessionLocal
from config.settings import settings
from core.limiter import limiter
from core.logging import configure_logging, request_id_var
from crud.borrow import mark_overdue_borrowings

configure_logging(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

SHOW_DOCS_ENVIRONMENT = ("development", "staging")

# Arbitrary 64-bit key for pg_try_advisory_lock; only one worker acquires this at a time.
_OVERDUE_LOCK_ID = 7_234_501


async def _overdue_scanner_loop() -> None:
    """Async task: mark overdue borrowings periodically.

    Uses PostgreSQL advisory locks so only one worker across all replicas
    performs the scan.  Falls back to unconditional execution on non-PostgreSQL
    databases (e.g. SQLite in tests).
    """
    interval = settings.OVERDUE_SCAN_INTERVAL_SECONDS
    while True:
        jitter = random.uniform(0, 60)
        await asyncio.sleep(interval + jitter)
        db = SessionLocal()
        try:
            # Attempt a session-level advisory lock (non-blocking).
            # Returns True if this worker grabbed the lock, False otherwise.
            try:
                acquired = db.execute(
                    text(f"SELECT pg_try_advisory_lock({_OVERDUE_LOCK_ID})")
                ).scalar()
            except Exception:
                # Non-PostgreSQL engine (e.g. SQLite in tests) — run unconditionally.
                acquired = True

            if not acquired:
                logger.debug("Overdue scan skipped — another worker holds the lock")
                continue

            try:
                count = mark_overdue_borrowings(db)
                if count:
                    logger.info("Overdue scanner: marked %d borrowing(s) overdue", count)
            finally:
                # Release the advisory lock so other workers can acquire it next cycle.
                try:
                    db.execute(
                        text(f"SELECT pg_advisory_unlock({_OVERDUE_LOCK_ID})")
                    )
                except Exception:
                    pass
        except Exception:
            logger.exception("Overdue scanner error")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_overdue_scanner_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app_configs: dict = {
        "title": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "description": "A RESTful API for managing a library's books, authors, and borrow records.",
        "lifespan": lifespan,
    }

    if settings.ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
        app_configs["openapi_url"] = None

    application = FastAPI(**app_configs)

    @application.middleware("http")
    async def correlation_id_middleware(request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or ""
        # Sanitize: cap length and strip CRLF / non-ASCII to prevent log-injection and header-splitting
        rid = "".join(c for c in rid if c.isprintable() and ord(c) < 128 and c not in "\r\n")[:64]
        if not rid:
            rid = str(uuid.uuid4())
        token = request_id_var.set(rid)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response

    application.state.limiter = limiter
    application.add_exception_handler(
        RateLimitExceeded,
        lambda request, exc: JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please slow down."},
        ),
    )
    application.add_middleware(SlowAPIMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
    )

    application.include_router(v1_router)

    return application


app = create_app()
