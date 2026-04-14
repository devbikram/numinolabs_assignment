import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import BadRequestException, NotFoundException
from crud import author as author_crud
from crud import book as book_crud
from crud import borrow as borrow_crud
from crud import category as category_crud
from crud import member as member_crud
from models.borrow import BorrowStatus, Borrowing
from schemas.borrow import BorrowingCreate

logger = logging.getLogger(__name__)


def _check_book(db: Session, book_id: uuid.UUID) -> None:
    if not book_crud.get_book(db, book_id):
        raise NotFoundException(detail=f"Book with id '{book_id}' not found")


def _check_member(db: Session, member_id: uuid.UUID) -> None:
    if not member_crud.get_member(db, member_id):
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")


def _check_category(db: Session, category_id: uuid.UUID) -> None:
    if not category_crud.get_category(db, category_id):
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")


def _check_author(db: Session, author_id: uuid.UUID) -> None:
    if not author_crud.get_author(db, author_id):
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")


def create_borrowing(db: Session, data: BorrowingCreate) -> Borrowing:
    member = member_crud.get_member(db, data.member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{data.member_id}' not found")

    book = book_crud.get_book(db, data.book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{data.book_id}' not found")

    if borrow_crud.has_active_borrowing(db, data.book_id, data.member_id):
        logger.warning(
            "Duplicate borrow attempt: member=%s book=%s ('%s')",
            data.member_id, data.book_id, book.title,
        )
        raise BadRequestException(
            detail=f"Member already has an active borrowing for '{book.title}'"
        )

    if book.available_copies <= 0:
        logger.warning(
            "No copies available: book=%s ('%s'), member=%s",
            data.book_id, book.title, data.member_id,
        )
        raise BadRequestException(detail=f"Book '{book.title}' has no available copies")

    try:
        borrowing = borrow_crud.create_borrowing(db, data)
    except (IntegrityError, ValueError):
        db.rollback()
        logger.warning(
            "Borrow failed (race condition): book=%s ('%s'), member=%s",
            data.book_id, book.title, data.member_id,
        )
        raise BadRequestException(detail=f"Book '{book.title}' has no available copies")

    logger.info(
        "Book borrowed: borrowing=%s book=%s ('%s') member=%s ('%s') due=%s",
        borrowing.id, data.book_id, book.title,
        data.member_id, member.full_name, data.due_date,
    )
    return borrowing


def list_borrowings(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    book_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    status: BorrowStatus | None = None,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    author_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = "borrowed_at",
    order: str = "desc",
) -> tuple[list[Borrowing], int]:
    if book_id is not None:
        _check_book(db, book_id)
    if member_id is not None:
        _check_member(db, member_id)
    if category_id is not None:
        _check_category(db, category_id)
    if author_id is not None:
        _check_author(db, author_id)
    return borrow_crud.get_borrowings(
        db, skip=skip, limit=limit, book_id=book_id, member_id=member_id,
        status=status, search=search, category_id=category_id, author_id=author_id,
        date_from=date_from, date_to=date_to, sort_by=sort_by, order=order,
    )


def get_borrowing(db: Session, borrowing_id: uuid.UUID) -> Borrowing:
    borrowing = borrow_crud.get_borrowing(db, borrowing_id)
    if not borrowing:
        raise NotFoundException(
            detail=f"Borrowing record with id '{borrowing_id}' not found"
        )
    return borrowing


def return_book(db: Session, borrowing_id: uuid.UUID) -> Borrowing:
    borrowing = get_borrowing(db, borrowing_id)

    if borrowing.status == BorrowStatus.returned:
        logger.warning("Return rejected (already returned): borrowing=%s", borrowing_id)
        raise BadRequestException(detail="This book has already been returned")

    if borrowing.book_id is None:
        # Book was deleted while on loan — mark returned without restoring copies
        borrowing.returned_at = datetime.now(timezone.utc)
        borrowing.status = BorrowStatus.returned
        db.commit()
        db.refresh(borrowing)
        logger.warning(
            "Returned borrowing for deleted book: borrowing=%s member=%s",
            borrowing_id, borrowing.member_id,
        )
        return borrowing

    returned = borrow_crud.return_borrowing(db, borrowing)
    logger.info(
        "Book returned: borrowing=%s book=%s member=%s was_overdue=%s",
        borrowing_id, borrowing.book_id, borrowing.member_id,
        borrowing.status == BorrowStatus.overdue,
    )
    return returned
