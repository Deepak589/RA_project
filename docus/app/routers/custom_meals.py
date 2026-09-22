from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.custom_meal import (
    CustomMealCalculateRequest,
    CustomMealCreateRequest,
    CustomMealListResponse,
    CustomMealNutrients,
    CustomMealResponse,
)
from app.services.custom_meal_service import (
    calculate_custom_meal,
    create_custom_meal,
    delete_custom_meal,
    get_custom_meal_by_id,
    get_custom_meals,
)

router = APIRouter(prefix="/api/v1/meals/custom", tags=["custom meals"])


@router.post("/calculate", response_model=CustomMealNutrients)
async def calculate_custom_meal_endpoint(
    data: CustomMealCalculateRequest,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> CustomMealNutrients:
    return await calculate_custom_meal(db, data.ingredients)


@router.post("", response_model=CustomMealResponse, status_code=201)
async def create_custom_meal_endpoint(
    data: CustomMealCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> CustomMealResponse:
    return await create_custom_meal(db, UUID(user_id), data)


@router.get("", response_model=CustomMealListResponse)
async def list_custom_meals_endpoint(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> CustomMealListResponse:
    items, total = await get_custom_meals(db, UUID(user_id), limit, offset)
    return CustomMealListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{meal_id}", response_model=CustomMealResponse)
async def get_custom_meal_endpoint(
    meal_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> CustomMealResponse:
    return await get_custom_meal_by_id(db, UUID(user_id), meal_id)


@router.delete("/{meal_id}")
async def delete_custom_meal_endpoint(
    meal_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> dict[str, str]:
    await delete_custom_meal(db, UUID(user_id), meal_id)
    return {"status": "deleted"}
