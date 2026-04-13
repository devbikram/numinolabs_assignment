import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from models.author import Author
from models.book import Book
from models.borrow import BorrowStatus, Borrowing
from schemas.book import BookCreate, BookUpdate

from crud._utils import db_create, db_delete, escape_like


def create_book(db: Session, data: BookCreate) -> Book:
    author_ids = data.author_ids
    book_data = data.model_dump(exclude={"author_ids"})
    book_data["available_copies"] = book_data["total_copies"]  # new copies are all available
    book = Book(**book_data)
    if author_ids:
        authors = db.scalars(select(Author).where(Author.id.in_(author_ids))).all()
        found_ids = {a.id for a in authors}
        missing = [aid for aid in author_ids if aid not in found_ids]
        if missing:
            raise ValueError(f"Author(s) not found: {[str(m) for m in missing]}")
        book.authors = list(authors)
    return db_create(db, book)


def get_book(db: Session, book_id: uuid.UUID) -> Book | None:
    return db.get(Book, book_id)


def get_books(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    author_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    sort_by: str = "title",
    order: str = "asc",
) -> tuple[list[Book], int]:
    query = select(Book)
    count_query = select(func.count()).select_from(Book)

    if search:
        pattern = f"%{escape_like(search)}%"
        search_filter = or_(Book.title.ilike(pattern), Book.isbn.ilike(pattern))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if author_id is not None:
        author_filter = Book.authors.any(Author.id == author_id)
        query = query.where(author_filter)
        count_query = count_query.where(author_filter)

    if category_id is not None:
        query = query.where(Book.category_id == category_id)
        count_query = count_query.where(Book.category_id == category_id)

    total = db.scalar(count_query)

    SORTABLE_COLUMNS = {
        "title": Book.title,
        "isbn": Book.isbn,
        "published_year": Book.published_year,
        "available_copies": Book.available_copies,
        "total_copies": Book.total_copies,
    }
    col = SORTABLE_COLUMNS.get(sort_by, Book.title)
    order_clause = col.desc() if order == "desc" else col.asc()

    books = (
        db.scalars(query.order_by(order_clause).offset(skip).limit(limit))
        .all()
    )
    return list(books), total or 0


def update_book(db: Session, book: Book, data: BookUpdate) -> Book:
    update_data = data.model_dump(exclude_unset=True)
    author_ids = update_data.pop("author_ids", None)
    new_total = update_data.get("total_copies")
    if new_total is not None:
        if new_total > book.total_copies:
            book.available_copies += new_total - book.total_copies
        elif new_total < book.total_copies:
            # Cap available_copies so it never exceeds the new (lower) total
            book.available_copies = min(book.available_copies, new_total)
    for field, value in update_data.items():
        setattr(book, field, value)
    if author_ids is not None:
        authors = db.scalars(select(Author).where(Author.id.in_(author_ids))).all()
        found_ids = {a.id for a in authors}
        missing = [aid for aid in author_ids if aid not in found_ids]
        if missing:
            raise ValueError(f"Author(s) not found: {[str(m) for m in missing]}")
        book.authors = list(authors)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    db_delete(db, book)


def get_book_borrowing_stats(db: Session, book_id: uuid.UUID) -> dict:
    base = select(Borrowing).where(Borrowing.book_id == book_id)

    total_borrows = db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0

    active_borrows = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(Borrowing.book_id == book_id)
        .where(Borrowing.status.in_([BorrowStatus.borrowed, BorrowStatus.overdue]))
    ) or 0

    unique_readers = db.scalar(
        select(func.count(func.distinct(Borrowing.member_id)))
        .where(Borrowing.book_id == book_id)
    ) or 0

    return {
        "total_borrows": total_borrows,
        "active_borrows": active_borrows,
        "unique_readers": unique_readers,
    }
