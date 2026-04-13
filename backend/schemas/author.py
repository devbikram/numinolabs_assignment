import uuid
from datetime import datetime

from pydantic import Field

from schemas.base import CustomBaseModel


class AuthorCreate(CustomBaseModel):
    name: str = Field(min_length=1, max_length=255, description="Author's full name")
    bio: str | None = Field(default=None, max_length=2000, description="Author biography")


class AuthorUpdate(CustomBaseModel):
    name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Author's full name"
    )
    bio: str | None = Field(default=None, max_length=2000, description="Author biography")


class AuthorResponse(CustomBaseModel):
    id: uuid.UUID
    name: str
    bio: str | None
    book_count: int = 0
    created_at: datetime
    updated_at: datetime


class AuthorBriefResponse(CustomBaseModel):
    id: uuid.UUID
    name: str
    book_count: int = 0


class MostBorrowedBook(CustomBaseModel):
    id: uuid.UUID
    title: str
    borrow_count: int = 0


class AuthorStats(CustomBaseModel):
    total_borrows: int = 0
    active_borrows: int = 0
    unique_readers: int = 0
    most_borrowed: MostBorrowedBook | None = None
