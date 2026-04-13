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


def create_borrowing(db: Session, data: BorrowingCreate) -> Borrowing:
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
