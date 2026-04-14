import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from models.author import Author
from models.book import Book
from models.borrow import BorrowStatus, Borrowing
from models.member import Member
from schemas.borrow import BorrowingCreate

from crud._utils import escape_like


def has_active_borrowing(
    db: Session, book_id: uuid.UUID, member_id: uuid.UUID
) -> bool:
    """Return True if the member already has an active (borrowed/overdue) borrowing for this book."""
    count = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(
            Borrowing.book_id == book_id,
            Borrowing.member_id == member_id,
            Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]),
        )
    )
    return (count or 0) > 0


def count_active_borrowings_for_book(db: Session, book_id: uuid.UUID) -> int:
    """Return the number of active (borrowed/overdue) borrowings for a given book."""
    return db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(
            Borrowing.book_id == book_id,
            Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]),
        )
    ) or 0


def count_active_borrowings_for_member(db: Session, member_id: uuid.UUID) -> int:
    """Return the number of active (borrowed/overdue) borrowings for a given member."""
    return db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(
            Borrowing.member_id == member_id,
            Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]),
        )
    ) or 0


def create_borrowing(db: Session, data: BorrowingCreate) -> Borrowing:
    # Atomically decrement available_copies; guards against race conditions.
    # On PostgreSQL the AFTER INSERT trigger will recalculate the authoritative
    # value, but this application-level update keeps SQLite (tests) correct too.
    result = db.execute(
        update(Book)
        .where(Book.id == data.book_id, Book.available_copies > 0)
        .values(available_copies=Book.available_copies - 1)
    )
    if result.rowcount == 0:
        raise ValueError("No available copies")

    borrowing = Borrowing(
        book_id=data.book_id,
        member_id=data.member_id,
        borrowed_at=datetime.now(timezone.utc),
        due_date=data.due_date,
        status=BorrowStatus.borrowed,
    )
    db.add(borrowing)
    db.commit()
    # Re-fetch with eager-loaded relations to avoid DetachedInstanceError on serialization
    return get_borrowing(db, borrowing.id)


def get_borrowings(
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
    query = select(Borrowing).options(
        selectinload(Borrowing.book),
        selectinload(Borrowing.member),
    )
    count_query = select(func.count()).select_from(Borrowing)

    conditions = []
    if search:
        pattern = f"%{escape_like(search)}%"
        conditions.append(or_(
            Borrowing.book.has(Book.title.ilike(pattern)),
            Borrowing.book.has(Book.authors.any(Author.name.ilike(pattern))),
            Borrowing.member.has(Member.full_name.ilike(pattern)),
            Borrowing.member.has(Member.email.ilike(pattern)),
            Borrowing.member.has(Member.library_id.ilike(pattern)),
        ))
    if category_id is not None:
        conditions.append(Borrowing.book.has(Book.category_id == category_id))
    if author_id is not None:
        conditions.append(Borrowing.book.has(Book.authors.any(Author.id == author_id)))
    if book_id is not None:
        conditions.append(Borrowing.book_id == book_id)
    if member_id is not None:
        conditions.append(Borrowing.member_id == member_id)
    if status is not None:
        conditions.append(Borrowing.status == status)
    if date_from is not None:
        conditions.append(Borrowing.borrowed_at >= datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc))
    if date_to is not None:
        conditions.append(Borrowing.borrowed_at <= datetime.combine(date_to, datetime.max.time(), tzinfo=timezone.utc))

    for cond in conditions:
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = db.scalar(count_query)

    SORTABLE_COLUMNS = {
        "borrowed_at": Borrowing.borrowed_at,
        "due_date": Borrowing.due_date,
        "returned_at": Borrowing.returned_at,
        "status": Borrowing.status,
    }
    col = SORTABLE_COLUMNS.get(sort_by, Borrowing.borrowed_at)
    order_clause = col.desc() if order == "desc" else col.asc()

    borrowings = (
        db.scalars(
            query.order_by(order_clause).offset(skip).limit(limit)
        )
        .all()
    )
    return list(borrowings), total or 0


def get_borrowing(db: Session, borrowing_id: uuid.UUID) -> Borrowing | None:
    return db.scalar(
        select(Borrowing)
        .where(Borrowing.id == borrowing_id)
        .options(selectinload(Borrowing.book), selectinload(Borrowing.member))
    )


def return_borrowing(db: Session, borrowing: Borrowing) -> Borrowing:
    borrowing.returned_at = datetime.now(timezone.utc)
    borrowing.status = BorrowStatus.returned
    # Restore an available copy (trigger will reconcile on PostgreSQL)
    db.execute(
        update(Book)
        .where(Book.id == borrowing.book_id)
        .values(available_copies=Book.available_copies + 1)
    )
    db.commit()
    # Re-fetch with eager-loaded relations so book/member are available for serialization
    return get_borrowing(db, borrowing.id)


def mark_overdue_borrowings(db: Session) -> int:
    """Bulk-transition borrowed records with a past due_date to 'overdue'.

    Returns the number of rows updated. The PostgreSQL trigger
    (sync_available_copies) counts both 'borrowed' and 'overdue' as active
    copies, so available_copies is unchanged by the status transition.
    """
    result = db.execute(
        update(Borrowing)
        .where(
            Borrowing.status == BorrowStatus.borrowed,
            Borrowing.due_date < datetime.now(timezone.utc),
        )
        .values(status=BorrowStatus.overdue, updated_at=datetime.now(timezone.utc))
        .execution_options(synchronize_session=False)
    )
    db.commit()
    return result.rowcount
