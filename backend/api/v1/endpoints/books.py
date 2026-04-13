import uuid

from fastapi import APIRouter, Query, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api.deps import DBSession, PaginationDep
from api.exceptions import ConflictException, NotFoundException, BadRequestException
from core.limiter import limiter
from crud import book as book_crud
from models.book import Book
from schemas.book import BookBorrowingStats, BookCreate, BookResponse, BookUpdate
from schemas.common import MessageResponse, PaginatedResponse

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a book",
)
@limiter.limit("20/minute")
def create_book(request: Request, data: BookCreate, db: DBSession):
    try:
        return book_crud.create_book(db, data)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"Book with ISBN '{data.isbn}' already exists")


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
    sort_by: str = Query(default="title", description="Sort by column"),
    order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort order"),
):
    books, total = book_crud.get_books(
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
    book = book_crud.get_book(db, book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")
    return book


@router.get(
    "/{book_id}/stats",
    response_model=BookBorrowingStats,
    summary="Get borrowing stats for a book",
)
@limiter.limit("60/minute")
def get_book_stats(request: Request, book_id: uuid.UUID, db: DBSession):
    book = book_crud.get_book(db, book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")
    return book_crud.get_book_borrowing_stats(db, book_id)


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update a book",
)
@limiter.limit("20/minute")
def update_book(
    request: Request, book_id: uuid.UUID, data: BookUpdate, db: DBSession
):
    book = book_crud.get_book(db, book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")

    # If updating ISBN, check for duplicate
    if data.isbn is not None and data.isbn != book.isbn:
        existing = db.scalar(select(Book).where(Book.isbn == data.isbn))
        if existing:
            raise ConflictException(
                detail=f"Book with ISBN '{data.isbn}' already exists"
            )

    try:
        return book_crud.update_book(db, book, data)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise BadRequestException(
            detail="Cannot reduce total_copies below the number of copies currently on loan"
        )


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a book",
)
@limiter.limit("20/minute")
def delete_book(request: Request, book_id: uuid.UUID, db: DBSession):
    book = book_crud.get_book(db, book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")
    book_crud.delete_book(db, book)
    return MessageResponse(message="Book deleted successfully")
