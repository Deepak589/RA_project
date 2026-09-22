from __future__ import annotations

from app.models.meal import Meal
from app.services.rule_engine import _meal_matches_dietary_flags


def _meal(name: str, *, is_vegetarian: bool = False, tags: list[str] | None = None, dietary_tags: list[str] | None = None) -> Meal:
    return Meal(
        name=name,
        meal_type="lunch",
        is_vegetarian=is_vegetarian,
        tags=tags or [],
        dietary_tags_jsonb=dietary_tags or [],
    )


def test_vegetarian_flag_keeps_vegetarian_meal() -> None:
    meal = _meal("Lentil bowl", is_vegetarian=True)
    assert _meal_matches_dietary_flags(meal, ["vegetarian"]) is True


def test_vegetarian_flag_excludes_non_vegetarian_meal() -> None:
    meal = _meal("Chicken bowl", is_vegetarian=False)
    assert _meal_matches_dietary_flags(meal, ["vegetarian"]) is False


def test_non_vegetarian_flag_keeps_meat_meal() -> None:
    meal = _meal("Chicken bowl", is_vegetarian=False)
    assert _meal_matches_dietary_flags(meal, ["non_vegetarian"]) is True


def test_non_vegetarian_flag_excludes_vegetarian_meal() -> None:
    meal = _meal("Lentil bowl", is_vegetarian=True)
    assert _meal_matches_dietary_flags(meal, ["non_vegetarian"]) is False


def test_non_vegetarian_flag_excludes_vegan_tagged_meal() -> None:
    meal = _meal("Tofu bowl", is_vegetarian=False, tags=["vegan"])
    assert _meal_matches_dietary_flags(meal, ["non_vegetarian"]) is False
