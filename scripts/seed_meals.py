from __future__ import annotations

import asyncio
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401
from app.db.session import AsyncSessionLocal
from app.models.food import Food, MealItem
from app.models.meal import Meal, MealIngredient
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score
from app.services.food_normalizer import normalize_usda_food
from scripts.ingest_usda_foods import fetch_foods

PROMPT_PATH = PROJECT_ROOT / "prompts" / "week 4 prompt.txt"
INGREDIENT_RE = re.compile(r"([A-Za-z ]+?)\s+(\d+)g")
MEAL_TITLE_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")
ZERO = Decimal("0")

SUPPORT_FOODS = {
    "banana": "banana raw",
    "lemon": "lemon raw",
}

ALIASES = {
    "avocado": ("Avocado",),
    "banana": ("Bananas, raw", "Banana"),
    "blueberries": ("Blueberries, raw",),
    "broccoli": ("Broccoli, raw",),
    "brown rice": ("Rice, brown",),
    "chicken": ("Chicken, broiler or fryers, breast", "cooked"),
    "cod": ("Fish, cod",),
    "eggs": ("Eggs, Grade A, Large, egg whole",),
    "garlic": ("Garlic, raw",),
    "ginger": ("Ginger root, raw", "Spices, ginger"),
    "greek yogurt": ("Yogurt, Greek, plain, nonfat",),
    "herring": ("Fish, herring",),
    "kidney beans": ("kidney", "beans"),
    "lemon": ("Lemons, raw", "Lemon"),
    "lentils": ("Lentils, mature seeds, cooked, boiled, without salt",),
    "mackerel": ("Fish, mackerel",),
    "oats": ("Oats, whole grain, steel cut",),
    "olive oil": ("Oil, olive, extra virgin",),
    "quinoa": ("Flour, quinoa",),
    "salmon": ("Fish, salmon",),
    "sardines": ("Fish, sardine",),
    "spinach": ("Spinach, baby", "Spinach, mature"),
    "sweet potato": ("Sweet potatoes",),
    "trout": ("Fish, trout",),
    "tuna": ("Fish, tuna",),
    "walnuts": ("Nuts, walnuts",),
}


@dataclass(frozen=True)
class IngredientSpec:
    name: str
    portion_g: Decimal


@dataclass(frozen=True)
class MealSpec:
    number: int
    name: str
    meal_type: str
    ingredients: list[IngredientSpec]
    effort_level: str
    prep_time_minutes: int


async def main() -> None:
    specs = parse_meal_specs()
    if len(specs) != 100:
        raise RuntimeError(f"Expected 100 meal specs, found {len(specs)}")

    report: dict[str, Any] = {"started_at": _now_iso(), "meals": [], "missing_ingredients": []}
    async with httpx.AsyncClient(timeout=30) as client:
        async with AsyncSessionLocal() as db:
            await ensure_support_foods(db, client, report)
            foods = (await db.scalars(select(Food).order_by(Food.name))).all()
            lookup = build_lookup(foods)

            await db.execute(delete(MealIngredient))
            await db.execute(delete(MealItem))
            await db.execute(delete(Meal))
            await db.commit()

            for spec in specs:
                resolved = []
                missing = []
                for ingredient in spec.ingredients:
                    food = lookup.get(ingredient.name)
                    if food is None:
                        missing.append(ingredient.name)
                    else:
                        resolved.append((ingredient, food))

                if missing:
                    for ingredient_name in missing:
                        issue = f"[MISSING INGREDIENT: {ingredient_name}] {spec.name}"
                        print(issue)
                        report["missing_ingredients"].append(issue)
                    continue

                meal = build_meal(spec, resolved)
                db.add(meal)
                await db.flush()
                for ingredient, food in resolved:
                    db.add(
                        MealIngredient(
                            meal_id=meal.id,
                            food_id=food.id,
                            portion_g=ingredient.portion_g,
                            cooking_state=food.cooking_state,
                            display_note=food.display_note,
                        )
                    )
                await db.commit()
                print(f"SEEDED: {meal.name} | {meal.meal_type} | score={meal.anti_inflammatory_score}")
                report["meals"].append({"name": meal.name, "meal_type": meal.meal_type, "score": str(meal.anti_inflammatory_score)})

    report["finished_at"] = _now_iso()
    path = save_report(report)
    print(f"Report saved: {path}")
    if len(report["meals"]) != 100:
        raise RuntimeError(f"Expected to seed exactly 100 meals, seeded {len(report['meals'])}")


