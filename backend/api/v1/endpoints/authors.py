import uuid

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from api.exceptions import ConflictException, NotFoundException
from core.limiter import limiter
from crud import author as author_crud
from schemas.author import AuthorCreate, AuthorResponse, AuthorStats, AuthorUpdate
from schemas.common import MessageResponse, PaginatedResponse

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.post(
    "/",
    response_model=AuthorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an author",
)
@limiter.limit("20/minute")
def create_author(request: Request, data: AuthorCreate, db: DBSession):
    if author_crud.author_name_taken(db, data.name):
        raise ConflictException(detail=f"An author named '{data.name}' already exists")
    author = author_crud.create_author(db, data)
    return author


@router.get(
    "/",
    response_model=PaginatedResponse[AuthorResponse],
    summary="List all authors",
)
@limiter.limit("60/minute")
def list_authors(
    request: Request,
    pagination: PaginationDep,
    db: DBSession,
    search: str | None = Query(default=None, max_length=200, description="Search by author name (case-insensitive substring)"),
):
    authors, total = author_crud.get_authors(
        db, skip=pagination.skip, limit=pagination.limit, search=search
    )
    return pagination.paginate(authors, total)


@router.get(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Get an author by ID",
)
@limiter.limit("60/minute")
def get_author(request: Request, author_id: uuid.UUID, db: DBSession):
    author = author_crud.get_author(db, author_id)
    if not author:
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")
    return author


@router.get(
    "/{author_id}/stats",
    response_model=AuthorStats,
    summary="Get stats for an author's books",
)
@limiter.limit("60/minute")
def get_author_stats(request: Request, author_id: uuid.UUID, db: DBSession):
    author = author_crud.get_author(db, author_id)
    if not author:
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")
    return author_crud.get_author_stats(db, author_id)


@router.patch(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Update an author",
)
@limiter.limit("20/minute")
def update_author(
    request: Request, author_id: uuid.UUID, data: AuthorUpdate, db: DBSession
):
    author = author_crud.get_author(db, author_id)
    if not author:
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")
    if data.name is not None and author_crud.author_name_taken(db, data.name, exclude_id=author_id):
        raise ConflictException(detail=f"An author named '{data.name}' already exists")
    return author_crud.update_author(db, author, data)


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete an author",
)
@limiter.limit("20/minute")
def delete_author(request: Request, author_id: uuid.UUID, db: DBSession):
    author = author_crud.get_author(db, author_id)
    if not author:
        raise NotFoundException(detail=f"Author with id '{author_id}' not found")
    author_crud.delete_author(db, author)
    return MessageResponse(message="Author deleted successfully")
