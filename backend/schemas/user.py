import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.user import UserRole
from schemas.base import CustomBaseModel


class LoginRequest(BaseModel):  # BaseModel intentional: str_strip_whitespace must not apply to passwords
    email: EmailStr
    password: str


class TokenResponse(CustomBaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPairResponse(TokenResponse):
    """Returned by POST /auth/login — includes both access and refresh tokens."""
    refresh_token: str


class RefreshRequest(CustomBaseModel):
    refresh_token: str


class LogoutRequest(CustomBaseModel):
    refresh_token: str | None = None


class UserResponse(CustomBaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Admin-only user management schemas ---


class UserCreate(BaseModel):  # BaseModel intentional: str_strip_whitespace must not apply to passwords
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt silently truncates at 72 bytes

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        errors = []
        if not re.search(r"[A-Z]", v):
            errors.append("at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            errors.append("at least one digit")
        if not re.search(r"[^A-Za-z0-9]", v):
            errors.append("at least one special character")
        if errors:
            raise ValueError("Password must contain " + ", ".join(errors))
        return v


class UserStatusUpdate(CustomBaseModel):
    is_active: bool
