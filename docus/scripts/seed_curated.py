"""
seed_curated.py — load curated_foods.json and curated_meals.json into the DB.

Usage:
    python scripts/seed_curated.py [--dry-run] [--foods-only] [--meals-only] [--limit N]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from types import SimpleNamespace
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.models.meal import Meal, MealIngredient
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score

FOODS_PATH = PROJECT_ROOT / "scripts" / "data" / "curated_foods.json"
MEALS_PATH = PROJECT_ROOT / "scripts" / "data" / "curated_meals.json"

ZERO = Decimal("0")

VALID_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "flare_day", "any"}
VALID_COOKING_STATES = {"raw", "cooked", "ready_to_eat", "unspecified"}
VALID_EFFORT_LEVELS = {"low", "medium", "high"}

ANIMAL_KEYWORDS = frozenset({
    "chicken", "fish", "salmon", "tuna", "egg", "cod", "tilapia",
    "prawn", "shrimp", "mackerel", "sardine", "trout", "herring",
    "beef", "pork", "lamb", "bone broth", "chicken broth",
})
ANIMAL_CATEGORIES = frozenset({"meat", "fish", "poultry", "meat_poultry"})

FOOD_REQUIRED_FIELDS = {
    "external_source", "external_id", "name", "category",
    "calories", "protein_g", "carbs_g", "fat_g", "saturated_fat_g",
    "fiber_g", "sugar_g", "sodium_mg", "omega3_g", "calcium_mg",
    "vitamin_d_ug", "serving_size_g", "cooking_state",
    "dietary_tags_jsonb", "quality_flag", "manual_override", "needs_review",
}

MEAL_REQUIRED_FIELDS = {
    "name", "meal_type", "cuisine_type", "is_vegetarian", "is_flare_friendly",
    "tags", "dietary_tags_jsonb", "reason_tags_jsonb", "prep_time_minutes",
    "effort_level", "serving_size_description", "instructions", "ingredients",
}


# ──────────────────────────────────────────────
#  Validation helpers
# ──────────────────────────────────────────────

def validate_foods(foods: list[dict]) -> None:
    seen_ids: set[str] = set()
    for i, f in enumerate(foods):
        missing = FOOD_REQUIRED_FIELDS - f.keys()
        if missing:
            raise ValueError(f"Food[{i}] '{f.get('name')}' missing fields: {missing}")
        if f["external_id"] in seen_ids:
            raise ValueError(f"Duplicate external_id: {f['external_id']}")
        seen_ids.add(f["external_id"])
        if f["cooking_state"] not in VALID_COOKING_STATES:
            raise ValueError(f"Food[{i}] invalid cooking_state: {f['cooking_state']!r}")
        for field in ("calories", "protein_g", "carbs_g", "fat_g", "saturated_fat_g",
                      "fiber_g", "sugar_g", "sodium_mg", "omega3_g", "calcium_mg", "vitamin_d_ug"):
            val = f.get(field)
            if val is not None and Decimal(str(val)) < ZERO:
                raise ValueError(f"Food[{i}] '{f['name']}' has negative {field}: {val}")


def validate_meals(meals: list[dict]) -> None:
    seen_names: set[str] = set()
    for i, m in enumerate(meals):
        missing = MEAL_REQUIRED_FIELDS - m.keys()
        if missing:
            raise ValueError(f"Meal[{i}] '{m.get('name')}' missing fields: {missing}")
        if m["meal_type"] not in VALID_MEAL_TYPES:
            raise ValueError(f"Meal[{i}] invalid meal_type: {m['meal_type']!r}")
        low_name = m["name"].lower()
        if low_name in seen_names:
            raise ValueError(f"Duplicate meal name: {m['name']}")
        seen_names.add(low_name)
        if m["prep_time_minutes"] < 0:
            raise ValueError(f"Meal[{i}] '{m['name']}' has negative prep_time_minutes")


# ──────────────────────────────────────────────
#  Lookup helpers
# ──────────────────────────────────────────────

def _food_to_ns(food: Food) -> Any:
    """Convert ORM Food to a namespace so calculate_anti_inflammatory_score works."""
    return SimpleNamespace(
        omega3_g=food.omega3_g,
        fiber_g=food.fiber_g,
        protein_g=food.protein_g,
        calcium_mg=food.calcium_mg,
        sugar_g=food.sugar_g,
        saturated_fat_g=food.saturated_fat_g,
        sodium_mg=food.sodium_mg,
        category=food.category,
    )


def build_food_lookup(foods: list[Food]) -> dict[str, Food]:
    """Case-insensitive substring lookup: food_name → first matching Food."""
    lookup: dict[str, Food] = {}
    for food in foods:
        lookup[food.name.lower()] = food
    return lookup


def resolve_food(name: str, lookup: dict[str, Food], manual_lookup: dict[str, Food]) -> Food | None:
    """Try exact lower match, then substring search, then manual alias.

    Substring matching prefers shorter DB names to avoid false positives where the
    ingredient name appears inside a longer unrelated food name (e.g. 'olive oil'
    matching 'Anchovies, canned in olive oil').
    """
    lower = name.lower()
    # exact
    if lower in lookup:
        return lookup[lower]
    if lower in manual_lookup:
        return manual_lookup[lower]
    # substring: query contained in db_name — prefer shortest match
    combined = {**lookup, **manual_lookup}
    candidates_query_in_db = [(db_name, food) for db_name, food in combined.items() if lower in db_name]
    if candidates_query_in_db:
        # Prefer the DB name where the query takes up the largest fraction (most specific match)
        candidates_query_in_db.sort(key=lambda x: len(x[0]))
        return candidates_query_in_db[0][1]
    # db_name contained in query
    candidates_db_in_query = [(db_name, food) for db_name, food in combined.items() if db_name in lower]
    if candidates_db_in_query:
        candidates_db_in_query.sort(key=lambda x: -len(x[0]))  # prefer longer match
        return candidates_db_in_query[0][1]
    return None


# ──────────────────────────────────────────────
#  Nutrition totals
# ──────────────────────────────────────────────

def calculate_totals(resolved: list[tuple[Decimal, Food]]) -> dict[str, Decimal]:
    fields = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg", "omega3_g")
    totals = {f: ZERO for f in fields}
    for portion_g, food in resolved:
        multiplier = portion_g / Decimal("100")
        for field in fields:
            totals[field] += Decimal(str(getattr(food, field) or ZERO)) * multiplier
    return {f: v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for f, v in totals.items()}


def calculate_meal_score(resolved: list[tuple[Decimal, Food]]) -> Decimal:
    total_portion = sum((p for p, _ in resolved), ZERO)
    if total_portion == ZERO:
        return ZERO
    weighted = sum(
        Decimal(str(food.anti_inflammatory_score or ZERO)) * portion_g
        for portion_g, food in resolved
    ) / total_portion
    return weighted.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


# ──────────────────────────────────────────────
#  Animal-ingredient guard
# ──────────────────────────────────────────────

def _is_animal_food(food: Food) -> bool:
    cat = str(food.category or "").lower()
    if cat in ANIMAL_CATEGORIES:
        return True
    name_lower = food.name.lower()
    for kw in ANIMAL_KEYWORDS:
        if kw in name_lower:
            return True
    return False


def apply_animal_guard(
    meal_dict: dict,
    resolved: list[tuple[Decimal, Food]],
) -> dict:
    """Force is_vegetarian=False and strip veg tags if any animal food detected."""
    animal_foods = [food.name for _, food in resolved if _is_animal_food(food)]
    if not animal_foods:
        return meal_dict

    if meal_dict.get("is_vegetarian"):
        print(f"  [ANIMAL GUARD] '{meal_dict['name']}': animal ingredients detected "
              f"({animal_foods}) — forcing is_vegetarian=False and stripping veg tags")
    meal_dict = dict(meal_dict)
    meal_dict["is_vegetarian"] = False
    for key in ("tags", "dietary_tags_jsonb"):
        meal_dict[key] = [t for t in meal_dict.get(key, []) if t not in ("vegetarian", "vegan")]
    return meal_dict


# ──────────────────────────────────────────────
#  Main seeder
# ──────────────────────────────────────────────

async def seed_foods(
    db: Any,
    foods_data: list[dict],
    dry_run: bool,
) -> dict[str, int]:
    stats = {"inserted": 0, "updated": 0, "skipped": 0}

    for f in foods_data:
        ns = SimpleNamespace(
            omega3_g=f.get("omega3_g", 0),
            fiber_g=f.get("fiber_g", 0),
            protein_g=f.get("protein_g", 0),
            calcium_mg=f.get("calcium_mg", 0),
            sugar_g=f.get("sugar_g", 0),
            saturated_fat_g=f.get("saturated_fat_g", 0),
            sodium_mg=f.get("sodium_mg", 0),
            category=f.get("category", ""),
        )
        ai_score = calculate_anti_inflammatory_score(ns)

        values = {
            "external_source": f["external_source"],
            "external_id": f["external_id"],
            "name": f["name"],
            "category": f.get("category"),
            "serving_size_g": f.get("serving_size_g"),
            "calories": f.get("calories"),
            "protein_g": f.get("protein_g"),
            "carbs_g": f.get("carbs_g"),
            "fat_g": f.get("fat_g"),
            "saturated_fat_g": f.get("saturated_fat_g", 0),
            "fiber_g": f.get("fiber_g"),
            "sugar_g": f.get("sugar_g"),
            "sodium_mg": f.get("sodium_mg"),
            "omega3_g": f.get("omega3_g"),
            "calcium_mg": f.get("calcium_mg", 0),
            "vitamin_d_ug": f.get("vitamin_d_ug", 0),
            "anti_inflammatory_score": ai_score,
            "cooking_state": f.get("cooking_state", "unspecified"),
            "dietary_tags_jsonb": f.get("dietary_tags_jsonb", []),
            "quality_flag": f.get("quality_flag", "manually_verified"),
            "manual_override": f.get("manual_override", True),
            "needs_review": f.get("needs_review", True),
        }

        if dry_run:
            print(f"  [DRY-RUN FOOD] Would upsert: {f['name']} | score={ai_score}")
            stats["inserted"] += 1
            continue

        stmt = pg_insert(Food).values(**values)
        update_cols = {k: v for k, v in values.items() if k not in ("external_source", "external_id")}
        stmt = stmt.on_conflict_do_update(
            index_elements=["external_source", "external_id"],
            set_=update_cols,
        ).returning(text("xmax"))

        result = await db.execute(stmt)
        row = result.fetchone()
        if row and row[0] == 0:
            stats["inserted"] += 1
        else:
            stats["updated"] += 1

    return stats


async def seed_meals(
    db: Any,
    meals_data: list[dict],
    all_foods: list[Food],
    manual_foods: list[Food],
    dry_run: bool,
    limit: int | None,
) -> dict[str, int]:
    stats = {"inserted": 0, "skipped_dup": 0, "skipped_missing_ingredient": 0}

    # build lookups
    lookup = build_food_lookup(all_foods)
    manual_lookup = build_food_lookup(manual_foods)

    # load existing meal names (lower) to skip duplicates
    existing_names: set[str] = set()
    if not dry_run:
        rows = await db.execute(select(func.lower(Meal.name)))
        existing_names = {r[0] for r in rows}

    count = 0
    for m in meals_data:
        if limit is not None and count >= limit:
            break

        low_name = m["name"].lower()
        if low_name in existing_names:
            print(f"  [SKIP DUP] {m['name']}")
            stats["skipped_dup"] += 1
            continue

        # resolve ingredients
        resolved: list[tuple[Decimal, Food]] = []
        missing: list[str] = []
        for ing in m["ingredients"]:
            food = resolve_food(ing["food_name"], lookup, manual_lookup)
            if food is None:
                missing.append(ing["food_name"])
            else:
                resolved.append((Decimal(str(ing["portion_g"])), food))

        if missing:
            print(f"  [MISSING INGREDIENT] '{m['name']}': {missing}")
            stats["skipped_missing_ingredient"] += 1
            continue

        # animal guard
        m = apply_animal_guard(m, resolved)

        # compute nutrition
        totals = calculate_totals(resolved)
        score = calculate_meal_score(resolved)

        # build tags
        tags = list(m.get("tags", []))
        if totals["protein_g"] >= Decimal("25"):
            if "high_protein" not in tags:
                tags.append("high_protein")
        if totals["fiber_g"] >= Decimal("8"):
            if "high_fiber" not in tags:
                tags.append("high_fiber")
        if totals["omega3_g"] >= Decimal("1"):
            if "high_omega3" not in tags:
                tags.append("high_omega3")
        if score >= Decimal("7"):
            if "anti_inflammatory" not in tags:
                tags.append("anti_inflammatory")
        if m["is_flare_friendly"] and "flare_friendly" not in tags:
            tags.append("flare_friendly")

        if dry_run:
            print(f"  [DRY-RUN MEAL] Would insert: {m['name']} | {m['meal_type']} | "
                  f"score={score} | veg={m['is_vegetarian']} | "
                  f"cal={totals['calories']:.0f} | protein={totals['protein_g']:.1f}g")
            stats["inserted"] += 1
            count += 1
            continue

        meal = Meal(
            name=m["name"],
            description=f"Curated manual meal – {m['cuisine_type']} {m['meal_type']}.",
            meal_type=m["meal_type"],
            cuisine_type=m.get("cuisine_type"),
            prep_time_minutes=m.get("prep_time_minutes"),
            effort_level=m.get("effort_level", "medium"),
            serving_size_description=m.get("serving_size_description"),
            total_calories=totals["calories"],
            total_protein_g=totals["protein_g"],
            total_carbs_g=totals["carbs_g"],
            total_fat_g=totals["fat_g"],
            total_fiber_g=totals["fiber_g"],
            total_sugar_g=totals["sugar_g"],
            total_sodium_mg=totals["sodium_mg"],
            total_omega3_g=totals["omega3_g"],
            anti_inflammatory_score=score,
            calories=totals["calories"],
            protein_g=totals["protein_g"],
            fiber_g=totals["fiber_g"],
            sugar_g=totals["sugar_g"],
            sodium_mg=totals["sodium_mg"],
            is_curated=True,
            is_vegetarian=m["is_vegetarian"],
            is_flare_friendly=m["is_flare_friendly"],
            tags=tags,
            dietary_tags_jsonb=m.get("dietary_tags_jsonb", []),
            reason_tags_jsonb=m.get("reason_tags_jsonb", []),
            instructions=m.get("instructions"),
        )
        db.add(meal)
        await db.flush()

        for ing, food in zip(m["ingredients"], [f for _, f in resolved]):
            db.add(MealIngredient(
                meal_id=meal.id,
                food_id=food.id,
                portion_g=Decimal(str(ing["portion_g"])),
                cooking_state=food.cooking_state if food.cooking_state in VALID_COOKING_STATES else "cooked",
            ))

        existing_names.add(low_name)
        stats["inserted"] += 1
        count += 1
        print(f"  SEEDED MEAL: {meal.name} | {meal.meal_type} | score={score}")

    return stats


async def main(
    dry_run: bool = False,
    foods_only: bool = False,
    meals_only: bool = False,
    limit: int | None = None,
) -> None:
    print(f"=== seed_curated.py {'DRY-RUN ' if dry_run else ''}===")

    # Load and validate JSON
    foods_data: list[dict] = json.loads(FOODS_PATH.read_text(encoding="utf-8"))
    meals_data: list[dict] = json.loads(MEALS_PATH.read_text(encoding="utf-8"))

    print(f"Loaded {len(foods_data)} foods, {len(meals_data)} meals from JSON")

    print("Validating foods...")
    validate_foods(foods_data)
    print("Validating meals...")
    validate_meals(meals_data)
    print("Validation passed.")

    async with AsyncSessionLocal() as db:
        async with db.begin():
            food_stats: dict[str, int] = {"inserted": 0, "updated": 0, "skipped": 0}
            meal_stats: dict[str, int] = {"inserted": 0, "skipped_dup": 0, "skipped_missing_ingredient": 0}

            if not meals_only:
                print(f"\n--- Seeding {len(foods_data)} foods ---")
                food_stats = await seed_foods(db, foods_data, dry_run)

            # Reload all foods (including newly inserted) for meal ingredient resolution
            all_foods: list[Food] = []
            manual_foods: list[Food] = []
            if not foods_only:
                if not dry_run:
                    all_foods = list((await db.scalars(select(Food).order_by(Food.name))).all())
                    manual_foods = [f for f in all_foods if f.external_source == "manual"]
                else:
                    # In dry-run, build mock food objects from the JSON for resolution
                    from types import SimpleNamespace as SN
                    for f in foods_data:
                        mock = SN(**{
                            "id": None,
                            "name": f["name"],
                            "external_source": f["external_source"],
                            "external_id": f["external_id"],
                            "category": f.get("category"),
                            "calories": f.get("calories"),
                            "protein_g": f.get("protein_g"),
                            "carbs_g": f.get("carbs_g"),
                            "fat_g": f.get("fat_g"),
                            "fiber_g": f.get("fiber_g"),
                            "sugar_g": f.get("sugar_g"),
                            "sodium_mg": f.get("sodium_mg"),
                            "omega3_g": f.get("omega3_g"),
                            "calcium_mg": f.get("calcium_mg", 0),
                            "vitamin_d_ug": f.get("vitamin_d_ug", 0),
                            "saturated_fat_g": f.get("saturated_fat_g", 0),
                            "anti_inflammatory_score": Decimal("5.0"),
                            "cooking_state": f.get("cooking_state", "unspecified"),
                        })
                        manual_foods.append(mock)
                    # Also load actual DB foods in dry-run for existing ingredient resolution
                    all_foods = list((await db.scalars(select(Food).order_by(Food.name))).all())
                    all_foods = list(all_foods) + list(manual_foods)

                print(f"\n--- Seeding {len(meals_data)} meals ---")
                meal_stats = await seed_meals(db, meals_data, all_foods, manual_foods, dry_run, limit)

            if dry_run:
                # Roll back so nothing is written
                await db.rollback()
            # else: context manager commits on exit from `async with db.begin()`

    print("\n=== SUMMARY ===")
    if not meals_only:
        print(f"Foods: inserted={food_stats['inserted']} updated={food_stats['updated']} skipped={food_stats['skipped']}")
    if not foods_only:
        print(f"Meals: inserted={meal_stats['inserted']} "
              f"skipped_dup={meal_stats['skipped_dup']} "
              f"skipped_missing={meal_stats['skipped_missing_ingredient']}")
    if dry_run:
        print("(DRY-RUN — no changes written)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed curated foods and meals")
    p.add_argument("--dry-run", action="store_true", help="Print plan without writing to DB")
    p.add_argument("--foods-only", action="store_true")
    p.add_argument("--meals-only", action="store_true")
    p.add_argument("--limit", type=int, default=None, help="Max meals to seed")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(
        dry_run=args.dry_run,
        foods_only=args.foods_only,
        meals_only=args.meals_only,
        limit=args.limit,
    ))
