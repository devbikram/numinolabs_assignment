from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from models.base import TimestampMixin, UUIDMixin


class Category(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "category"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    books: Mapped[list["Book"]] = relationship(  # noqa: F821
        back_populates="category",
        lazy="noload",
    )
