from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score


def food(**kwargs: object) -> SimpleNamespace:
    defaults = {
        "omega3_g": 0,
        "fiber_g": 0,
        "protein_g": 0,
        "calcium_mg": 0,
        "sugar_g": 0,
        "saturated_fat_g": 0,
        "sodium_mg": 0,
        "category": "other",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_high_scoring_food() -> None:
    score = calculate_anti_inflammatory_score(
        food(omega3_g=1.2, fiber_g=5.5, protein_g=25, calcium_mg=240, category="fish")
    )

    assert score == Decimal("10.0")


def test_penalized_food() -> None:
    score = calculate_anti_inflammatory_score(
        food(sugar_g=25, saturated_fat_g=12, sodium_mg=700, category="other")
    )

    assert score == Decimal("0.5")


def test_zero_values_baseline() -> None:
    assert calculate_anti_inflammatory_score(food()) == Decimal("5.0")


def test_boundary_values() -> None:
    score = calculate_anti_inflammatory_score(
        food(omega3_g=0.3, fiber_g=2.0, sugar_g=10.0, saturated_fat_g=5.0, sodium_mg=300)
    )

    assert score == Decimal("4.5")


def test_low_fiber_tier_adds_half_point() -> None:
    assert calculate_anti_inflammatory_score(food(fiber_g=1.3)) == Decimal("5.5")


def test_below_low_fiber_tier_adds_no_bonus() -> None:
    assert calculate_anti_inflammatory_score(food(fiber_g=0.8)) == Decimal("5.0")


def test_medium_fiber_tier_adds_one_point() -> None:
    assert calculate_anti_inflammatory_score(food(fiber_g=2.0)) == Decimal("6.0")


def test_high_fiber_tier_adds_one_and_half_points() -> None:
    assert calculate_anti_inflammatory_score(food(fiber_g=5.0)) == Decimal("6.5")


def test_clamping() -> None:
    assert calculate_anti_inflammatory_score(food(sugar_g=100, saturated_fat_g=100, sodium_mg=2000)) >= Decimal("0.0")
    assert calculate_anti_inflammatory_score(food(omega3_g=99, fiber_g=99, protein_g=99, calcium_mg=999, category="fish")) <= Decimal("10.0")
