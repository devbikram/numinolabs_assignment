import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from core.limiter import limiter
from models.borrow import BorrowStatus
from schemas.borrow import BorrowingCreate, BorrowingResponse
from schemas.common import PaginatedResponse
from services import borrow as borrow_service

router = APIRouter(prefix="/borrows", tags=["Borrows"])


@router.post(
    "/",
    response_model=BorrowingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow a book",
)
@limiter.limit("30/minute")
def create_borrowing(request: Request, data: BorrowingCreate, db: DBSession):
    return borrow_service.create_borrowing(db, data)


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
    sort_by: Literal["borrowed_at", "due_date", "returned_at", "status"] = Query(
        default="borrowed_at", description="Sort by column"
    ),
    order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
):
    borrowings, total = borrow_service.list_borrowings(
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
    return borrow_service.get_borrowing(db, borrowing_id)


@router.patch(
    "/{borrowing_id}/return",
    response_model=BorrowingResponse,
    summary="Return a borrowed book",
)
@limiter.limit("20/minute")
def return_book(request: Request, borrowing_id: uuid.UUID, db: DBSession):
    return borrow_service.return_book(db, borrowing_id)
