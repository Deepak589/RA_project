from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.meal import Meal
from app.models.recommendation import RecommendationLog
from app.services.nutrition_tracker import DailyNutritionState, NutritionGaps
from app.services.rule_engine import get_next_meal_recommendation


MODULE = "app.services.rule_engine"


def _meal(
    name: str,
    score: str = "6.0",
    is_vegetarian: bool = False,
    dietary_tags: list[str] | None = None,
) -> Meal:
    meal = Meal(
        name=name,
        meal_type="lunch",
        anti_inflammatory_score=Decimal(score),
        is_flare_friendly=False,
        is_vegetarian=is_vegetarian,
        tags=[],
        dietary_tags_jsonb=dietary_tags or [],
        reason_tags_jsonb=[],
        is_curated=True,
    )
    meal.id = uuid.uuid4()
    meal.ingredients = []
    return meal


def _no_gaps() -> NutritionGaps:
    return NutritionGaps(
        protein_gap=0, fiber_gap=0, omega3_gap=0,
        calories_gap=0, sugar_headroom=30, sodium_headroom=1500,
        is_protein_low=False, is_fiber_low=False, is_omega3_low=False,
        is_sugar_over=False, is_sodium_over=False,
    )


def _zero_nutrition() -> DailyNutritionState:
    return DailyNutritionState(0, 0, 0, 0, 0, 0, 0, 0, 0, None, None)


def _make_db_mock() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _no_prefs() -> SimpleNamespace:
    return SimpleNamespace(
        dietary_flags_jsonb=[],
        allergies_jsonb=[],
        goal_flags_jsonb=[],
        cuisine_type=None,
    )


def _prefs_with_flags(flags: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        dietary_flags_jsonb=flags,
        allergies_jsonb=[],
        goal_flags_jsonb=[],
        cuisine_type=None,
    )


async def _call(
    meals: list[Meal],
    preferences: Any = None,
    diet_override: str | None = None,
) -> Any:
    user_id = uuid.uuid4()
    db = _make_db_mock()

    with (
        patch(f"{MODULE}._load_candidate_meals", new=AsyncMock(return_value=meals)),
        patch(f"{MODULE}._load_preferences", new=AsyncMock(return_value=preferences)),
        patch(f"{MODULE}.get_user_medications", new=AsyncMock(return_value=[])),
        patch(f"{MODULE}.get_recommendation_mode", new=AsyncMock(return_value="normal")),
        patch(f"{MODULE}.get_todays_lifestyle", new=AsyncMock(return_value=None)),
        patch(f"{MODULE}.get_todays_nutrition", new=AsyncMock(return_value=_zero_nutrition())),
        patch(f"{MODULE}.get_nutrition_gaps", return_value=_no_gaps()),
        patch(f"{MODULE}._load_recent_recommendation_logs", new=AsyncMock(return_value=[])),
    ):
        result = await get_next_meal_recommendation(
            db, user_id, meal_type="lunch", flare_active=False, diet_override=diet_override
        )
    return result


async def test_D1_non_veg_override_returns_non_veg_meal() -> None:
    """D1: No preference, mixed pool, non_vegetarian override → primary is non-veg."""
    veg_meals = [_meal(f"Veg {i}", score="7.0", is_vegetarian=True) for i in range(3)]
    non_veg_meals = [_meal(f"NonVeg {i}", score="6.0", is_vegetarian=False) for i in range(2)]
    meals = veg_meals + non_veg_meals

    result = await _call(meals, preferences=_no_prefs(), diet_override="non_vegetarian")

    assert result.primary_recommendation.is_vegetarian is False, (
        f"Expected non-veg primary, got: {result.primary_recommendation.name}"
    )


async def test_D2_veg_override_returns_veg_meal() -> None:
    """D2: No preference, mixed pool, vegetarian override → primary is vegetarian."""
    veg_meals = [_meal(f"Veg {i}", score="6.0", is_vegetarian=True) for i in range(3)]
    non_veg_meals = [_meal(f"NonVeg {i}", score="8.0", is_vegetarian=False) for i in range(2)]
    meals = veg_meals + non_veg_meals

    result = await _call(meals, preferences=_no_prefs(), diet_override="vegetarian")

    assert result.primary_recommendation.is_vegetarian is True, (
        f"Expected veg primary, got: {result.primary_recommendation.name}"
    )


async def test_D3_empty_non_veg_pool_falls_back_gracefully() -> None:
    """D3: Only veg meals available, non_vegetarian override → graceful fallback (no 404)."""
    meals = [_meal(f"Veg {i}", score="6.0", is_vegetarian=True) for i in range(4)]

    # After fix: should NOT raise 404, should fall back to full pool
    result = await _call(meals, preferences=_no_prefs(), diet_override="non_vegetarian")
    assert result is not None, "Expected a result (graceful fallback), got None"


async def test_D4_override_ignored_when_real_preference() -> None:
    """D4: User has vegetarian preference, non_vegetarian override → real pref wins, primary is veg."""
    veg_meals = [_meal(f"Veg {i}", score="6.0", is_vegetarian=True) for i in range(3)]
    non_veg_meals = [_meal(f"NonVeg {i}", score="8.0", is_vegetarian=False) for i in range(2)]
    meals = veg_meals + non_veg_meals

    result = await _call(
        meals,
        preferences=_prefs_with_flags(["vegetarian"]),
        diet_override="non_vegetarian",
    )

    assert result.primary_recommendation.is_vegetarian is True, (
        f"Real veg preference should win over override. Got: {result.primary_recommendation.name}"
    )


async def test_D5_invalid_override_silently_ignored() -> None:
    """D5: Invalid diet_override value → ignored, runs normally without crashing."""
    meals = [_meal(f"Meal {i}", score="6.0", is_vegetarian=(i % 2 == 0)) for i in range(5)]

    result = await _call(meals, preferences=_no_prefs(), diet_override="invalid_value")

    assert result is not None
    assert result.primary_recommendation is not None


async def test_D6_mixed_flag_with_no_preference_real_pref_wins() -> None:
    """D6: User has ["vegetarian", "no_preference"] — real pref (veg) should win over override.

    Was broken by bug (c): has_real_preference = bool(active) AND "no_preference" not in flags
    caused real pref to be ignored when no_preference was also present.
    After fix: has_real_preference = bool(active_dietary_flags) — no_preference already stripped.
    """
    veg_meals = [_meal(f"Veg {i}", score="6.0", is_vegetarian=True) for i in range(3)]
    non_veg_meals = [_meal(f"NonVeg {i}", score="8.0", is_vegetarian=False) for i in range(2)]
    meals = veg_meals + non_veg_meals

    result = await _call(
        meals,
        preferences=_prefs_with_flags(["vegetarian", "no_preference"]),
        diet_override="non_vegetarian",
    )

    assert result.primary_recommendation.is_vegetarian is True, (
        f"Mixed flag ['vegetarian','no_preference']: real veg pref should win over non_veg override. "
        f"Got: {result.primary_recommendation.name}"
    )