def parse_meal_specs() -> list[MealSpec]:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    meal_text = text.split("MEAL LIST TO SEED:", 1)[1].split("After seeding verify:", 1)[0]
    lines = meal_text.splitlines()
    specs: list[MealSpec] = []
    current_number: int | None = None
    current_name = ""
    current_lines: list[str] = []

    def flush() -> None:
        if current_number is None:
            return
        joined = " ".join(line.strip() for line in current_lines)
        ingredients = [
            IngredientSpec(name=match.group(1).strip().lower(), portion_g=Decimal(match.group(2)))
            for match in INGREDIENT_RE.finditer(joined)
            if match.group(1).strip().lower() not in {"effort", "prep"}
        ]
        effort_match = re.search(r"effort:\s*(low|medium|high)", joined, re.IGNORECASE)
        prep_match = re.search(r"prep:\s*(\d+)\s*min", joined, re.IGNORECASE)
        specs.append(
            MealSpec(
                number=current_number,
                name=current_name,
                meal_type=meal_type_for_number(current_number),
                ingredients=ingredients,
                effort_level=(effort_match.group(1).lower() if effort_match else default_effort(current_number)),
                prep_time_minutes=int(prep_match.group(1)) if prep_match else default_prep_minutes(current_number),
            )
        )

    for line in lines:
        match = MEAL_TITLE_RE.match(line)
        if match:
            flush()
            current_number = int(match.group(1))
            current_name = match.group(2).strip()
            current_lines = []
        elif current_number is not None:
            current_lines.append(line)
    flush()
    return specs


async def ensure_support_foods(db: Any, client: httpx.AsyncClient, report: dict[str, Any]) -> None:
    for ingredient_name, term in SUPPORT_FOODS.items():
        if await find_food(db, ingredient_name) is not None:
            continue
        foods, data_type = await fetch_foods(client, term, data_type_override="SR Legacy")
        if not foods:
            raise RuntimeError(f"Unable to fetch support food: {ingredient_name}")
        normalized = normalize_usda_food(foods[0])
        normalized.anti_inflammatory_score = calculate_anti_inflammatory_score(normalized)
        food = Food(**normalized.model_dump())
        food.cooking_state = "raw"
        food.conversion_factor = Decimal("1.000")
        db.add(food)
        await db.commit()
        report.setdefault("support_foods", []).append({"ingredient": ingredient_name, "name": food.name, "data_type": data_type})
        print(f"SUPPORT FOOD: inserted {food.name} for {ingredient_name}")


async def find_food(db: Any, ingredient_name: str) -> Food | None:
    pattern = f"%{ingredient_name}%"
    return await db.scalar(select(Food).where(Food.name.ilike(pattern)).limit(1))


def build_lookup(foods: list[Food]) -> dict[str, Food]:
    lookup: dict[str, Food] = {}
    for ingredient_name, patterns in ALIASES.items():
        food = best_match(foods, patterns)
        if food is not None:
            lookup[ingredient_name] = food
    return lookup


def best_match(foods: list[Food], patterns: tuple[str, ...]) -> Food | None:
    lowered_patterns = tuple(pattern.lower() for pattern in patterns)
    for food in foods:
        name = food.name.lower()
        if all(pattern in name for pattern in lowered_patterns):
            return food
    for food in foods:
        name = food.name.lower()
        if any(pattern in name for pattern in lowered_patterns):
            return food
    return None


