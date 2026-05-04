from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.food import Food
from app.models.meal import CustomMeal, CustomMealIngredient
from app.schemas.custom_meal import (
    CustomMealCreateRequest,
    CustomMealIngredientInput,
    CustomMealIngredientResponse,
    CustomMealNutrients,
    CustomMealResponse,
)
from app.schemas.ingredient import MissingIngredientCreate
from app.services.ingredient_service import create_missing_ingredient


MEAT_WORDS = {"chicken", "beef", "pork", "turkey", "lamb", "fish", "salmon", "tuna", "shrimp", "cod"}
HARD_RAW_WORDS = {"raw carrot", "carrot", "celery", "radish"}


async def calculate_custom_meal(db: AsyncSession, ingredients: list[CustomMealIngredientInput]) -> CustomMealNutrients:
    foods_by_id = await _load_foods(db, [item.food_id for item in ingredients])
    totals = {key: Decimal("0") for key in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg", "omega3_g")}
    weighted_score = Decimal("0")
    scored_portion = Decimal("0")
    total_portion = Decimal("0")
    missing: list[str] = []
    seen_foods: list[Food] = []

    for item in ingredients:
        food = foods_by_id.get(item.food_id)
        if food is None:
            missing.append(str(item.food_id))
            continue
        seen_foods.append(food)
        portion = Decimal(item.portion_g)
        total_portion += portion
        factor = portion / Decimal("100")
        totals["calories"] += (food.calories or 0) * factor
        totals["protein_g"] += (food.protein_g or 0) * factor
        totals["carbs_g"] += (food.carbs_g or 0) * factor
        totals["fat_g"] += (food.fat_g or 0) * factor
        totals["fiber_g"] += (food.fiber_g or 0) * factor
        totals["sugar_g"] += (food.sugar_g or 0) * factor
        totals["sodium_mg"] += (food.sodium_mg or 0) * factor
        totals["omega3_g"] += (food.omega3_g or 0) * factor
        weighted_score += (food.anti_inflammatory_score or 0) * portion
        scored_portion += portion

    score = float(weighted_score / scored_portion) if scored_portion else 0.0
    is_vegetarian = _is_vegetarian(seen_foods)
    tags = _build_tags(totals, score, is_vegetarian)
    return CustomMealNutrients(
        total_calories=round(float(totals["calories"]), 2),
        total_protein_g=round(float(totals["protein_g"]), 2),
        total_carbs_g=round(float(totals["carbs_g"]), 2),
        total_fat_g=round(float(totals["fat_g"]), 2),
        total_fiber_g=round(float(totals["fiber_g"]), 2),
        total_sugar_g=round(float(totals["sugar_g"]), 2),
        total_sodium_mg=round(float(totals["sodium_mg"]), 2),
        total_omega3_g=round(float(totals["omega3_g"]), 3),
        anti_inflammatory_score=round(score, 1),
        is_vegetarian=is_vegetarian,
        is_flare_friendly=score >= 6.0 and _easy_foods(seen_foods),
        tags=tags,
        missing_ingredients=missing,
        score_note=f"Score excludes {len(missing)} ingredient not yet in our database" if missing else None,
    )


async def create_custom_meal(db: AsyncSession, user_id: UUID, data: CustomMealCreateRequest) -> CustomMealResponse:
    nutrients = await calculate_custom_meal(db, data.ingredients)
    meal = CustomMeal(
        user_id=user_id,
        name=data.name,
        meal_type=data.meal_type,
        total_calories=Decimal(str(nutrients.total_calories)),
        total_protein_g=Decimal(str(nutrients.total_protein_g)),
        total_carbs_g=Decimal(str(nutrients.total_carbs_g)),
        total_fat_g=Decimal(str(nutrients.total_fat_g)),
        total_fiber_g=Decimal(str(nutrients.total_fiber_g)),
        total_sugar_g=Decimal(str(nutrients.total_sugar_g)),
        total_sodium_mg=Decimal(str(nutrients.total_sodium_mg)),
        total_omega3_g=Decimal(str(nutrients.total_omega3_g)),
        anti_inflammatory_score=Decimal(str(nutrients.anti_inflammatory_score)),
        is_vegetarian=nutrients.is_vegetarian,
        is_flare_friendly=nutrients.is_flare_friendly,
        tags=nutrients.tags,
    )
    db.add(meal)
    await db.flush()
    foods_by_id = await _load_foods(db, [item.food_id for item in data.ingredients])
    for item in data.ingredients:
        food = foods_by_id.get(item.food_id)
        if food is None:
            continue
        db.add(
            CustomMealIngredient(
                custom_meal_id=meal.id,
                food_id=food.id,
                portion_g=item.portion_g,
                cooking_state=item.cooking_state,
                display_note=food.display_note,
            )
        )
    for name in data.missing_ingredient_names:
        await create_missing_ingredient(db, user_id, MissingIngredientCreate(ingredient_name=name))
    await db.commit()
    loaded = await _load_custom_meal(db, user_id, meal.id)
    if loaded is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom meal not found")
    return _response(loaded)


async def get_custom_meals(db: AsyncSession, user_id: UUID, limit: int, offset: int) -> tuple[list[CustomMealResponse], int]:
    statement = select(CustomMeal).where(CustomMeal.user_id == user_id)
    total = int(await db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    result = await db.scalars(
        statement.options(selectinload(CustomMeal.ingredients).selectinload(CustomMealIngredient.food))
        .order_by(CustomMeal.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_response(item) for item in result], total


async def get_custom_meal_by_id(db: AsyncSession, user_id: UUID, meal_id: UUID) -> CustomMealResponse:
    meal = await _load_custom_meal(db, user_id, meal_id)
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom meal not found")
    return _response(meal)


async def delete_custom_meal(db: AsyncSession, user_id: UUID, meal_id: UUID) -> None:
    meal = await db.get(CustomMeal, meal_id)
    if meal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom meal not found")
    if meal.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Custom meal belongs to another user")
    await db.delete(meal)
    await db.commit()


async def _load_foods(db: AsyncSession, food_ids: list[UUID]) -> dict[UUID, Food]:
    if not food_ids:
        return {}
    result = await db.scalars(select(Food).where(Food.id.in_(food_ids)))
    return {food.id: food for food in result}


async def _load_custom_meal(db: AsyncSession, user_id: UUID, meal_id: UUID) -> CustomMeal | None:
    return await db.scalar(
        select(CustomMeal)
        .where(CustomMeal.id == meal_id, CustomMeal.user_id == user_id)
        .options(selectinload(CustomMeal.ingredients).selectinload(CustomMealIngredient.food))
    )


def _response(meal: CustomMeal) -> CustomMealResponse:
    ingredients = []
    for item in meal.ingredients:
        factor = Decimal(item.portion_g or 0) / Decimal("100")
        ingredients.append(
            CustomMealIngredientResponse(
                food_id=item.food_id,
                food_name=item.food.name if item.food else "",
                portion_g=item.portion_g or Decimal("0"),
                cooking_state=item.cooking_state or "cooked",
                display_note=item.display_note,
                calories_contribution=round(float((item.food.calories or 0) * factor), 2) if item.food else 0.0,
                protein_contribution=round(float((item.food.protein_g or 0) * factor), 2) if item.food else 0.0,
            )
        )
    return CustomMealResponse(
        id=meal.id,
        user_id=meal.user_id,
        name=meal.name,
        meal_type=meal.meal_type,
        total_calories=meal.total_calories,
        total_protein_g=meal.total_protein_g,
        total_carbs_g=meal.total_carbs_g,
        total_fat_g=meal.total_fat_g,
        total_fiber_g=meal.total_fiber_g,
        total_sugar_g=meal.total_sugar_g,
        total_sodium_mg=meal.total_sodium_mg,
        total_omega3_g=meal.total_omega3_g,
        anti_inflammatory_score=meal.anti_inflammatory_score,
        is_vegetarian=meal.is_vegetarian,
        is_flare_friendly=meal.is_flare_friendly,
        tags=meal.tags or [],
        ingredients=ingredients,
        created_at=meal.created_at,
    )


def _is_vegetarian(foods: list[Food]) -> bool:
    for food in foods:
        haystack = f"{food.name} {food.category or ''}".lower()
        if any(word in haystack for word in MEAT_WORDS):
            return False
    return True


def _easy_foods(foods: list[Food]) -> bool:
    for food in foods:
        name = food.name.lower()
        if any(word in name for word in HARD_RAW_WORDS):
            return False
    return True


def _build_tags(totals: dict[str, Decimal], score: float, is_vegetarian: bool) -> list[str]:
    tags: list[str] = []
    if is_vegetarian:
        tags.append("vegetarian")
    if totals["protein_g"] >= 25:
        tags.append("high_protein")
    if totals["fiber_g"] >= 8:
        tags.append("high_fiber")
    if score >= 6:
        tags.append("anti_inflammatory")
    return tags
