import uuid

from fastapi import APIRouter, Request, status

from api.deps import AdminUser, CurrentUser, DBSession, PaginationDep, TokenPayload
from core.limiter import limiter
from schemas.common import PaginatedResponse
from schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
)
from services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPairResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: DBSession):
    return auth_service.login(db, body)


@router.get("/me", response_model=UserResponse)
@limiter.limit("60/minute")
def get_current_user_info(request: Request, current_user: CurrentUser):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the current access token")
@limiter.limit("30/minute")
def logout(request: Request, token_payload: TokenPayload, body: LogoutRequest | None = None):
    auth_service.logout(token_payload, body)


@router.post("/refresh", response_model=TokenPairResponse, summary="Exchange a refresh token for a new access token")
@limiter.limit("10/minute")
def refresh(request: Request, body: RefreshRequest, db: DBSession):
    return auth_service.refresh_tokens(db, body)


# --- Admin-only user management ---


@router.get("/users", response_model=PaginatedResponse[UserResponse], summary="List all users (admin only)")
@limiter.limit("30/minute")
def list_users(request: Request, pagination: PaginationDep, db: DBSession, _admin: AdminUser):
    users, total = auth_service.list_all_users(db, skip=pagination.skip, limit=pagination.limit)
    return pagination.paginate(users, total)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manager account (admin only)",
)
@limiter.limit("20/minute")
def create_user(request: Request, body: UserCreate, db: DBSession, _admin: AdminUser):
    return auth_service.create_user(db, body)


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate a user (admin only)",
)
@limiter.limit("20/minute")
def update_user_status(request: Request, user_id: uuid.UUID, body: UserStatusUpdate, db: DBSession, admin: AdminUser):
    return auth_service.update_user_status(db, user_id, body, admin)
