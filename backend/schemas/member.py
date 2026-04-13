import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from schemas.base import CustomBaseModel


class MemberCreate(CustomBaseModel):
    full_name: str = Field(min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(description="Email address")
    phone: str | None = Field(
        default=None, max_length=20, description="Phone number"
    )
    address: str | None = Field(default=None, max_length=256, description="Address")


class MemberUpdate(CustomBaseModel):
    full_name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Full name"
    )
    email: EmailStr | None = Field(default=None, description="Email address")
    phone: str | None = Field(
        default=None, max_length=20, description="Phone number"
    )
    address: str | None = Field(default=None, max_length=256, description="Address")


class MemberResponse(CustomBaseModel):
    id: uuid.UUID
    library_id: str
    full_name: str
    email: str
    phone: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime


class MemberBorrowingStats(CustomBaseModel):
    total: int = 0
    borrowed: int = 0
    returned: int = 0
    overdue: int = 0
