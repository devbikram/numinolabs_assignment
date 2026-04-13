import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.security import hash_password
from crud._utils import db_create
from models.user import User, UserRole
from schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_users(db: Session, *, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
    total = db.scalar(select(func.count()).select_from(User))
    users = list(db.scalars(select(User).order_by(User.created_at).offset(skip).limit(limit)))
    return users, total or 0


def create_manager(db: Session, data: UserCreate) -> User:
    """Create a new user with the manager role."""
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole.manager,
        is_active=True,
    )
    return db_create(db, user)


def set_user_active(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
