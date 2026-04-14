import uuid

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from core.limiter import limiter
from schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from schemas.common import MessageResponse, PaginatedResponse
from services import category as category_service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
@limiter.limit("20/minute")
def create_category(request: Request, data: CategoryCreate, db: DBSession):
    return category_service.create_category(db, data)


@router.get(
    "/",
    response_model=PaginatedResponse[CategoryResponse],
    summary="List all categories",
)
@limiter.limit("60/minute")
def list_categories(
    request: Request,
    pagination: PaginationDep,
    db: DBSession,
    search: str | None = Query(default=None, max_length=200, description="Filter by name (case-insensitive substring match)"),
):
    categories, total = category_service.list_categories(
        db, skip=pagination.skip, limit=pagination.limit, search=search
    )
    return pagination.paginate(categories, total)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
)
@limiter.limit("60/minute")
def get_category(request: Request, category_id: uuid.UUID, db: DBSession):
    return category_service.get_category(db, category_id)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
)
@limiter.limit("20/minute")
def update_category(
    request: Request, category_id: uuid.UUID, data: CategoryUpdate, db: DBSession
):
    return category_service.update_category(db, category_id, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a category",
)
@limiter.limit("20/minute")
def delete_category(request: Request, category_id: uuid.UUID, db: DBSession):
    category_service.delete_category(db, category_id)
    return MessageResponse(message="Category deleted successfully")
