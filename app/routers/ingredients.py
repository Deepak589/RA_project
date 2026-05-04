from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin_user, require_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.ingredient import (
    IngredientSearchRequest,
    IngredientSearchResult,
    MissingIngredientAdminUpdate,
    MissingIngredientCreate,
    MissingIngredientCreateResponse,
    MissingIngredientListResponse,
    MissingIngredientResponse,
)
from app.services.ingredient_service import (
    create_missing_ingredient,
    get_missing_ingredients,
    search_or_flag_ingredient,
    update_missing_ingredient,
)

router = APIRouter(prefix="/api/v1/ingredients", tags=["ingredients"])


@router.post("/search", response_model=IngredientSearchResult)
async def search_ingredient(
    data: IngredientSearchRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_current_user),
) -> IngredientSearchResult:
    submitted = data.submitted_values
    if submitted is not None:
        submitted.ingredient_name = data.ingredient_name
    return await search_or_flag_ingredient(db, current_user.id, data.ingredient_name, submitted)


@router.post("/missing", response_model=MissingIngredientCreateResponse)
async def create_missing(
    data: MissingIngredientCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_current_user),
) -> MissingIngredientCreateResponse:
    record = await create_missing_ingredient(db, current_user.id, data)
    message = (
        "Thanks. We will verify and add this ingredient shortly."
        if record.status == "user_entered"
        else "Added to our review list. We will include it soon."
    )
    return MissingIngredientCreateResponse(status=record.status, message=message, reported_count=record.reported_count)


@router.get("/missing", response_model=MissingIngredientListResponse)
async def list_missing(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin_user),
) -> MissingIngredientListResponse:
    items, total = await get_missing_ingredients(db, status_filter, limit, offset)
    return MissingIngredientListResponse(items=items, total=total, limit=limit, offset=offset)


@router.patch("/missing/{ingredient_id}", response_model=MissingIngredientResponse)
async def patch_missing(
    ingredient_id: UUID,
    data: MissingIngredientAdminUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin_user),
) -> MissingIngredientResponse:
    record = await update_missing_ingredient(
        db, ingredient_id, data.status, data.admin_notes, data.food_id, current_user.email
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing ingredient not found")
    return record
