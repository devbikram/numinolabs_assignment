from sqlalchemy import Index, String, Text, column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models.base import TimestampMixin, UUIDMixin


class Author(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "author"
    __table_args__ = (
        Index("author_name_normalized_key", func.lower(func.trim(column("name"))), unique=True),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    books: Mapped[list["Book"]] = relationship(  # noqa: F821
        secondary="book_authors",
        back_populates="authors",
    )
