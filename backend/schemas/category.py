import uuid
from datetime import datetime

from pydantic import Field

from schemas.base import CustomBaseModel


class CategoryCreate(CustomBaseModel):
    name: str = Field(min_length=1, max_length=100, description="Category name")


class CategoryUpdate(CustomBaseModel):
    name: str | None = Field(
        default=None, min_length=1, max_length=100, description="Category name"
    )


class CategoryResponse(CustomBaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CategoryBriefResponse(CustomBaseModel):
    id: uuid.UUID
    name: str
