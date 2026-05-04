from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.food import Food
from app.models.log import FoodLog
from app.models.meal import CustomMeal, Meal


@dataclass
class UserProfile:
    daily_calories_target: float = 1800
    daily_protein_g_target: float = 60
    daily_fiber_g_target: float = 25
    daily_sugar_g_ceiling: float = 30
    daily_sodium_mg_ceiling: float = 1500
    daily_omega3_g_target: float = 1.1


@dataclass
class DailyNutritionState:
    calories_consumed: float
    protein_consumed: float
    carbs_consumed: float
    fat_consumed: float
    fiber_consumed: float
    sugar_consumed: float
    sodium_consumed: float
    omega3_consumed: float
    meal_count_today: int
    last_meal_type: str | None
    last_meal_time: datetime | None


@dataclass
class NutritionGaps:
    protein_gap: float
    fiber_gap: float
    omega3_gap: float
    calories_gap: float
    sugar_headroom: float
    sodium_headroom: float
    is_protein_low: bool
    is_fiber_low: bool
    is_omega3_low: bool
    is_sugar_over: bool
    is_sodium_over: bool


async def get_todays_nutrition(db: AsyncSession, user_id: UUID) -> DailyNutritionState:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = datetime.combine(now.date(), time.min)
    end = datetime.combine(now.date(), time.max)
    result = await db.scalars(
        select(FoodLog)
        .where(FoodLog.user_id == user_id, FoodLog.logged_at >= start, FoodLog.logged_at <= end)
        .options(
            selectinload(FoodLog.food),
            selectinload(FoodLog.meal),
            selectinload(FoodLog.recommendation_meal),
            selectinload(FoodLog.custom_meal),
        )
        .order_by(FoodLog.logged_at)
    )
    return summarize_food_logs(list(result))


def summarize_food_logs(logs: list[FoodLog]) -> DailyNutritionState:
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0,
        "fiber": 0.0,
        "sugar": 0.0,
        "sodium": 0.0,
        "omega3": 0.0,
    }
    for log in logs:
        nutrients = nutrients_for_log(log)
        for key in totals:
            totals[key] += nutrients[key]

    last = max(logs, key=lambda item: item.logged_at, default=None)
    return DailyNutritionState(
        calories_consumed=round(totals["calories"], 2),
        protein_consumed=round(totals["protein"], 2),
        carbs_consumed=round(totals["carbs"], 2),
        fat_consumed=round(totals["fat"], 2),
        fiber_consumed=round(totals["fiber"], 2),
        sugar_consumed=round(totals["sugar"], 2),
        sodium_consumed=round(totals["sodium"], 2),
        omega3_consumed=round(totals["omega3"], 3),
        meal_count_today=len(logs),
        last_meal_type=last.meal_type if last else None,
        last_meal_time=last.logged_at if last else None,
    )


def get_nutrition_gaps(state: DailyNutritionState, user_profile: UserProfile | None = None) -> NutritionGaps:
    profile = user_profile or UserProfile()
    protein_gap = max(profile.daily_protein_g_target - state.protein_consumed, 0)
    fiber_gap = max(profile.daily_fiber_g_target - state.fiber_consumed, 0)
    omega3_gap = max(profile.daily_omega3_g_target - state.omega3_consumed, 0)
    calories_gap = max(profile.daily_calories_target - state.calories_consumed, 0)
    sugar_headroom = max(profile.daily_sugar_g_ceiling - state.sugar_consumed, 0)
    sodium_headroom = max(profile.daily_sodium_mg_ceiling - state.sodium_consumed, 0)
    return NutritionGaps(
        protein_gap=round(protein_gap, 2),
        fiber_gap=round(fiber_gap, 2),
        omega3_gap=round(omega3_gap, 3),
        calories_gap=round(calories_gap, 2),
        sugar_headroom=round(sugar_headroom, 2),
        sodium_headroom=round(sodium_headroom, 2),
        is_protein_low=protein_gap > 15,
        is_fiber_low=fiber_gap > 8,
        is_omega3_low=omega3_gap > 0.5,
        is_sugar_over=state.sugar_consumed > profile.daily_sugar_g_ceiling,
        is_sodium_over=state.sodium_consumed > profile.daily_sodium_mg_ceiling,
    )


def nutrients_for_log(log: FoodLog) -> dict[str, float]:
    if log.log_source == "curated_recommendation":
        return nutrients_from_meal(log.recommendation_meal or log.meal)
    if log.log_source == "custom_meal":
        return nutrients_from_meal(log.custom_meal)
    if log.meal is not None:
        return nutrients_from_meal(log.meal)
    if log.food is not None:
        return nutrients_from_food(log.food, log.portion_g)
    return {key: 0.0 for key in ("calories", "protein", "carbs", "fat", "fiber", "sugar", "sodium", "omega3")}


def nutrients_from_meal(meal: Meal | CustomMeal | None) -> dict[str, float]:
    return {
        "calories": _float_attr(meal, "total_calories", "calories"),
        "protein": _float_attr(meal, "total_protein_g", "protein_g"),
        "carbs": _float_attr(meal, "total_carbs_g"),
        "fat": _float_attr(meal, "total_fat_g"),
        "fiber": _float_attr(meal, "total_fiber_g", "fiber_g"),
        "sugar": _float_attr(meal, "total_sugar_g", "sugar_g"),
        "sodium": _float_attr(meal, "total_sodium_mg", "sodium_mg"),
        "omega3": _float_attr(meal, "total_omega3_g"),
    }


def nutrients_from_food(food: Food, portion_g: Decimal | None) -> dict[str, float]:
    serving = _decimal(getattr(food, "serving_size_g", None)) or Decimal("100")
    portion = _decimal(portion_g) or serving
    factor = float(portion / serving) if serving else 1.0
    return {
        "calories": _float_attr(food, "calories") * factor,
        "protein": _float_attr(food, "protein_g") * factor,
        "carbs": _float_attr(food, "carbs_g") * factor,
        "fat": _float_attr(food, "fat_g") * factor,
        "fiber": _float_attr(food, "fiber_g") * factor,
        "sugar": _float_attr(food, "sugar_g") * factor,
        "sodium": _float_attr(food, "sodium_mg") * factor,
        "omega3": _float_attr(food, "omega3_g") * factor,
    }


def nutrition_context_json(state: DailyNutritionState) -> dict[str, float]:
    return {
        "calories_consumed": state.calories_consumed,
        "protein_consumed": state.protein_consumed,
        "fiber_consumed": state.fiber_consumed,
        "sugar_consumed": state.sugar_consumed,
        "sodium_consumed": state.sodium_consumed,
    }


def _float_attr(obj: Any, *names: str) -> float:
    if obj is None:
        return 0.0
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return float(value)
    return 0.0


def _decimal(value: Decimal | None) -> Decimal | None:
    return value if value is not None else None
