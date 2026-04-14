from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models.base import TimestampMixin, UUIDMixin


class Member(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "member"

    library_id: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    borrowings: Mapped[list["Borrowing"]] = relationship(  # noqa: F821
        back_populates="member",
        passive_deletes=True,
    )
