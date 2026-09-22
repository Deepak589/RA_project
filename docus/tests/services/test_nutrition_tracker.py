from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

from app.services.nutrition_tracker import (
    DailyNutritionState,
    UserProfile,
    get_nutrition_gaps,
    summarize_food_logs,
)


def test_empty_log_returns_all_zeros() -> None:
    state = summarize_food_logs([])

    assert state.calories_consumed == 0
    assert state.protein_consumed == 0
    assert state.meal_count_today == 0
    assert state.last_meal_type is None
    assert state.last_meal_time is None


def test_single_meal_log_returns_correct_sums() -> None:
    meal = SimpleNamespace(
        total_calories=Decimal("420"),
        total_protein_g=Decimal("31"),
        total_carbs_g=Decimal("44"),
        total_fat_g=Decimal("12"),
        total_fiber_g=Decimal("9"),
        total_sugar_g=Decimal("6"),
        total_sodium_mg=Decimal("380"),
        total_omega3_g=Decimal("0.8"),
    )
    log = SimpleNamespace(log_source="curated_recommendation", recommendation_meal=meal, meal=meal, logged_at=datetime.now(UTC), meal_type="lunch")

    state = summarize_food_logs([log])

    assert state.calories_consumed == 420
    assert state.protein_consumed == 31
    assert state.fiber_consumed == 9
    assert state.omega3_consumed == 0.8


def test_multiple_meals_accumulate_correctly() -> None:
    first = SimpleNamespace(
        log_source="manual_log",
        meal=None,
        food=SimpleNamespace(
            serving_size_g=Decimal("100"),
            calories=Decimal("100"),
            protein_g=Decimal("10"),
            carbs_g=Decimal("15"),
            fat_g=Decimal("2"),
            fiber_g=Decimal("4"),
            sugar_g=Decimal("3"),
            sodium_mg=Decimal("120"),
            omega3_g=Decimal("0.1"),
        ),
        portion_g=Decimal("100"),
        logged_at=datetime.now(UTC) - timedelta(hours=2),
        meal_type="breakfast",
    )
    second = SimpleNamespace(
        log_source="manual_log",
        meal=None,
        food=first.food,
        portion_g=Decimal("50"),
        logged_at=datetime.now(UTC),
        meal_type="snack",
    )

    state = summarize_food_logs([first, second])

    assert state.calories_consumed == 150
    assert state.protein_consumed == 15
    assert state.last_meal_type == "snack"
    assert state.last_meal_time == second.logged_at


def test_gaps_calculate_correctly_vs_targets() -> None:
    state = DailyNutritionState(1000, 40, 0, 0, 10, 12, 500, 0.4, 2, "lunch", datetime.now(UTC))

    gaps = get_nutrition_gaps(state, UserProfile())

    assert gaps.calories_gap == 800
    assert gaps.protein_gap == 20
    assert gaps.fiber_gap == 15
    assert gaps.omega3_gap == 0.7
    assert gaps.sugar_headroom == 18
    assert gaps.sodium_headroom == 1000


def test_is_protein_low_triggers_at_correct_threshold() -> None:
    state = DailyNutritionState(0, 44.9, 0, 0, 25, 0, 0, 1.1, 0, None, None)

    assert get_nutrition_gaps(state).is_protein_low is True


def test_is_sugar_over_triggers_when_consumed_over_30g() -> None:
    state = DailyNutritionState(0, 60, 0, 0, 25, 31, 0, 1.1, 0, None, None)

    assert get_nutrition_gaps(state).is_sugar_over is True
