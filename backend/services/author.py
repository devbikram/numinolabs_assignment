import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.exceptions import ConflictException, NotFoundException
from crud import author as author_crud
from models.author import Author
from schemas.author import AuthorCreate, AuthorUpdate


def create_author(db: Session, data: AuthorCreate) -> Author:
    if author_crud.author_name_taken(db, data.name):
        raise ConflictException(detail=f"An author named '{data.name}' already exists")
    try:
        return author_crud.create_author(db, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"An author named '{data.name}' already exists")


def list_authors(
    db: Session, *, skip: int = 0, limit: int = 20, search: str | None = None
) -> tuple[list[Author], int]:
    return author_crud.get_authors(db, skip=skip, limit=limit, search=search)


def get_author(db: Session, author_id: uuid.UUID) -> Author:
    author = author_crud.get_author(db, author_id)
    if not author:
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")
    return author


def get_author_stats(db: Session, author_id: uuid.UUID) -> dict:
    get_author(db, author_id)
    return author_crud.get_author_stats(db, author_id)


def update_author(db: Session, author_id: uuid.UUID, data: AuthorUpdate) -> Author:
    author = get_author(db, author_id)
    if data.name is not None and author_crud.author_name_taken(db, data.name, exclude_id=author_id):
        raise ConflictException(detail=f"An author named '{data.name}' already exists")
    try:
        return author_crud.update_author(db, author, data)
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail=f"An author named '{data.name}' already exists")


def delete_author(db: Session, author_id: uuid.UUID) -> None:
    author = get_author(db, author_id)
    author_crud.delete_author(db, author)
