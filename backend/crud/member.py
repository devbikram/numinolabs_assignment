import uuid

from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from models.borrow import BorrowStatus, Borrowing
from models.member import Member
from schemas.member import MemberCreate, MemberUpdate

from crud._utils import db_create, db_delete, db_update, escape_like


def _next_library_id(db: Session) -> str:
    """Generate the next sequential library ID like LIBU0001.

    Uses a transaction-scoped advisory lock to prevent race conditions.
    The numeric suffix is extracted in SQL via REGEXP_REPLACE + CAST so the
    result is always correct regardless of prefix width or historical format drift.
    """
    db.execute(text("SELECT pg_advisory_xact_lock(42)"))
    # Extract the trailing digits from every library_id, cast to integer, take max.
    # REGEXP_REPLACE(library_id, '[^0-9]', '', 'g') strips all non-digit characters.
    max_seq: int | None = db.scalar(
        text(
            "SELECT MAX(CAST(REGEXP_REPLACE(library_id, '[^0-9]', '', 'g') AS INTEGER))"
            " FROM member"
        )
    )
    seq = (max_seq or 0) + 1
    return f"LIBU{seq:04d}"


def create_member(db: Session, data: MemberCreate) -> Member:
    library_id = _next_library_id(db)
    return db_create(db, Member(**data.model_dump(), library_id=library_id))


def get_member(db: Session, member_id: uuid.UUID) -> Member | None:
    return db.get(Member, member_id)


def get_member_by_email(db: Session, email: str) -> Member | None:
    return db.scalar(select(Member).where(Member.email == email))


def get_members(
    db: Session, *, skip: int = 0, limit: int = 20, search: str | None = None,
    sort_by: str = "full_name", order: str = "asc",
) -> tuple[list[Member], int]:
    query = select(Member)
    count_query = select(func.count()).select_from(Member)

    if search:
        pattern = f"%{escape_like(search)}%"
        search_filter = or_(
            Member.full_name.ilike(pattern),
            Member.email.ilike(pattern),
            Member.library_id.ilike(pattern),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = db.scalar(count_query)

    SORTABLE_COLUMNS = {
        "library_id": Member.library_id,
        "full_name": Member.full_name,
        "email": Member.email,
        "phone": Member.phone,
        "address": Member.address,
    }
    col = SORTABLE_COLUMNS.get(sort_by, Member.full_name)
    order_clause = col.desc() if order == "desc" else col.asc()

    members = (
        db.scalars(
            query.order_by(order_clause).offset(skip).limit(limit)
        )
        .all()
    )
    return list(members), total or 0


def update_member(db: Session, member: Member, data: MemberUpdate) -> Member:
    return db_update(db, member, data)


def delete_member(db: Session, member: Member) -> None:
    db_delete(db, member)


def get_member_borrowing_stats(db: Session, member_id: uuid.UUID) -> dict:
    rows = db.execute(
        select(Borrowing.status, func.count())
        .where(Borrowing.member_id == member_id)
        .group_by(Borrowing.status)
    ).all()
    counts = {status.value: count for status, count in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "borrowed": counts.get(BorrowStatus.borrowed.value, 0),
        "returned": counts.get(BorrowStatus.returned.value, 0),
        "overdue": counts.get(BorrowStatus.overdue.value, 0),
    }
