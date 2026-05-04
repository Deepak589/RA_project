from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.meal import MealResponse, MealSearchResponse
from app.services.meal_service import get_flare_safe_meals, get_meal_by_id, get_meals, get_meals_by_tag

router = APIRouter(prefix="/api/v1/meals", tags=["meals"])


@router.get("/flare-safe", response_model=list[MealResponse])
async def get_flare_safe_meals_endpoint(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> list[MealResponse]:
    return await get_flare_safe_meals(db, limit=10)


@router.get("/by-tag/{tag}", response_model=MealSearchResponse)
async def get_meals_by_tag_endpoint(
    tag: str,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> MealSearchResponse:
    meals, total = await get_meals_by_tag(db=db, tag=tag, limit=limit, offset=offset)
    return MealSearchResponse(items=meals, total=total, limit=limit, offset=offset)


@router.get("/{meal_id}", response_model=MealResponse)
async def get_meal_endpoint(
    meal_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> MealResponse:
    return await get_meal_by_id(db, meal_id)


@router.get("", response_model=MealSearchResponse)
@router.get("/", response_model=MealSearchResponse)
async def get_meals_endpoint(
    meal_type: str | None = Query(default=None),
    is_vegetarian: bool | None = Query(default=None),
    is_flare_friendly: bool | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=10),
    max_calories: int | None = Query(default=None, ge=0),
    tags: str | None = Query(default=None),
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> MealSearchResponse:
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    meals, total = await get_meals(
        db=db,
        meal_type=meal_type,
        is_vegetarian=is_vegetarian,
        is_flare_friendly=is_flare_friendly,
        min_score=min_score,
        max_calories=max_calories,
        tags=tag_list,
        limit=limit,
        offset=offset,
    )
    return MealSearchResponse(items=meals, total=total, limit=limit, offset=offset)
