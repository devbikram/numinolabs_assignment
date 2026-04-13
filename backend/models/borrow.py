import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models.base import TimestampMixin, UUIDMixin


class BorrowStatus(str, enum.Enum):
    borrowed = "borrowed"
    returned = "returned"
    overdue = "overdue"


class Borrowing(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "borrowing"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("book.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("member.id", ondelete="CASCADE"),
        nullable=False,
    )
    borrowed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[BorrowStatus] = mapped_column(
        Enum(BorrowStatus, name="borrow_status"),
        nullable=False,
        default=BorrowStatus.borrowed,
    )

    book: Mapped["Book"] = relationship(back_populates="borrowings")  # noqa: F821
    member: Mapped["Member"] = relationship(back_populates="borrowings")  # noqa: F821
