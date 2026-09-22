from __future__ import annotations

from uuid import UUID

import pytest
from fastapi import HTTPException

from app.db.session import AsyncSessionLocal
from app.services.meal_service import get_flare_safe_meals, get_meal_by_id, get_meals, get_meals_by_tag


@pytest.mark.asyncio
async def test_get_meals_filters_by_meal_type_correctly() -> None:
    async with AsyncSessionLocal() as db:
        meals, total = await get_meals(db, meal_type="breakfast", limit=50)

    assert total >= 20
    assert meals
    assert {meal.meal_type for meal in meals} == {"breakfast"}


@pytest.mark.asyncio
async def test_get_meals_filters_by_is_vegetarian_correctly() -> None:
    async with AsyncSessionLocal() as db:
        meals, total = await get_meals(db, is_vegetarian=True, limit=50)

    assert total >= 30
    assert meals
    assert all(meal.is_vegetarian for meal in meals)


@pytest.mark.asyncio
async def test_get_meals_filters_by_is_flare_friendly_correctly() -> None:
    async with AsyncSessionLocal() as db:
        meals, total = await get_meals(db, is_flare_friendly=True, limit=50)

    assert total >= 15
    assert meals
    assert all(meal.is_flare_friendly for meal in meals)


@pytest.mark.asyncio
async def test_get_meals_respects_limit_and_offset() -> None:
    async with AsyncSessionLocal() as db:
        first_page, total = await get_meals(db, limit=5, offset=0)
        second_page, _ = await get_meals(db, limit=5, offset=5)

    assert total >= 100
    assert len(first_page) == 5
    assert len(second_page) == 5
    assert {meal.id for meal in first_page}.isdisjoint({meal.id for meal in second_page})


@pytest.mark.asyncio
async def test_get_meals_filters_by_q_and_orders_by_name() -> None:
    async with AsyncSessionLocal() as db:
        meals, total = await get_meals(db, q="salad", limit=50)

    assert total == len(meals)
    assert meals
    assert all("salad" in meal.name.lower() for meal in meals)
    assert [meal.name for meal in meals] == sorted(meal.name for meal in meals)


@pytest.mark.asyncio
async def test_get_meal_by_id_returns_meal_with_ingredients() -> None:
    async with AsyncSessionLocal() as db:
        meals, _ = await get_meals(db, limit=1)
        meal = await get_meal_by_id(db, meals[0].id)

    assert meal.id == meals[0].id
    assert meal.ingredients
    assert all(ingredient.food is not None for ingredient in meal.ingredients)


@pytest.mark.asyncio
async def test_get_meal_by_id_raises_404_for_unknown_id() -> None:
    async with AsyncSessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            await get_meal_by_id(db, UUID("00000000-0000-0000-0000-000000000000"))

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_flare_safe_meals_returns_only_flare_meals() -> None:
    async with AsyncSessionLocal() as db:
        meals = await get_flare_safe_meals(db)

    assert len(meals) >= 1
    assert all(meal.is_flare_friendly for meal in meals)


@pytest.mark.asyncio
async def test_get_meals_by_tag_returns_correct_meals() -> None:
    async with AsyncSessionLocal() as db:
        meals, total = await get_meals_by_tag(db, "vegetarian", limit=50)

    assert total >= 30
    assert meals
    assert all("vegetarian" in meal.tags for meal in meals)
