import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import ConflictException, NotFoundException
from crud import category as category_crud
from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, data: CategoryCreate) -> Category:
    existing = category_crud.get_category_by_name(db, data.name)
    if existing:
        raise ConflictException(detail=f"Category '{data.name}' already exists")
    return category_crud.create_category(db, data)


def list_categories(
    db: Session, *, skip: int = 0, limit: int = 100, search: str | None = None
) -> tuple[list[Category], int]:
    return category_crud.get_categories(db, skip=skip, limit=limit, search=search)


def get_category(db: Session, category_id: uuid.UUID) -> Category:
    category = category_crud.get_category(db, category_id)
    if not category:
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")
    return category


def update_category(db: Session, category_id: uuid.UUID, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)

    if data.name is not None and data.name != category.name:
        existing = category_crud.get_category_by_name(db, data.name)
        if existing:
            raise ConflictException(detail=f"Category '{data.name}' already exists")

    try:
        return category_crud.update_category(db, category, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"Category '{data.name}' already exists")


def delete_category(db: Session, category_id: uuid.UUID) -> None:
    category = get_category(db, category_id)
    category_crud.delete_category(db, category)
