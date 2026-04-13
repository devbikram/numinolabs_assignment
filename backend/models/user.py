import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from models.base import TimestampMixin, UUIDMixin


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole", native_enum=False),
        nullable=False,
        default=UserRole.manager,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
