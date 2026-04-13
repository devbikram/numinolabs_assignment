import uuid
from datetime import datetime

from pydantic import Field

from schemas.author import AuthorBriefResponse
from schemas.base import CustomBaseModel
from schemas.category import CategoryBriefResponse


class BookCreate(CustomBaseModel):
    title: str = Field(min_length=1, max_length=500, description="Book title")
    author_ids: list[uuid.UUID] = Field(default_factory=list, description="Author IDs")
    isbn: str = Field(
        pattern=r"^\d{10}(\d{3})?$",
        description="ISBN-10 or ISBN-13 (digits only)",
    )
    category_id: uuid.UUID | None = Field(default=None, description="Category ID")
    published_year: int | None = Field(
        default=None, ge=1000, le=2100, description="Year of publication"
    )
    total_copies: int = Field(default=1, ge=1, description="Total number of copies")


class BookUpdate(CustomBaseModel):
    title: str | None = Field(
        default=None, min_length=1, max_length=500, description="Book title"
    )
    author_ids: list[uuid.UUID] | None = Field(
        default=None, min_length=1, description="Author IDs"
    )
    isbn: str | None = Field(
        default=None,
        pattern=r"^\d{10}(\d{3})?$",
        description="ISBN-10 or ISBN-13 (digits only)",
    )
    category_id: uuid.UUID | None = Field(default=None, description="Category ID")
    published_year: int | None = Field(
        default=None, ge=1000, le=2100, description="Year of publication"
    )
    total_copies: int | None = Field(
        default=None, ge=1, description="Total number of copies"
    )


class BookResponse(CustomBaseModel):
    id: uuid.UUID
    title: str
    authors: list[AuthorBriefResponse]
    isbn: str
    category_id: uuid.UUID | None
    category: CategoryBriefResponse | None
    published_year: int | None
    total_copies: int
    available_copies: int
    borrow_count: int = 0
    created_at: datetime
    updated_at: datetime


class BookBriefResponse(CustomBaseModel):
    id: uuid.UUID
    title: str
    isbn: str


class BookBorrowingStats(CustomBaseModel):
    total_borrows: int = 0
    active_borrows: int = 0
    unique_readers: int = 0
