from fastapi import APIRouter, Request

from api.deps import DBSession
from core.limiter import limiter
from schemas.dashboard import DashboardStats
from services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats, summary="Get dashboard statistics")
@limiter.limit("30/minute")
def get_dashboard_stats(request: Request, db: DBSession):
    return dashboard_service.get_dashboard_stats(db)
