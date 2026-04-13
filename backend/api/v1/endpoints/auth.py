import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.deps import AdminUser, CurrentUser, DBSession, PaginationDep, TokenPayload
from api.exceptions import BadRequestException, ConflictException, NotFoundException
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from crud.user import create_manager, get_user_by_id, get_users, set_user_active
from core.limiter import limiter
from models.user import User
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

router = APIRouter(prefix="/auth", tags=["auth"])

# Computed once at startup so unknown-email logins always pay the same bcrypt cost.
_DUMMY_HASH = hash_password("__dummy_sentinel__")


@router.post("/login", response_model=TokenPairResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: DBSession):
    user = db.scalar(select(User).where(User.email == body.email))
    # Always call verify_password to prevent user-enumeration via timing.
    candidate_hash = user.hashed_password if user else _DUMMY_HASH
    password_ok = verify_password(body.password, candidate_hash)
    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
@limiter.limit("60/minute")
def get_current_user_info(request: Request, current_user: CurrentUser):
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the current access token")
@limiter.limit("30/minute")
def logout(request: Request, token_payload: TokenPayload, body: LogoutRequest | None = None):
    # Revoke the access token
    jti = token_payload.get("jti")
    if jti:
        revoke_token(jti, exp=token_payload.get("exp"))
    # Revoke the refresh token if provided
    if body and body.refresh_token:
        refresh_payload = decode_token(body.refresh_token)
        if refresh_payload and refresh_payload.get("token_type") == "refresh":
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                revoke_token(refresh_jti, exp=refresh_payload.get("exp"))


@router.post("/refresh", response_model=TokenPairResponse, summary="Exchange a refresh token for a new access token")
@limiter.limit("10/minute")
def refresh(request: Request, body: RefreshRequest, db: DBSession):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    # Rotate: revoke the consumed refresh token, issue a fresh pair
    if jti:
        revoke_token(jti, exp=payload.get("exp"))
    return TokenPairResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


# --- Admin-only user management ---


@router.get("/users", response_model=PaginatedResponse[UserResponse], summary="List all users (admin only)")
@limiter.limit("30/minute")
def list_users(request: Request, pagination: PaginationDep, db: DBSession, _admin: AdminUser):
    users, total = get_users(db, skip=pagination.skip, limit=pagination.limit)
    return pagination.paginate(users, total)


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manager account (admin only)",
)
@limiter.limit("20/minute")
def create_user(request: Request, body: UserCreate, db: DBSession, _admin: AdminUser):
    try:
        return create_manager(db, body)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail="A user with this email already exists")


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate a user (admin only)",
)
@limiter.limit("20/minute")
def update_user_status(request: Request, user_id: uuid.UUID, body: UserStatusUpdate, db: DBSession, admin: AdminUser):
    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException(detail="User not found")
    if user.id == admin.id and not body.is_active:
        raise BadRequestException(detail="You cannot deactivate your own account")
    return set_user_active(db, user, body.is_active)
