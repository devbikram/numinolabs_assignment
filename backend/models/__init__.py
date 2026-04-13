from sqlalchemy import func, select
from sqlalchemy.orm import column_property

from models.author import Author
from models.book import Book, book_authors
from models.borrow import Borrowing
from models.category import Category
from models.member import Member
from models.user import User, UserRole

# Computed column properties (defined here to avoid circular imports)
Book.borrow_count = column_property(
    select(func.count(Borrowing.id))
    .where(Borrowing.book_id == Book.id)
    .correlate_except(Borrowing)
    .scalar_subquery()
)

Author.book_count = column_property(
    select(func.count(book_authors.c.book_id))
    .where(book_authors.c.author_id == Author.id)
    .correlate_except(book_authors)
    .scalar_subquery()
)

__all__ = ["Author", "Book", "book_authors", "Borrowing", "Category", "Member", "User", "UserRole"]
