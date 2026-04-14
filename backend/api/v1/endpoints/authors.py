import uuid

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from core.limiter import limiter
from schemas.author import AuthorCreate, AuthorResponse, AuthorStats, AuthorUpdate
from schemas.common import MessageResponse, PaginatedResponse
from services import author as author_service

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.post(
    "/",
    response_model=AuthorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an author",
)
@limiter.limit("20/minute")
def create_author(request: Request, data: AuthorCreate, db: DBSession):
    return author_service.create_author(db, data)


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
    authors, total = author_service.list_authors(
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
    return author_service.get_author(db, author_id)


@router.get(
    "/{author_id}/stats",
    response_model=AuthorStats,
    summary="Get stats for an author's books",
)
@limiter.limit("60/minute")
def get_author_stats(request: Request, author_id: uuid.UUID, db: DBSession):
    return author_service.get_author_stats(db, author_id)


@router.patch(
    "/{author_id}",
    response_model=AuthorResponse,
    summary="Update an author",
)
@limiter.limit("20/minute")
def update_author(
    request: Request, author_id: uuid.UUID, data: AuthorUpdate, db: DBSession
):
    return author_service.update_author(db, author_id, data)


@router.delete(
    "/{author_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete an author",
)
@limiter.limit("20/minute")
def delete_author(request: Request, author_id: uuid.UUID, db: DBSession):
    author_service.delete_author(db, author_id)
    return MessageResponse(message="Author deleted successfully")
