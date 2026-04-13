from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config.database import SessionLocal
from core.security import decode_token, is_token_revoked
from models.user import User, UserRole
from schemas.common import PaginatedResponse


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False)


def _verified_payload(
    credentials: HTTPAuthorizationCredentials | None,
) -> dict:
    """Decode and verify a JWT, checking expiry and revocation."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return payload


def get_current_user(
    db: DBSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> User:
    payload = _verified_payload(credentials)
    user = db.get(User, UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> dict:
    """Return the raw decoded JWT payload without a DB lookup."""
    return _verified_payload(credentials)


TokenPayload = Annotated[dict, Depends(get_token_payload)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


class PaginationParams:
    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            default=20, ge=1, le=100, description="Max records to return"
        ),
    ):
        self.skip = skip
        self.limit = limit

    def paginate(self, items: list, total: int) -> PaginatedResponse:
        return PaginatedResponse(items=items, total=total, skip=self.skip, limit=self.limit)


PaginationDep = Annotated[PaginationParams, Depends()]
