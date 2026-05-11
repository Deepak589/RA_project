"""
unseed_curated.py — remove curated foods/meals seeded by seed_curated.py.

Usage:
    python scripts/unseed_curated.py [--dry-run]

FK-safe: skips rows referenced by recommendation_logs, food_logs, or meal_ingredients.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.models.meal import Meal, MealIngredient

FOODS_PATH = PROJECT_ROOT / "scripts" / "data" / "curated_foods.json"
MEALS_PATH = PROJECT_ROOT / "scripts" / "data" / "curated_meals.json"


async def main(dry_run: bool = False) -> None:
    print(f"=== unseed_curated.py {'DRY-RUN ' if dry_run else ''}===")

    foods_data = json.loads(FOODS_PATH.read_text(encoding="utf-8"))
    meals_data = json.loads(MEALS_PATH.read_text(encoding="utf-8"))

    curated_meal_names_lower = {m["name"].lower() for m in meals_data}

    meals_deleted = 0
    meals_blocked = 0
    foods_deleted = 0
    foods_blocked = 0

    async with AsyncSessionLocal() as db:
        async with db.begin():
            # ── Meals ──
            # Find curated meals by name
            stmt = select(Meal).where(
                func.lower(Meal.name).in_(curated_meal_names_lower)
            ).options(selectinload(Meal.recommendation_logs), selectinload(Meal.food_logs))
            result = await db.execute(stmt)
            meals = result.scalars().all()

            for meal in meals:
                has_rec_logs = bool(meal.recommendation_logs)
                has_food_logs = bool(meal.food_logs)
                if has_rec_logs or has_food_logs:
                    print(f"  [BLOCKED MEAL] '{meal.name}' — referenced by "
                          f"rec_logs={len(meal.recommendation_logs)}, "
                          f"food_logs={len(meal.food_logs)}")
                    meals_blocked += 1
                    continue

                if dry_run:
                    print(f"  [DRY-RUN] Would delete meal: {meal.name}")
                else:
                    await db.delete(meal)
                    print(f"  DELETED MEAL: {meal.name}")
                meals_deleted += 1

            if not dry_run:
                await db.flush()

            # ── Foods (manual only) ──
            # Only delete foods with external_source='manual' not referenced by meal_ingredients or food_logs
            stmt = select(Food).where(Food.external_source == "manual").options(
                selectinload(Food.meal_ingredients),
                selectinload(Food.food_logs),
            )
            result = await db.execute(stmt)
            manual_foods = result.scalars().all()

            for food in manual_foods:
                has_meal_ings = bool(food.meal_ingredients)
                has_food_logs = bool(food.food_logs)
                if has_meal_ings or has_food_logs:
                    print(f"  [BLOCKED FOOD] '{food.name}' — still referenced by "
                          f"meal_ingredients={len(food.meal_ingredients)}, "
                          f"food_logs={len(food.food_logs)}")
                    foods_blocked += 1
                    continue

                if dry_run:
                    print(f"  [DRY-RUN] Would delete food: {food.name}")
                else:
                    await db.delete(food)
                    print(f"  DELETED FOOD: {food.name}")
                foods_deleted += 1

            if dry_run:
                await db.rollback()

    print("\n=== SUMMARY ===")
    print(f"Meals: deleted={meals_deleted}, blocked={meals_blocked}")
    print(f"Foods: deleted={foods_deleted}, blocked={foods_blocked}")
    if dry_run:
        print("(DRY-RUN — no changes written)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove curated seed data")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(dry_run=args.dry_run))
