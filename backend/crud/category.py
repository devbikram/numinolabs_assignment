import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from crud._utils import db_create, db_delete, db_update, escape_like
from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, data: CategoryCreate) -> Category:
    return db_create(db, Category(**data.model_dump()))


def get_category(db: Session, category_id: uuid.UUID) -> Category | None:
    return db.get(Category, category_id)


def get_category_by_name(db: Session, name: str) -> Category | None:
    return db.scalar(select(Category).where(func.lower(Category.name) == name.lower().strip()))


def get_categories(db: Session, *, skip: int = 0, limit: int = 100, search: str | None = None) -> tuple[list[Category], int]:
    query = select(Category)
    count_query = select(func.count()).select_from(Category)

    if search:
        search_filter = Category.name.ilike(f"%{escape_like(search)}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = db.scalar(count_query)
    categories = (
        db.scalars(
            query.order_by(Category.name).offset(skip).limit(limit)
        )
        .all()
    )
    return list(categories), total or 0


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    return db_update(db, category, data)


def delete_category(db: Session, category: Category) -> None:
    db_delete(db, category)
