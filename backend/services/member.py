import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import BadRequestException, ConflictException, NotFoundException
from crud import borrow as borrow_crud
from crud import member as member_crud
from models.member import Member
from schemas.member import MemberCreate, MemberUpdate


def create_member(db: Session, data: MemberCreate) -> Member:
    try:
        return member_crud.create_member(db, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"Member with email '{data.email}' already exists")


def list_members(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    sort_by: str = "full_name",
    order: str = "asc",
) -> tuple[list[Member], int]:
    return member_crud.get_members(
        db, skip=skip, limit=limit, search=search, sort_by=sort_by, order=order,
    )


def get_member(db: Session, member_id: uuid.UUID) -> Member:
    member = member_crud.get_member(db, member_id)
    if not member:
        raise NotFoundException(detail=f"Member with id '{member_id}' not found")
    return member


def get_member_stats(db: Session, member_id: uuid.UUID) -> dict:
    get_member(db, member_id)
    return member_crud.get_member_borrowing_stats(db, member_id)


def update_member(db: Session, member_id: uuid.UUID, data: MemberUpdate) -> Member:
    member = get_member(db, member_id)

    if data.email is not None and data.email != member.email:
        existing = member_crud.get_member_by_email(db, data.email)
        if existing:
            raise ConflictException(detail=f"Member with email '{data.email}' already exists")

    try:
        return member_crud.update_member(db, member, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"Member with email '{data.email}' already exists")


def delete_member(db: Session, member_id: uuid.UUID) -> None:
    member = get_member(db, member_id)
    active = borrow_crud.count_active_borrowings_for_member(db, member_id)
    if active:
        raise BadRequestException(
            detail=f"Cannot delete member '{member.full_name}': {active} active borrowing(s) exist"
        )
    member_crud.delete_member(db, member)
