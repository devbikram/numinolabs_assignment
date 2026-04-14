import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import BadRequestException, ConflictException, NotFoundException
from crud import author as author_crud
from crud import book as book_crud
from crud import borrow as borrow_crud
from crud import category as category_crud
from models.book import Book
from schemas.book import BookCreate, BookUpdate


def _check_category(db: Session, category_id: uuid.UUID) -> None:
    if not category_crud.get_category(db, category_id):
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")


def _check_author(db: Session, author_id: uuid.UUID) -> None:
    if not author_crud.get_author(db, author_id):
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")


def create_book(db: Session, data: BookCreate) -> Book:
    if data.category_id is not None:
        _check_category(db, data.category_id)
    try:
        return book_crud.create_book(db, data)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"Book with ISBN '{data.isbn}' already exists")


def list_books(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    author_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    sort_by: str = "title",
    order: str = "asc",
) -> tuple[list[Book], int]:
    if author_id is not None:
        _check_author(db, author_id)
    if category_id is not None:
        _check_category(db, category_id)
    return book_crud.get_books(
        db, skip=skip, limit=limit,
        search=search, author_id=author_id, category_id=category_id,
        sort_by=sort_by, order=order,
    )


def get_book(db: Session, book_id: uuid.UUID) -> Book:
    book = book_crud.get_book(db, book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")
    return book


def get_book_stats(db: Session, book_id: uuid.UUID) -> dict:
    get_book(db, book_id)
    return book_crud.get_book_borrowing_stats(db, book_id)


def update_book(db: Session, book_id: uuid.UUID, data: BookUpdate) -> Book:
    book = get_book(db, book_id)

    if data.category_id is not None:
        _check_category(db, data.category_id)

    if data.isbn is not None and data.isbn != book.isbn:
        existing = db.scalar(select(Book).where(Book.isbn == data.isbn))
        if existing:
            raise ConflictException(detail=f"Book with ISBN '{data.isbn}' already exists")

    try:
        return book_crud.update_book(db, book, data)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc))
    except IntegrityError as exc:
        db.rollback()
        err = str(exc).lower()
        if "isbn" in err or "uq" in err or "unique" in err:
            raise ConflictException(detail=f"Book with ISBN '{data.isbn}' already exists")
        raise BadRequestException(
            detail="Cannot reduce total_copies below the number of copies currently on loan"
        )


def delete_book(db: Session, book_id: uuid.UUID) -> None:
    book = get_book(db, book_id)
    active = borrow_crud.count_active_borrowings_for_book(db, book_id)
    if active:
        raise BadRequestException(
            detail=f"Cannot delete book '{book.title}': {active} active borrowing(s) exist"
        )
    book_crud.delete_book(db, book)
