from fastapi import APIRouter, Request

from config.settings import settings
from core.limiter import limiter
from schemas.health import HealthResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status and version.",
)
@limiter.limit("60/minute")
def health_check(request: Request) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        service=settings.APP_TITLE,
    )
