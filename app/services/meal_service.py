from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import app.db.base  # noqa: F401  # Ensure all relationship targets are registered.
from app.models.meal import Meal, MealIngredient


async def get_meals(
    db: AsyncSession,
    meal_type: str | None = None,
    is_vegetarian: bool | None = None,
    is_flare_friendly: bool | None = None,
    min_score: float | None = None,
    max_calories: int | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
    q: str | None = None,
) -> tuple[list[Meal], int]:
    statement = _apply_meal_filters(
        select(Meal).where(Meal.is_curated.is_(True)),
        meal_type=meal_type,
        is_vegetarian=is_vegetarian,
        is_flare_friendly=is_flare_friendly,
        min_score=min_score,
        max_calories=max_calories,
        tags=tags,
        q=q,
    )
    order_by = (Meal.name,) if q else (Meal.anti_inflammatory_score.desc(), Meal.name)
    count_statement = select(func.count()).select_from(statement.subquery())
    total = int(await db.scalar(count_statement) or 0)
    result = await db.scalars(
        statement.options(selectinload(Meal.ingredients).selectinload(MealIngredient.food))
        .order_by(*order_by)
        .limit(limit)
        .offset(offset)
    )
    return list(result), total


async def get_meal_by_id(db: AsyncSession, meal_id: UUID) -> Meal:
    meal = await db.scalar(
        select(Meal)
        .where(Meal.id == meal_id, Meal.is_curated.is_(True))
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.food))
    )
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found")
    return meal


async def get_flare_safe_meals(db: AsyncSession, limit: int = 10) -> list[Meal]:
    result = await db.scalars(
        select(Meal)
        .where(Meal.is_curated.is_(True), Meal.is_flare_friendly.is_(True))
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.food))
        .order_by(Meal.anti_inflammatory_score.desc(), Meal.name)
        .limit(limit)
    )
    return list(result)


async def get_meals_by_tag(db: AsyncSession, tag: str, limit: int = 20, offset: int = 0) -> tuple[list[Meal], int]:
    statement = select(Meal).where(Meal.is_curated.is_(True), Meal.tags.contains([tag]))
    count_statement = select(func.count()).select_from(statement.subquery())
    total = int(await db.scalar(count_statement) or 0)
    result = await db.scalars(
        statement.options(selectinload(Meal.ingredients).selectinload(MealIngredient.food))
        .order_by(Meal.anti_inflammatory_score.desc(), Meal.name)
        .limit(limit)
        .offset(offset)
    )
    return list(result), total


def _apply_meal_filters(
    statement: Select[tuple[Meal]],
    meal_type: str | None,
    is_vegetarian: bool | None,
    is_flare_friendly: bool | None,
    min_score: float | None,
    max_calories: int | None,
    tags: list[str] | None,
    q: str | None = None,
) -> Select[tuple[Meal]]:
    if meal_type:
        statement = statement.where(Meal.meal_type == meal_type)
    if is_vegetarian is not None:
        statement = statement.where(Meal.is_vegetarian.is_(is_vegetarian))
    if is_flare_friendly is not None:
        statement = statement.where(Meal.is_flare_friendly.is_(is_flare_friendly))
    if min_score is not None:
        statement = statement.where(Meal.anti_inflammatory_score >= min_score)
    if max_calories is not None:
        statement = statement.where(Meal.total_calories <= max_calories)
    for tag in tags or []:
        statement = statement.where(Meal.tags.contains([tag]))
    if q:
        statement = statement.where(Meal.name.ilike(f"%{q}%"))
    return statement
