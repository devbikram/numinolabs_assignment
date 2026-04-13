import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.author import Author
from models.book import Book, book_authors
from models.borrow import BorrowStatus, Borrowing
from schemas.author import AuthorCreate, AuthorUpdate

from crud._utils import db_create, db_delete, db_update, escape_like


def create_author(db: Session, data: AuthorCreate) -> Author:
    return db_create(db, Author(**data.model_dump()))


def get_author(db: Session, author_id: uuid.UUID) -> Author | None:
    return db.get(Author, author_id)


def get_authors(
    db: Session, *, skip: int = 0, limit: int = 20, search: str | None = None
) -> tuple[list[Author], int]:
    query = select(Author)
    count_query = select(func.count()).select_from(Author)

    if search:
        pattern = f"%{escape_like(search)}%"
        query = query.where(Author.name.ilike(pattern))
        count_query = count_query.where(Author.name.ilike(pattern))

    total = db.scalar(count_query)
    authors = (
        db.scalars(
            query.order_by(Author.name).offset(skip).limit(limit)
        )
        .all()
    )
    return list(authors), total or 0


def update_author(db: Session, author: Author, data: AuthorUpdate) -> Author:
    return db_update(db, author, data)


def author_name_taken(db: Session, name: str, exclude_id=None) -> bool:
    """Return True if a different author already uses this name (case-insensitive)."""
    q = select(Author).where(func.lower(Author.name) == name.lower().strip())
    if exclude_id is not None:
        q = q.where(Author.id != exclude_id)
    return db.scalar(q) is not None


def delete_author(db: Session, author: Author) -> None:
    db_delete(db, author)


def get_author_stats(db: Session, author_id: uuid.UUID) -> dict:
    # All book IDs for this author
    author_books = (
        select(book_authors.c.book_id)
        .where(book_authors.c.author_id == author_id)
    )

    # Total borrows
    total_borrows = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(Borrowing.book_id.in_(author_books))
    ) or 0

    # Active borrows (borrowed + overdue)
    active_borrows = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(Borrowing.book_id.in_(author_books))
        .where(Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]))
    ) or 0

    # Unique readers
    unique_readers = db.scalar(
        select(func.count(func.distinct(Borrowing.member_id)))
        .where(Borrowing.book_id.in_(author_books))
    ) or 0

    # Most borrowed book
    most_borrowed_row = db.execute(
        select(Book.id, Book.title, func.count(Borrowing.id).label("cnt"))
        .join(Borrowing, Borrowing.book_id == Book.id)
        .where(Book.id.in_(author_books))
        .group_by(Book.id, Book.title)
        .order_by(func.count(Borrowing.id).desc())
        .limit(1)
    ).first()

    most_borrowed = None
    if most_borrowed_row:
        most_borrowed = {
            "id": most_borrowed_row.id,
            "title": most_borrowed_row.title,
            "borrow_count": most_borrowed_row.cnt,
        }

    return {
        "total_borrows": total_borrows,
        "active_borrows": active_borrows,
        "unique_readers": unique_readers,
        "most_borrowed": most_borrowed,
    }
