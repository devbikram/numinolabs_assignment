from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.v1.endpoints import auth, authors, books, borrows, categories, dashboard, health, members

v1_router = APIRouter(prefix="/api/v1")

# Public routes
v1_router.include_router(health.router)
# Auth router is intentionally unguarded — login, refresh, me, and health must be
# publicly accessible. The three admin-only endpoints inside it are individually
# protected by the AdminUser dependency. Any new handler added to auth.router
# MUST explicitly declare its own auth dependency.
v1_router.include_router(auth.router)

# Protected routes — require a valid JWT
_auth = [Depends(get_current_user)]
v1_router.include_router(authors.router, dependencies=_auth)
v1_router.include_router(categories.router, dependencies=_auth)
v1_router.include_router(books.router, dependencies=_auth)
v1_router.include_router(members.router, dependencies=_auth)
v1_router.include_router(borrows.router, dependencies=_auth)
v1_router.include_router(dashboard.router, dependencies=_auth)
