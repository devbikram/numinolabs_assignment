from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from models.author import Author
from models.book import Book
from models.borrow import BorrowStatus, Borrowing
from models.category import Category
from models.member import Member
from schemas.dashboard import DashboardStats


def get_dashboard_stats(db: Session) -> DashboardStats:
    # --- Counts (single round-trip with scalar subqueries) ---
    row = db.execute(
        select(
            select(func.count()).select_from(Book).scalar_subquery().label("total_books"),
            select(func.count()).select_from(Member).scalar_subquery().label("total_members"),
            select(func.count()).select_from(Author).scalar_subquery().label("total_authors"),
            select(func.count()).select_from(Category).scalar_subquery().label("total_categories"),
            select(func.coalesce(func.sum(Book.total_copies), 0)).scalar_subquery().label("total_copies"),
            select(func.coalesce(func.sum(Book.available_copies), 0)).scalar_subquery().label("available_copies"),
        )
    ).one()
    total_books = row.total_books
    total_members = row.total_members
    total_authors = row.total_authors
    total_categories = row.total_categories
    total_copies = row.total_copies
    available_copies = row.available_copies

    # --- Borrowing counts by status ---
    status_counts = dict(
        db.execute(
            select(Borrowing.status, func.count(Borrowing.id))
            .group_by(Borrowing.status)
        ).all()
    )
    borrowed_count = status_counts.get(BorrowStatus.borrowed, 0)
    returned_count = status_counts.get(BorrowStatus.returned, 0)
    overdue_count = status_counts.get(BorrowStatus.overdue, 0)
    total_borrowings = borrowed_count + returned_count + overdue_count

    # --- Books per category (top 10) ---
    books_per_category = [
        {"name": name, "count": count}
        for name, count in db.execute(
            select(Category.name, func.count(Book.id))
            .join(Book, Book.category_id == Category.id)
            .group_by(Category.name)
            .order_by(func.count(Book.id).desc())
            .limit(10)
        ).all()
    ]

    # --- Most borrowed books (top 5) ---
    most_borrowed_books = [
        {"title": title, "borrow_count": count}
        for title, count in db.execute(
            select(Book.title, func.count(Borrowing.id))
            .join(Borrowing, Borrowing.book_id == Book.id)
            .group_by(Book.title)
            .order_by(func.count(Borrowing.id).desc())
            .limit(5)
        ).all()
    ]

    # --- Most active members (top 5) ---
    most_active_members = [
        {"name": name, "library_id": lid, "borrow_count": count}
        for name, lid, count in db.execute(
            select(Member.full_name, Member.library_id, func.count(Borrowing.id))
            .join(Borrowing, Borrowing.member_id == Member.id)
            .group_by(Member.full_name, Member.library_id)
            .order_by(func.count(Borrowing.id).desc())
            .limit(5)
        ).all()
    ]

    # --- Recent borrowings (last 5, with eager-loaded relations) ---
    recent_borrowings_rows = list(
        db.scalars(
            select(Borrowing)
            .options(selectinload(Borrowing.book), selectinload(Borrowing.member))
            .order_by(Borrowing.borrowed_at.desc())
            .limit(5)
        )
    )
    recent_borrowings = [
        {
            "id": b.id,
            "book_title": b.book.title if b.book else "[Deleted]",
            "member_name": b.member.full_name if b.member else "[Deleted]",
            "borrowed_at": b.borrowed_at,
            "status": b.status,
        }
        for b in recent_borrowings_rows
    ]

    return DashboardStats(
        total_books=total_books,
        total_members=total_members,
        total_authors=total_authors,
        total_categories=total_categories,
        total_copies=total_copies,
        available_copies=available_copies,
        total_borrowings=total_borrowings,
        borrowed_count=borrowed_count,
        returned_count=returned_count,
        overdue_count=overdue_count,
        books_per_category=books_per_category,
        most_borrowed_books=most_borrowed_books,
        most_active_members=most_active_members,
        recent_borrowings=recent_borrowings,
    )
