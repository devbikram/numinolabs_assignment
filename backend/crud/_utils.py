from typing import Any, TypeVar

from sqlalchemy.orm import Session

_T = TypeVar("_T")


def escape_like(value: str) -> str:
    """Escape special characters for SQL LIKE patterns."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def db_create(db: Session, obj: _T) -> _T:
    """Add a new ORM instance, commit, refresh, and return it."""
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def db_update(db: Session, obj: _T, data: Any) -> _T:
    """Apply a Pydantic patch schema to an ORM instance, commit, refresh, and return it."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def db_delete(db: Session, obj) -> None:
    """Delete an ORM instance and commit."""
    db.delete(obj)
    db.commit()
