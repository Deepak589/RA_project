from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.meal import Meal
from app.models.recommendation import RecommendationLog
from app.services.nutrition_tracker import DailyNutritionState, NutritionGaps
from app.services.rule_engine import get_next_meal_recommendation


def _meal(
    name: str,
    score: str = "6.0",
    is_flare_friendly: bool = False,
    is_vegetarian: bool = False,
    meal_type: str = "lunch",
) -> Meal:
    meal = Meal(
        name=name,
        meal_type=meal_type,
        anti_inflammatory_score=Decimal(score),
        is_flare_friendly=is_flare_friendly,
        is_vegetarian=is_vegetarian,
        tags=[],
        dietary_tags_jsonb=[],
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


def _make_rec_log(meal_id: uuid.UUID) -> RecommendationLog:
    log = RecommendationLog(
        user_id=uuid.uuid4(),
        meal_id=meal_id,
        recommended_for_meal_type="lunch",
        recommendation_context_jsonb={},
        explanation_text="test",
        feedback_status="pending",
    )
    log.id = uuid.uuid4()
    return log


def _recent_logs_from(picked: list[uuid.UUID], limit: int = 4) -> list[RecommendationLog]:
    """Build recent RecommendationLog list from the tail of picked IDs (most recent first)."""
    tail = picked[-limit:] if len(picked) >= limit else picked[:]
    return [_make_rec_log(mid) for mid in reversed(tail)]


MODULE = "app.services.rule_engine"


async def _call_recommendation(
    meals: list[Meal],
    recent_logs: list[RecommendationLog],
    preferences: Any = None,
    symptom_mode: str = "normal",
    flare_active: bool = False,
) -> Any:
    user_id = uuid.uuid4()
    db = _make_db_mock()

    with (
        patch(f"{MODULE}._load_candidate_meals", new=AsyncMock(return_value=meals)),
        patch(f"{MODULE}._load_preferences", new=AsyncMock(return_value=preferences)),
        patch(f"{MODULE}.get_user_medications", new=AsyncMock(return_value=[])),
        patch(f"{MODULE}.get_recommendation_mode", new=AsyncMock(return_value=symptom_mode)),
        patch(f"{MODULE}.get_todays_lifestyle", new=AsyncMock(return_value=None)),
        patch(f"{MODULE}.get_todays_nutrition", new=AsyncMock(return_value=_zero_nutrition())),
        patch(f"{MODULE}.get_nutrition_gaps", return_value=_no_gaps()),
        patch(f"{MODULE}._load_recent_recommendation_logs", new=AsyncMock(return_value=recent_logs)),
    ):
        result = await get_next_meal_recommendation(db, user_id, meal_type="lunch", flare_active=flare_active)
    return result


async def test_small_pool_no_repeat() -> None:
    """T1: 4 curated lunch meals, no filters, no flare — >=3 distinct primaries after 6 calls."""
    meals = [_meal(f"Meal {i}", score=str(6 + (i % 4) * 0.1)) for i in range(4)]
    picked: list[uuid.UUID] = []

    for _ in range(6):
        result = await _call_recommendation(meals, _recent_logs_from(picked))
        picked.append(result.primary_recommendation.id)

    assert len(set(picked)) >= 3, f"Only {len(set(picked))} distinct meals in 6 picks: {picked}"


async def test_flare_only_no_consecutive_repeats() -> None:
    """T2: 3 flare_friendly + 5 normal lunch meals, flare_active=True — >=2 distinct flare meals in 5 calls.
    Pool is large enough (8 meals total, 3 flare-friendly) that variety penalty should work.
    Uses deterministic shuffle to avoid random flakiness."""
    import app.services.rule_engine as rule_engine_mod

    flare_meals = [_meal(f"Flare {i}", score=str(6.0 + i * 0.5), is_flare_friendly=True) for i in range(3)]
    normal_meals = [_meal(f"Normal {i}", score="4.0") for i in range(5)]
    meals = flare_meals + normal_meals
    picked: list[uuid.UUID] = []

    original_shuffle = rule_engine_mod.random.shuffle
    rule_engine_mod.random.shuffle = lambda items: None
    try:
        for _ in range(5):
            result = await _call_recommendation(meals, _recent_logs_from(picked), symptom_mode="flare_only", flare_active=True)
            picked.append(result.primary_recommendation.id)
            flare_ids = {m.id for m in flare_meals}
            assert result.primary_recommendation.id in flare_ids, (
                f"Non-flare meal picked in flare mode: {result.primary_recommendation.name}"
            )
    finally:
        rule_engine_mod.random.shuffle = original_shuffle

    assert len(set(picked)) >= 2, f"Only {len(set(picked))} distinct flare meals in 5 picks: {picked}"


async def test_vegetarian_filter_loop() -> None:
    """T3: 3 veg + 4 non-veg lunch meals with vegetarian preference — >=2 distinct primaries after 5 calls."""
    from types import SimpleNamespace

    prefs = SimpleNamespace(
        dietary_flags_jsonb=["vegetarian"],
        allergies_jsonb=[],
        goal_flags_jsonb=[],
        cuisine_type=None,
    )

    veg_meals = [_meal(f"Veg {i}", score=str(6.0 + i * 0.1), is_vegetarian=True) for i in range(3)]
    non_veg_meals = [_meal(f"Non-veg {i}", score="8.0") for i in range(4)]
    meals = veg_meals + non_veg_meals
    picked: list[uuid.UUID] = []

    for _ in range(5):
        result = await _call_recommendation(meals, _recent_logs_from(picked), preferences=prefs)
        picked.append(result.primary_recommendation.id)
        assert result.primary_recommendation.id in {m.id for m in veg_meals}, (
            f"Non-veg meal selected despite vegetarian filter: {result.primary_recommendation.name}"
        )

    assert len(set(picked)) >= 2, f"Only {len(set(picked))} distinct veg meals in 5 picks"


async def test_tied_score_jitter() -> None:
    """T4: 5 meals with identical anti_inflammatory_score=7.0 — >=3 distinct primaries after 4 calls."""
    meals = [_meal(f"Tied {i}", score="7.0") for i in range(5)]
    picked: list[uuid.UUID] = []

    for _ in range(4):
        result = await _call_recommendation(meals, _recent_logs_from(picked))
        picked.append(result.primary_recommendation.id)

    assert len(set(picked)) >= 3, f"Only {len(set(picked))} distinct meals in 4 picks (tied scores): {picked}"


async def test_repeat_offender_demoted_on_third_call() -> None:
    """T5: small pool (3 meals), meal_X appears twice in recent logs.
    Bug: eligible_pool<3 triggers full reset → penalties wiped → meal_X (9.0) wins every time.
    Fix: partial reset keeps penalty on repeat offenders → non-offenders get higher priority delta.

    Test is deterministic: random.shuffle is monkeypatched to identity (no shuffle), so the
    priority-bucket order decides the winner. After the fix, meal_X has negative delta (in lower
    bucket) while other meals have delta=0 (higher bucket) → non-meal_X wins deterministically."""
    import app.services.rule_engine as rule_engine_mod

    meal_x = _meal("meal_X", score="9.0")
    other_a = _meal("Other A", score="5.0")
    other_b = _meal("Other B", score="5.0")
    meals = [meal_x, other_a, other_b]

    recent_logs = [
        _make_rec_log(meal_x.id),
        _make_rec_log(meal_x.id),
    ]

    original_shuffle = rule_engine_mod.random.shuffle
    rule_engine_mod.random.shuffle = lambda items: None  # identity — preserve insertion order
    try:
        result = await _call_recommendation(meals, recent_logs)
    finally:
        rule_engine_mod.random.shuffle = original_shuffle

    assert result.primary_recommendation.id != meal_x.id, (
        f"Variety partial-reset failed — meal_X (highest base score) still picked despite "
        f"being a repeat offender in a small pool (pool=3, meal_X in recent x2). "
        f"Got: {result.primary_recommendation.name}"
    )


async def test_healthy_pool_regression() -> None:
    """T6 (regression): 10 meals, no filters — >=4 distinct primaries after 5 calls. Must pass before AND after fix."""
    meals = [_meal(f"Meal {i}", score=str(5.0 + i * 0.2)) for i in range(10)]
    picked: list[uuid.UUID] = []

    for _ in range(5):
        result = await _call_recommendation(meals, _recent_logs_from(picked))
        picked.append(result.primary_recommendation.id)

    assert len(set(picked)) >= 4, f"Only {len(set(picked))} distinct meals in 5 picks (healthy pool): {picked}"


async def test_single_meal_pool_returns_same_meal() -> None:
    """T7: Only 1 meal survives — both calls return that same meal. This is expected, not a bug."""
    only_meal = _meal("Only Meal", score="7.0")
    meals = [only_meal]

    result1 = await _call_recommendation(meals, [])
    logs_after_1 = [_make_rec_log(only_meal.id)]
    result2 = await _call_recommendation(meals, logs_after_1)

    assert result1.primary_recommendation.id == only_meal.id
    assert result2.primary_recommendation.id == only_meal.id
