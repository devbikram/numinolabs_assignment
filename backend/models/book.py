import uuid

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models.base import TimestampMixin, UUIDMixin

# Many-to-many association table
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("book.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", ForeignKey("author.id", ondelete="CASCADE"), primary_key=True),
)


class Book(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "book"
    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="total_copies_non_negative"),
        CheckConstraint("available_copies >= 0", name="available_copies_non_negative"),
        CheckConstraint(
            "available_copies <= total_copies",
            name="available_lte_total",
        ),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("category.id", ondelete="SET NULL"), nullable=True, index=True
    )
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    authors: Mapped[list["Author"]] = relationship(  # noqa: F821
        secondary=book_authors,
        back_populates="books",
        lazy="selectin",
    )
    category: Mapped["Category | None"] = relationship(  # noqa: F821
        back_populates="books",
        lazy="selectin",
    )
    borrowings: Mapped[list["Borrowing"]] = relationship(  # noqa: F821
        back_populates="book",
        cascade="all, delete-orphan",
    )
