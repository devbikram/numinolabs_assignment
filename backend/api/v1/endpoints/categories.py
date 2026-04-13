import uuid

from fastapi import APIRouter, Query, Request, status

from api.deps import DBSession, PaginationDep
from api.exceptions import ConflictException, NotFoundException
from core.limiter import limiter
from crud import category as category_crud
from schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from schemas.common import MessageResponse, PaginatedResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
@limiter.limit("20/minute")
def create_category(request: Request, data: CategoryCreate, db: DBSession):
    existing = category_crud.get_category_by_name(db, data.name)
    if existing:
        raise ConflictException(detail=f"Category '{data.name}' already exists")
    return category_crud.create_category(db, data)


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
    categories, total = category_crud.get_categories(
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
    category = category_crud.get_category(db, category_id)
    if not category:
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")
    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update a category",
)
@limiter.limit("20/minute")
def update_category(
    request: Request, category_id: uuid.UUID, data: CategoryUpdate, db: DBSession
):
    category = category_crud.get_category(db, category_id)
    if not category:
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")

    if data.name is not None and data.name != category.name:
        existing = category_crud.get_category_by_name(db, data.name)
        if existing:
            raise ConflictException(detail=f"Category '{data.name}' already exists")

    return category_crud.update_category(db, category, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Delete a category",
)
@limiter.limit("20/minute")
def delete_category(request: Request, category_id: uuid.UUID, db: DBSession):
    category = category_crud.get_category(db, category_id)
    if not category:
        raise NotFoundException(detail=f"Category with id '{category_id}' not found")
    category_crud.delete_category(db, category)
    return MessageResponse(message="Category deleted successfully")
