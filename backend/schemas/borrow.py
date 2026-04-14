import uuid
from datetime import datetime, timedelta, timezone

from pydantic import Field, field_validator

from models.borrow import BorrowStatus
from schemas.base import CustomBaseModel
from schemas.book import BookBriefResponse


class BorrowingCreate(CustomBaseModel):
    book_id: uuid.UUID = Field(description="ID of the book to borrow")
    member_id: uuid.UUID = Field(description="ID of the member borrowing the book")
    due_date: datetime = Field(description="Expected return date (must be in the future)")

    @field_validator("due_date")
    @classmethod
    def due_date_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("due_date must be timezone-aware (include UTC offset, e.g. +00:00 or Z)")
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError("due_date must be a future datetime")
        upper = now + timedelta(days=5 * 365)
        if v > upper:
            raise ValueError("due_date cannot be more than 5 years in the future")
        return v


class MemberBriefResponse(CustomBaseModel):
    id: uuid.UUID
    library_id: str
    full_name: str
    email: str
    phone: str | None = None


class BorrowingResponse(CustomBaseModel):
    id: uuid.UUID
    book_id: uuid.UUID | None
    member_id: uuid.UUID | None
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: BorrowStatus
    book: BookBriefResponse | None
    member: MemberBriefResponse | None
    created_at: datetime
    updated_at: datetime
