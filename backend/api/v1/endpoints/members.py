import uuid

from fastapi import APIRouter, Query, Request, status
from sqlalchemy.exc import IntegrityError

from api.deps import DBSession, PaginationDep
from api.exceptions import ConflictException, NotFoundException
from core.limiter import limiter
from crud import member as member_crud
from schemas.common import MessageResponse, PaginatedResponse
from schemas.member import MemberBorrowingStats, MemberCreate, MemberResponse, MemberUpdate

router = APIRouter(prefix="/members", tags=["Members"])


@router.post(
    "/",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
)
@limiter.limit("20/minute")
def create_member(request: Request, data: MemberCreate, db: DBSession):
    try:
        return member_crud.create_member(db, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(
            detail=f"Member with email '{data.email}' already exists"
        )


@router.get(
    "/",
    response_model=PaginatedResponse[MemberResponse],
    summary="List all members",
)
@limiter.limit("60/minute")
def list_members(
    request: Request,
    pagination: PaginationDep,
    db: DBSession,
    search: str | None = Query(default=None, max_length=200, description="Search by name, email, or library ID"),
    sort_by: str = Query(default="full_name", description="Sort by column"),
    order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort order"),
):
    members, total = member_crud.get_members(
        db, skip=pagination.skip, limit=pagination.limit, search=search,
        sort_by=sort_by, order=order,
    )
    return pagination.paginate(members, total)


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get a member by ID",
)
@limiter.limit("60/minute")
def get_member(request: Request, member_id: uuid.UUID, db: DBSession):
    member = member_crud.get_member(db, member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")
    return member


@router.get(
    "/{member_id}/stats",
    response_model=MemberBorrowingStats,
    summary="Get borrowing stats for a member",
)
@limiter.limit("60/minute")
def get_member_stats(request: Request, member_id: uuid.UUID, db: DBSession):
    member = member_crud.get_member(db, member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")
    return member_crud.get_member_borrowing_stats(db, member_id)


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update a member",
)
@limiter.limit("20/minute")
def update_member(
    request: Request, member_id: uuid.UUID, data: MemberUpdate, db: DBSession
):
    member = member_crud.get_member(db, member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")

    if data.email is not None and data.email != member.email:
        existing = member_crud.get_member_by_email(db, data.email)
        if existing:
            raise ConflictException(
                detail=f"Member with email '{data.email}' already exists"
            )

    return member_crud.update_member(db, member, data)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a member",
)
@limiter.limit("20/minute")
def delete_member(request: Request, member_id: uuid.UUID, db: DBSession):
    member = member_crud.get_member(db, member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")
    member_crud.delete_member(db, member)
    return MessageResponse(message="Member deleted successfully")
