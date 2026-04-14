import uuid
from typing import Literal

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from core.limiter import limiter
from schemas.common import MessageResponse, PaginatedResponse
from schemas.member import MemberBorrowingStats, MemberCreate, MemberResponse, MemberUpdate
from services import member as member_service

router = APIRouter(prefix="/members", tags=["Members"])


@router.post(
    "/",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
)
@limiter.limit("20/minute")
def create_member(request: Request, data: MemberCreate, db: DBSession):
    return member_service.create_member(db, data)


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
    sort_by: Literal["full_name", "email", "library_id", "created_at"] = Query(
        default="full_name", description="Sort by column"
    ),
    order: str = Query(default="asc", pattern="^(asc|desc)$", description="Sort order"),
):
    members, total = member_service.list_members(
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
    return member_service.get_member(db, member_id)


@router.get(
    "/{member_id}/stats",
    response_model=MemberBorrowingStats,
    summary="Get borrowing stats for a member",
)
@limiter.limit("60/minute")
def get_member_stats(request: Request, member_id: uuid.UUID, db: DBSession):
    return member_service.get_member_stats(db, member_id)


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update a member",
)
@limiter.limit("20/minute")
def update_member(
    request: Request, member_id: uuid.UUID, data: MemberUpdate, db: DBSession
):
    return member_service.update_member(db, member_id, data)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a member",
)
@limiter.limit("20/minute")
def delete_member(request: Request, member_id: uuid.UUID, db: DBSession):
    member_service.delete_member(db, member_id)
    return MessageResponse(message="Member deleted successfully")
