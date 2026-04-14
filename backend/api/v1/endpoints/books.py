import uuid
from typing import Literal

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from core.limiter import limiter
from schemas.book import BookBorrowingStats, BookCreate, BookResponse, BookUpdate
from schemas.common import MessageResponse, PaginatedResponse
from services import book as book_service

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
)
@limiter.limit("20/minute")
def create_book(request: Request, data: BookCreate, db: DBSession):
    return book_service.create_book(db, data)


@router.get(
    "/",
    response_model=PaginatedResponse[BookResponse],
    summary="List all books",
)
@limiter.limit("60/minute")
def list_books(
    request: Request,
    pagination: PaginationDep,
    db: DBSession,
    search: str | None = Query(default=None, max_length=200, description="Search by title or ISBN (case-insensitive substring)"),
    author_id: uuid.UUID | None = Query(default=None, description="Filter by author ID"),
    category_id: uuid.UUID | None = Query(default=None, description="Filter by category ID"),
    sort_by: Literal["title", "isbn", "published_year", "available_copies", "total_copies"] = Query(
        default="title", description="Sort by column"
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort order"),
):
    books, total = book_service.list_books(
        db, skip=pagination.skip, limit=pagination.limit,
        search=search, author_id=author_id, category_id=category_id,
        sort_by=sort_by, order=order,
    )
    return pagination.paginate(books, total)


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get a book by ID",
)
@limiter.limit("60/minute")
def get_book(request: Request, book_id: uuid.UUID, db: DBSession):
    return book_service.get_book(db, book_id)


@router.get(
    "/{book_id}/stats",
    response_model=BookBorrowingStats,
    summary="Get borrowing stats for a book",
)
@limiter.limit("60/minute")
def get_book_stats(request: Request, book_id: uuid.UUID, db: DBSession):
    return book_service.get_book_stats(db, book_id)


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update a book",
)
@limiter.limit("20/minute")
def update_book(
    request: Request, book_id: uuid.UUID, data: BookUpdate, db: DBSession
):
    return book_service.update_book(db, book_id, data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a book",
)
@limiter.limit("20/minute")
def delete_book(request: Request, book_id: uuid.UUID, db: DBSession):
    book_service.delete_book(db, book_id)
    return MessageResponse(message="Book deleted successfully")
