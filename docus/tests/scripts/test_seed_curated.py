"""
tests/scripts/test_seed_curated.py — unit tests for seed_curated.py logic.

Tests are pure-Python (no DB) where possible. DB-dependent tests use
AsyncSessionLocal and are marked asyncio.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.seed_curated import (
    VALID_MEAL_TYPES,
    apply_animal_guard,
    validate_foods,
    validate_meals,
    calculate_totals,
    calculate_meal_score,
    resolve_food,
    build_food_lookup,
    ANIMAL_CATEGORIES,
    ANIMAL_KEYWORDS,
)


# ─────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────

def _food_ns(name: str, category: str | None = None, **kwargs: Any) -> SimpleNamespace:
    """Build a minimal mock Food-like namespace."""
    defaults = {
        "id": None,
        "name": name,
        "external_source": "manual",
        "external_id": f"manual_{name.lower().replace(' ', '_')}",
        "category": category,
        "calories": 100,
        "protein_g": 10,
        "carbs_g": 10,
        "fat_g": 5,
        "saturated_fat_g": 1,
        "fiber_g": 2,
        "sugar_g": 2,
        "sodium_mg": 50,
        "omega3_g": 0.1,
        "calcium_mg": 50,
        "vitamin_d_ug": 0,
        "anti_inflammatory_score": Decimal("5.0"),
        "cooking_state": "cooked",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_meal_dict(
    name: str = "Test Meal",
    meal_type: str = "lunch",
    is_vegetarian: bool = True,
    tags: list[str] | None = None,
    dietary_tags_jsonb: list[str] | None = None,
    ingredients: list[dict] | None = None,
) -> dict:
    return {
        "name": name,
        "meal_type": meal_type,
        "cuisine_type": "western",
        "is_vegetarian": is_vegetarian,
        "is_flare_friendly": False,
        "tags": tags or ["vegetarian"],
        "dietary_tags_jsonb": dietary_tags_jsonb or ["vegetarian"],
        "reason_tags_jsonb": [],
        "prep_time_minutes": 15,
        "effort_level": "low",
        "serving_size_description": "1 bowl",
        "instructions": "Cook and serve.",
        "ingredients": ingredients or [{"food_name": "spinach", "portion_g": 100}],
    }


def _make_food_dict(**overrides: Any) -> dict:
    base = {
        "external_source": "manual",
        "external_id": "manual_test_food",
        "name": "Test Food",
        "category": "vegetable",
        "serving_size_g": 100,
        "calories": 50,
        "protein_g": 2,
        "carbs_g": 8,
        "fat_g": 0.5,
        "saturated_fat_g": 0.1,
        "fiber_g": 2,
        "sugar_g": 3,
        "sodium_mg": 10,
        "omega3_g": 0.0,
        "calcium_mg": 30,
        "vitamin_d_ug": 0,
        "cooking_state": "raw",
        "dietary_tags_jsonb": ["vegetarian", "vegan"],
        "quality_flag": "manually_verified",
        "manual_override": True,
        "needs_review": True,
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────
#  T1: Loader rejects invalid meal_type
# ─────────────────────────────────────────

def test_validate_meals_rejects_invalid_meal_type() -> None:
    """Meal with invalid meal_type must raise ValueError."""
    bad_meal = _make_meal_dict(meal_type="brunch")  # not in VALID_MEAL_TYPES
    with pytest.raises(ValueError, match="invalid meal_type"):
        validate_meals([bad_meal])


def test_validate_meals_accepts_all_valid_meal_types() -> None:
    """All valid meal_type values must pass validation."""
    meals = [_make_meal_dict(name=f"Meal {mt}", meal_type=mt) for mt in VALID_MEAL_TYPES]
    validate_meals(meals)  # no exception


def test_validate_meals_rejects_missing_required_field() -> None:
    """Meal missing 'instructions' must raise ValueError."""
    bad = _make_meal_dict()
    del bad["instructions"]
    with pytest.raises(ValueError, match="missing fields"):
        validate_meals([bad])


# ─────────────────────────────────────────
#  T2: Loader rejects out-of-range score (foods)
# ─────────────────────────────────────────

def test_validate_foods_rejects_negative_calories() -> None:
    """Food with negative calories must raise ValueError."""
    bad = _make_food_dict(calories=-10)
    with pytest.raises(ValueError, match="negative calories"):
        validate_foods([bad])


def test_validate_foods_rejects_negative_protein() -> None:
    """Food with negative protein_g must raise ValueError."""
    bad = _make_food_dict(protein_g=-5)
    with pytest.raises(ValueError, match="negative protein_g"):
        validate_foods([bad])


def test_validate_foods_rejects_duplicate_external_id() -> None:
    """Two foods sharing the same external_id must raise ValueError."""
    f1 = _make_food_dict()
    f2 = _make_food_dict()  # same external_id
    with pytest.raises(ValueError, match="Duplicate external_id"):
        validate_foods([f1, f2])


def test_validate_foods_rejects_invalid_cooking_state() -> None:
    """Food with cooking_state not in allowed set must raise ValueError."""
    bad = _make_food_dict(cooking_state="frozen")
    with pytest.raises(ValueError, match="invalid cooking_state"):
        validate_foods([bad])


def test_validate_foods_accepts_valid_entry() -> None:
    """A fully valid food entry must pass without error."""
    good = _make_food_dict()
    validate_foods([good])  # no exception


# ─────────────────────────────────────────
#  T3: Animal-ingredient guard flips is_vegetarian
# ─────────────────────────────────────────

def test_animal_guard_flips_is_vegetarian_for_chicken() -> None:
    """Meal marked is_vegetarian=True with chicken ingredient must be flipped to False."""
    chicken = _food_ns("Chicken, broiler breast", category="poultry")
    meal_dict = _make_meal_dict(
        name="Chicken Veggie Bowl",
        is_vegetarian=True,
        tags=["vegetarian", "high_protein"],
        dietary_tags_jsonb=["vegetarian"],
    )
    resolved = [(Decimal("150"), chicken)]
    result = apply_animal_guard(meal_dict, resolved)
    assert result["is_vegetarian"] is False
    assert "vegetarian" not in result["tags"]
    assert "vegetarian" not in result["dietary_tags_jsonb"]


def test_animal_guard_flips_is_vegetarian_for_fish_category() -> None:
    """Meal with a food in 'fish' category must have is_vegetarian flipped."""
    salmon = _food_ns("Fish, salmon", category="fish")
    meal_dict = _make_meal_dict(
        is_vegetarian=True,
        tags=["vegetarian"],
        dietary_tags_jsonb=["vegetarian"],
    )
    resolved = [(Decimal("180"), salmon)]
    result = apply_animal_guard(meal_dict, resolved)
    assert result["is_vegetarian"] is False


def test_animal_guard_does_not_flip_for_dairy() -> None:
    """Dairy foods (category dairy_egg) must NOT trigger the animal guard — dairy is vegetarian."""
    paneer = _food_ns("Paneer", category="dairy_egg")
    meal_dict = _make_meal_dict(
        is_vegetarian=True,
        tags=["vegetarian"],
        dietary_tags_jsonb=["vegetarian"],
    )
    resolved = [(Decimal("100"), paneer)]
    result = apply_animal_guard(meal_dict, resolved)
    assert result["is_vegetarian"] is True, "Dairy foods must not trigger animal guard"


def test_animal_guard_does_not_flip_non_vegetarian_meal() -> None:
    """Already-False is_vegetarian meals must stay False after guard (no error)."""
    chicken = _food_ns("chicken breast", category="poultry")
    meal_dict = _make_meal_dict(is_vegetarian=False, tags=[], dietary_tags_jsonb=[])
    resolved = [(Decimal("150"), chicken)]
    result = apply_animal_guard(meal_dict, resolved)
    assert result["is_vegetarian"] is False


def test_animal_guard_strips_vegan_tag_too() -> None:
    """Both 'vegetarian' and 'vegan' tags must be stripped when animal guard fires."""
    tuna = _food_ns("Fish, tuna", category="fish")
    meal_dict = _make_meal_dict(
        is_vegetarian=True,
        tags=["vegetarian", "vegan", "high_omega3"],
        dietary_tags_jsonb=["vegetarian", "vegan"],
    )
    resolved = [(Decimal("150"), tuna)]
    result = apply_animal_guard(meal_dict, resolved)
    assert "vegetarian" not in result["tags"]
    assert "vegan" not in result["tags"]
    assert "high_omega3" in result["tags"]
    assert "vegetarian" not in result["dietary_tags_jsonb"]
    assert "vegan" not in result["dietary_tags_jsonb"]


# ─────────────────────────────────────────
#  T4: resolve_food avoids false positives
# ─────────────────────────────────────────

def test_resolve_food_prefers_shorter_match_over_long_false_positive() -> None:
    """'olive oil' should NOT resolve to 'Anchovies, canned in olive oil' —
    it should resolve to the shorter 'Oil, olive, extra virgin'."""
    olive_oil_food = _food_ns("Oil, olive, extra virgin", category="fat")
    anchovy_food = _food_ns("Anchovies, canned in olive oil, with salt, drained", category="fish")

    lookup = build_food_lookup([olive_oil_food, anchovy_food])
    result = resolve_food("oil, olive", lookup, {})
    assert result is not None
    assert "anchov" not in result.name.lower(), (
        f"resolve_food('oil, olive') resolved to '{result.name}' — expected olive oil food"
    )


def test_resolve_food_exact_match_wins() -> None:
    """Exact name match must be returned directly."""
    spinach_food = _food_ns("Spinach, baby", category="vegetable")
    lookup = build_food_lookup([spinach_food])
    result = resolve_food("spinach, baby", lookup, {})
    assert result is not None
    assert result.name == "Spinach, baby"


def test_resolve_food_returns_none_for_unknown() -> None:
    """Unknown ingredient name must return None."""
    food = _food_ns("Quinoa flour", category="grain")
    lookup = build_food_lookup([food])
    result = resolve_food("dragonfruit", lookup, {})
    assert result is None


# ─────────────────────────────────────────
#  T5: Nutrition totals calculation
# ─────────────────────────────────────────

def test_calculate_totals_scales_by_portion() -> None:
    """Nutrition totals must scale linearly with portion_g."""
    food = _food_ns("Test veg", calories=200, protein_g=10, carbs_g=20,
                    fat_g=5, fiber_g=4, sugar_g=8, sodium_mg=100, omega3_g=0.5)
    # 50g portion = 50/100 = 0.5x
    resolved = [(Decimal("50"), food)]
    totals = calculate_totals(resolved)
    assert totals["calories"] == Decimal("100.00")
    assert totals["protein_g"] == Decimal("5.00")
    assert totals["fiber_g"] == Decimal("2.00")


def test_calculate_totals_sums_multiple_ingredients() -> None:
    """Totals must add up across multiple ingredients."""
    f1 = _food_ns("Food A", calories=100, protein_g=10, carbs_g=5,
                  fat_g=2, fiber_g=3, sugar_g=2, sodium_mg=50, omega3_g=0.1)
    f2 = _food_ns("Food B", calories=200, protein_g=20, carbs_g=10,
                  fat_g=4, fiber_g=6, sugar_g=4, sodium_mg=100, omega3_g=0.2)
    resolved = [(Decimal("100"), f1), (Decimal("100"), f2)]
    totals = calculate_totals(resolved)
    assert totals["calories"] == Decimal("300.00")
    assert totals["protein_g"] == Decimal("30.00")


# ─────────────────────────────────────────
#  T6: Meal AI score calculation
# ─────────────────────────────────────────

def test_calculate_meal_score_weighted_average() -> None:
    """Meal score must be weighted average of ingredient scores by portion."""
    f1 = _food_ns("High score food", anti_inflammatory_score=Decimal("8.0"))
    f2 = _food_ns("Low score food", anti_inflammatory_score=Decimal("4.0"))
    # 100g of 8.0 + 100g of 4.0 → weighted avg = (800 + 400) / 200 = 6.0
    resolved = [(Decimal("100"), f1), (Decimal("100"), f2)]
    score = calculate_meal_score(resolved)
    assert score == Decimal("6.0")


def test_calculate_meal_score_zero_for_empty_resolved() -> None:
    """Empty resolved list must yield score of 0."""
    score = calculate_meal_score([])
    assert score == Decimal("0")


# ─────────────────────────────────────────
#  T7: JSON data files are valid
# ─────────────────────────────────────────

def test_curated_foods_json_is_valid() -> None:
    """curated_foods.json must parse and pass schema validation."""
    path = PROJECT_ROOT / "scripts" / "data" / "curated_foods.json"
    assert path.exists(), "curated_foods.json must exist"
    foods = json.loads(path.read_text(encoding="utf-8"))
    assert len(foods) >= 40, f"Expected >=40 foods, got {len(foods)}"
    validate_foods(foods)  # no exception


def test_curated_meals_json_is_valid() -> None:
    """curated_meals.json must parse and pass schema validation."""
    path = PROJECT_ROOT / "scripts" / "data" / "curated_meals.json"
    assert path.exists(), "curated_meals.json must exist"
    meals = json.loads(path.read_text(encoding="utf-8"))
    assert len(meals) >= 90, f"Expected >=90 meals, got {len(meals)}"
    validate_meals(meals)  # no exception


def test_curated_meals_has_all_required_types() -> None:
    """curated_meals.json must include all 5 meal_types."""
    path = PROJECT_ROOT / "scripts" / "data" / "curated_meals.json"
    meals = json.loads(path.read_text(encoding="utf-8"))
    types_present = {m["meal_type"] for m in meals}
    for mt in ("breakfast", "lunch", "dinner", "snack", "flare_day"):
        assert mt in types_present, f"Missing meal_type: {mt}"


# ─────────────────────────────────────────
#  T8: DB integration — idempotent run
# ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_curated_idempotent() -> None:
    """Running seed_curated twice must not double-insert foods or meals.

    Foods: upserted on (external_source, external_id) → count stays same.
    Meals: duplicate LOWER(name) check → skipped on second run.
    """
    import app.db.base  # noqa: F401
    from sqlalchemy import func, select, text
    from app.db.session import AsyncSessionLocal
    from app.models.food import Food
    from app.models.meal import Meal
    from scripts.seed_curated import main as seed_main

    async with AsyncSessionLocal() as db:
        food_count_before = await db.scalar(select(func.count()).select_from(Food))
        meal_count_before = await db.scalar(select(func.count()).select_from(Meal))

    # Run seed again (dry_run=False, but it should skip all due to upsert/dedup)
    await seed_main(dry_run=False, foods_only=False, meals_only=False)

    async with AsyncSessionLocal() as db:
        food_count_after = await db.scalar(select(func.count()).select_from(Food))
        meal_count_after = await db.scalar(select(func.count()).select_from(Meal))

    assert food_count_after == food_count_before, (
        f"Food count changed on second run: {food_count_before} → {food_count_after}"
    )
    assert meal_count_after == meal_count_before, (
        f"Meal count changed on second run: {meal_count_before} → {meal_count_after}"
    )