def build_meal(spec: MealSpec, resolved: list[tuple[IngredientSpec, Food]]) -> Meal:
    totals = calculate_totals(resolved)
    score = calculate_meal_score(resolved)
    tags = build_tags(spec, totals, resolved, score)
    vegetarian = is_vegetarian(resolved)
    flare_friendly = spec.meal_type == "flare_day" or (score >= Decimal("7.0") and (totals["sodium_mg"] or ZERO) < Decimal("700"))
    return Meal(
        name=spec.name,
        description=f"Curated Week 4 {spec.meal_type.replace('_', ' ')} meal.",
        meal_type=spec.meal_type,
        cuisine_type="general",
        prep_time_minutes=spec.prep_time_minutes,
        effort_level=spec.effort_level,
        serving_size_description="1 curated serving",
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
        is_vegetarian=vegetarian,
        is_flare_friendly=flare_friendly,
        tags=tags,
        dietary_tags_jsonb=["vegetarian"] if vegetarian else [],
        reason_tags_jsonb=tags,
        instructions="Prepare ingredients simply with minimal added salt. Portion sizes are listed in grams.",
    )


def calculate_totals(resolved: list[tuple[IngredientSpec, Food]]) -> dict[str, Decimal]:
    fields = ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g", "sugar_g", "sodium_mg", "omega3_g")
    totals = {field: ZERO for field in fields}
    for ingredient, food in resolved:
        multiplier = ingredient.portion_g / Decimal("100")
        for field in fields:
            totals[field] += Decimal(str(getattr(food, field) or ZERO)) * multiplier
    return {field: value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) for field, value in totals.items()}


def calculate_meal_score(resolved: list[tuple[IngredientSpec, Food]]) -> Decimal:
    total_portion = sum((ingredient.portion_g for ingredient, _ in resolved), ZERO)
    if total_portion == ZERO:
        return ZERO
    weighted = sum(
        Decimal(str(food.anti_inflammatory_score or ZERO)) * ingredient.portion_g
        for ingredient, food in resolved
    ) / total_portion
    return weighted.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def build_tags(
    spec: MealSpec,
    totals: dict[str, Decimal],
    resolved: list[tuple[IngredientSpec, Food]],
    score: Decimal,
) -> list[str]:
    tags = [spec.meal_type]
    categories = {str(food.category or "") for _, food in resolved}
    if is_vegetarian(resolved):
        tags.append("vegetarian")
    if spec.meal_type == "flare_day":
        tags.append("flare_friendly")
    if totals["protein_g"] >= Decimal("25"):
        tags.append("high_protein")
    if totals["fiber_g"] >= Decimal("8"):
        tags.append("high_fiber")
    if totals["omega3_g"] >= Decimal("1"):
        tags.append("high_omega3")
    if "fish" in categories:
        tags.append("fish")
    if score >= Decimal("7"):
        tags.append("anti_inflammatory")
    return sorted(set(tags))


def is_vegetarian(resolved: list[tuple[IngredientSpec, Food]]) -> bool:
    animal_keywords = ("chicken", "fish", "salmon", "tuna", "mackerel", "sardine", "cod", "trout", "herring", "anchovies")
    return not any(
        str(food.category or "").lower() == "fish" or any(keyword in food.name.lower() for keyword in animal_keywords)
        for _, food in resolved
    )


def meal_type_for_number(number: int) -> str:
    if number <= 20:
        return "breakfast"
    if number <= 45:
        return "lunch"
    if number <= 70:
        return "dinner"
    if number <= 85:
        return "snack"
    return "flare_day"


def default_effort(number: int) -> str:
    if number <= 20 or 71 <= number <= 100:
        return "low"
    if number <= 45:
        return "medium"
    return "medium"


def default_prep_minutes(number: int) -> int:
    if number <= 20:
        return 10
    if number <= 45:
        return 20
    if number <= 70:
        return 30
    return 5


def save_report(report: dict[str, Any]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"seed_meals_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
