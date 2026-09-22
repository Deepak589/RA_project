from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.food import FoodResponse, FoodSearchResponse
from app.services.food_service import get_categories, get_food_by_id, search_foods

router = APIRouter(prefix="/api/v1/foods", tags=["foods"])


@router.get("/search", response_model=FoodSearchResponse)
async def search_foods_endpoint(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    category: str | None = Query(default=None, max_length=50),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> FoodSearchResponse:
    foods, total = await search_foods(db=db, query=q, category=category, limit=limit, offset=offset)
    return FoodSearchResponse(items=foods, total=total, limit=limit, offset=offset)


@router.get("/categories", response_model=list[str])
async def get_food_categories_endpoint(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> list[str]:
    return await get_categories(db)


@router.get("/{food_id}", response_model=FoodResponse)
async def get_food_endpoint(
    food_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> FoodResponse:
    food = await get_food_by_id(db, food_id)
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food not found")
    return food
