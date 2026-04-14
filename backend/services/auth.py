import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import BadRequestException, ConflictException, NotFoundException
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_token_revoked,
    revoke_token,
    revoke_token_if_unused,
    verify_password,
)
from crud.user import create_manager, get_user_by_id, get_users, set_user_active
from models.user import User
from schemas.user import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenPairResponse,
    UserCreate,
    UserStatusUpdate,
)

# Computed once at startup so unknown-email logins always pay the same bcrypt cost.
_DUMMY_HASH = hash_password("__dummy_sentinel__")


def login(db: Session, body: LoginRequest) -> TokenPairResponse:
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


def logout(token_payload: dict, body: LogoutRequest | None = None) -> None:
    jti = token_payload.get("jti")
    if jti:
        revoke_token(jti, exp=token_payload.get("exp"))
    if body and body.refresh_token:
        refresh_payload = decode_token(body.refresh_token)
        if refresh_payload and refresh_payload.get("token_type") == "refresh":
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                revoke_token(refresh_jti, exp=refresh_payload.get("exp"))


def refresh_tokens(db: Session, body: RefreshRequest) -> TokenPairResponse:
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    jti = payload.get("jti")
    # Atomically consume the refresh token — only the first caller wins.
    if jti and not revoke_token_if_unused(jti, exp=payload.get("exp")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return TokenPairResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


def list_all_users(
    db: Session, *, skip: int = 0, limit: int = 100
) -> tuple[list[User], int]:
    return get_users(db, skip=skip, limit=limit)


def create_user(db: Session, body: UserCreate) -> User:
    try:
        return create_manager(db, body)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail="A user with this email already exists")


def update_user_status(
    db: Session, user_id: uuid.UUID, body: UserStatusUpdate, admin: User
) -> User:
    user = get_user_by_id(db, user_id)
    if user is None:
        raise NotFoundException(detail="User not found")
    if user.id == admin.id and not body.is_active:
        raise BadRequestException(detail="You cannot deactivate your own account")
    return set_user_active(db, user, body.is_active)
