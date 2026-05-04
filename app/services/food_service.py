from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import Food


async def search_foods(
    db: AsyncSession,
    query: str,
    category: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Food], int]:
    statement = select(Food).where(Food.name.ilike(f"%{query}%"))
    statement = _apply_category_filter(statement, category)
    count_statement = select(func.count()).select_from(statement.subquery())
    total = int(await db.scalar(count_statement) or 0)
    result = await db.scalars(statement.order_by(Food.name).limit(limit).offset(offset))
    return list(result), total


async def get_food_by_id(db: AsyncSession, food_id: UUID) -> Food | None:
    return await db.get(Food, food_id)


async def get_categories(db: AsyncSession) -> list[str]:
    result = await db.scalars(
        select(Food.category)
        .where(Food.category.is_not(None))
        .distinct()
        .order_by(Food.category)
    )
    return [category for category in result if category]


def _apply_category_filter(statement: Select[tuple[Food]], category: str | None) -> Select[tuple[Food]]:
    if category:
        return statement.where(Food.category == category)
    return statement
