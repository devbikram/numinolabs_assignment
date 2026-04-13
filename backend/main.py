import logging
import random
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.v1.router import v1_router
from config.database import SessionLocal
from config.settings import settings
from core.limiter import limiter
from core.logging import configure_logging, request_id_var
from crud.borrow import mark_overdue_borrowings

configure_logging(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

SHOW_DOCS_ENVIRONMENT = ("development", "staging")


def _overdue_scanner_loop() -> None:
    """Daemon thread: mark overdue borrowings periodically.

    Sleeps first so the thread never fires during the automated test suite
    (typical test run completes in under 30 seconds). A random jitter up to
    60 s is added so multiple replicas do not fire the bulk UPDATE in lock-step.
    """
    interval = settings.OVERDUE_SCAN_INTERVAL_SECONDS
    while True:
        jitter = random.uniform(0, 60)
        time.sleep(interval + jitter)
        db = SessionLocal()
        try:
            mark_overdue_borrowings(db)
        except Exception:
            logger.exception("Overdue scanner error")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    t = threading.Thread(target=_overdue_scanner_loop, daemon=True)
    t.start()
    yield


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
