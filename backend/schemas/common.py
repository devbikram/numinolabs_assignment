from typing import Generic, TypeVar

from schemas.base import CustomBaseModel

T = TypeVar("T")


class PaginatedResponse(CustomBaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


class MessageResponse(CustomBaseModel):
    message: str
