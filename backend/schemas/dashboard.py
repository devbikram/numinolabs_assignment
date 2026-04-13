import uuid
from datetime import datetime

from models.borrow import BorrowStatus
from schemas.base import CustomBaseModel


class CategoryCount(CustomBaseModel):
    name: str
    count: int


class BookBorrowCount(CustomBaseModel):
    title: str
    borrow_count: int


class ActiveMember(CustomBaseModel):
    name: str
    library_id: str
    borrow_count: int


class RecentBorrowing(CustomBaseModel):
    id: uuid.UUID
    book_title: str
    member_name: str
    borrowed_at: datetime
    status: BorrowStatus


class DashboardStats(CustomBaseModel):
    total_books: int
    total_members: int
    total_authors: int
    total_categories: int
    total_copies: int
    available_copies: int
    total_borrowings: int
    borrowed_count: int
    returned_count: int
    overdue_count: int
    books_per_category: list[CategoryCount]
    most_borrowed_books: list[BookBorrowCount]
    most_active_members: list[ActiveMember]
    recent_borrowings: list[RecentBorrowing]
