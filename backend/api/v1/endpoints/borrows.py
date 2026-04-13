import uuid
from datetime import date

from fastapi import APIRouter, Query, Request, status
from sqlalchemy.exc import IntegrityError

from api.deps import DBSession, PaginationDep
from api.exceptions import BadRequestException, NotFoundException
from core.limiter import limiter
from crud import book as book_crud
from crud import borrow as borrow_crud
from crud import member as member_crud
from models.borrow import BorrowStatus
from schemas.borrow import BorrowingCreate, BorrowingResponse
from schemas.common import PaginatedResponse

router = APIRouter(prefix="/borrows", tags=["Borrows"])


@router.post(
    "/",
    response_model=BorrowingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow a book",
)
@limiter.limit("30/minute")
def create_borrowing(request: Request, data: BorrowingCreate, db: DBSession):
    # Validate member exists
    member = member_crud.get_member(db, data.member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{data.member_id}' not found")

    # Validate book exists
    book = book_crud.get_book(db, data.book_id)
    if not book:
        raise NotFoundException(detail=f"Book with id '{data.book_id}' not found")

    # Check available copies (fast-fail guard; DB constraint is authoritative)
    if book.available_copies <= 0:
        raise BadRequestException(detail=f"Book '{book.title}' has no available copies")

    # Create borrowing record (trigger auto-updates available_copies)
    try:
        borrowing = borrow_crud.create_borrowing(db, data)
    except IntegrityError:
        db.rollback()
        raise BadRequestException(
            detail=f"Book '{book.title}' has no available copies"
        )
    return borrowing


@router.get(
    "/",
    response_model=PaginatedResponse[BorrowingResponse],
    summary="List borrowing records",
)
@limiter.limit("30/minute")
def list_borrowings(
    request: Request,
    pagination: PaginationDep,
    db: DBSession,
    book_id: uuid.UUID | None = Query(default=None, description="Filter by book"),
    member_id: uuid.UUID | None = Query(default=None, description="Filter by member"),
    borrowing_status: BorrowStatus | None = Query(
        default=None, alias="status", description="Filter by status"
    ),
    search: str | None = Query(
        default=None, max_length=200, description="Search by book title, member name, email, or library ID"
    ),
    category_id: uuid.UUID | None = Query(default=None, description="Filter by book category"),
    author_id: uuid.UUID | None = Query(default=None, description="Filter by author ID"),
    date_from: date | None = Query(default=None, description="Filter borrowings from this date (inclusive)"),
    date_to: date | None = Query(default=None, description="Filter borrowings up to this date (inclusive)"),
    sort_by: str = Query(default="borrowed_at", description="Sort by column"),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
):
    borrowings, total = borrow_crud.get_borrowings(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        book_id=book_id,
        member_id=member_id,
        status=borrowing_status,
        search=search,
        category_id=category_id,
        author_id=author_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
    )
    return pagination.paginate(borrowings, total)


@router.get(
    "/{borrowing_id}",
    response_model=BorrowingResponse,
    summary="Get a borrowing record by ID",
)
@limiter.limit("60/minute")
def get_borrowing(request: Request, borrowing_id: uuid.UUID, db: DBSession):
    borrowing = borrow_crud.get_borrowing(db, borrowing_id)
    if not borrowing:
        raise NotFoundException(
            detail=f"Borrowing record with id '{borrowing_id}' not found"
        )
    return borrowing


@router.patch(
    "/{borrowing_id}/return",
    response_model=BorrowingResponse,
    summary="Return a borrowed book",
)
@limiter.limit("20/minute")
def return_book(request: Request, borrowing_id: uuid.UUID, db: DBSession):
    borrowing = borrow_crud.get_borrowing(db, borrowing_id)
    if not borrowing:
        raise NotFoundException(
            detail=f"Borrowing record with id '{borrowing_id}' not found"
        )

    if borrowing.status == BorrowStatus.returned:
        raise BadRequestException(detail="This book has already been returned")

    # Return the book (trigger auto-updates available_copies)
    return borrow_crud.return_borrowing(db, borrowing)
