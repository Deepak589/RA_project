from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.security import create_access_token, create_refresh_token, decode_token, hash_token
from app.models.food import Food
from app.models.meal import Meal
from app.schemas.custom_meal import CustomMealIngredientInput
from app.schemas.ingredient import MissingIngredientCreate
from app.schemas.user import ChangePasswordRequest, RegisterRequest
from app.services.custom_meal_service import _build_tags, _easy_foods, _is_vegetarian
from app.services.rule_engine import RecommendationResult, _final_rank, result_context
from app.services.nutrition_tracker import DailyNutritionState, NutritionGaps


def _meal(name: str, score: str, flare: bool) -> Meal:
    return Meal(name=name, meal_type="lunch", anti_inflammatory_score=Decimal(score), is_flare_friendly=flare, tags=[])


def _food(name: str, category: str | None = None) -> Food:
    return Food(external_id=str(uuid4()), name=name, category=category, anti_inflammatory_score=Decimal("6.0"))


def test_access_token_decodes_subject_and_type() -> None:
    token = create_access_token("user-1")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "access"


def test_refresh_token_decodes_subject_and_type() -> None:
    token = create_refresh_token("user-1")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["type"] == "refresh"


def test_decode_invalid_token_raises_value_error() -> None:
    with pytest.raises(ValueError):
        decode_token("not-a-token")


def test_hash_token_is_deterministic() -> None:
    assert hash_token("abc") == hash_token("abc")


def test_hash_token_does_not_return_plain_token() -> None:
    assert hash_token("abc") != "abc"


def test_register_request_accepts_name_field() -> None:
    data = RegisterRequest(email="person@example.com", password="password123", name="Person")
    assert data.name == "Person"


def test_register_request_rejects_weak_password() -> None:
    with pytest.raises(ValueError):
        RegisterRequest(email="person@example.com", password="short", name="Person")


def test_change_password_request_requires_strong_new_password() -> None:
    with pytest.raises(ValueError):
        ChangePasswordRequest(current_password="password123", new_password="short")


def test_custom_meal_ingredient_defaults_to_cooked() -> None:
    item = CustomMealIngredientInput(food_id=uuid4(), portion_g=Decimal("50"))
    assert item.cooking_state == "cooked"


def test_custom_meal_ingredient_requires_positive_portion() -> None:
    with pytest.raises(ValueError):
        CustomMealIngredientInput(food_id=uuid4(), portion_g=Decimal("0"))


def test_missing_ingredient_create_accepts_name_only() -> None:
    data = MissingIngredientCreate(ingredient_name="dragonfruit")
    assert data.ingredient_name == "dragonfruit"
    assert data.submitted_calories is None


def test_missing_ingredient_create_accepts_submitted_values() -> None:
    data = MissingIngredientCreate(ingredient_name="papaya", submitted_calories=Decimal("43"))
    assert data.submitted_calories == Decimal("43")


def test_normal_rank_orders_by_score() -> None:
    ranked = _final_rank([_meal("b", "4.0", False), _meal("a", "8.0", False)], "normal")
    assert [meal.name for meal in ranked] == ["a", "b"]


def test_flare_only_rank_places_flare_meals_first() -> None:
    ranked = _final_rank([_meal("normal", "9.0", False), _meal("flare", "6.0", True)], "flare_only")
    assert ranked[0].is_flare_friendly is True


def test_mixed_rank_places_two_flare_first_then_normal() -> None:
    meals = [
        _meal("normal 1", "9.0", False),
        _meal("normal 2", "8.0", False),
        _meal("flare 1", "7.0", True),
        _meal("flare 2", "6.0", True),
        _meal("flare 3", "5.0", True),
    ]
    ranked = _final_rank(meals, "mixed")
    assert [meal.is_flare_friendly for meal in ranked[:3]] == [True, True, False]


def test_mixed_rank_keeps_extra_flare_after_top_five_pattern() -> None:
    meals = [_meal(f"flare {i}", str(9 - i), True) for i in range(3)] + [_meal("normal", "8", False)]
    ranked = _final_rank(meals, "mixed")
    assert ranked[3].is_flare_friendly is True


def test_result_context_includes_recommendation_mode() -> None:
    result = RecommendationResult(
        primary_recommendation=_meal("primary", "7", True),
        alternatives=[],
        explanation="ok",
        rule_applied="flare",
        flare_mode_active=True,
        recommendation_mode="flare_only",
        nutrition_context=DailyNutritionState(0, 0, 0, 0, 0, 0, 0, 0, 0, None, None),
        gaps=NutritionGaps(0, 0, 0, 0, 0, 0, False, False, False, False, False),
        recommendation_log_id=None,
    )
    assert result_context(result)["recommendation_mode"] == "flare_only"


def test_is_vegetarian_true_for_plant_foods() -> None:
    assert _is_vegetarian([_food("spinach"), _food("lentils")]) is True


def test_is_vegetarian_false_for_chicken() -> None:
    assert _is_vegetarian([_food("chicken breast")]) is False


def test_is_vegetarian_false_for_fish_category() -> None:
    assert _is_vegetarian([_food("salmon fillet", "fish")]) is False


def test_easy_foods_true_for_soft_foods() -> None:
    assert _easy_foods([_food("oatmeal"), _food("yogurt")]) is True


def test_easy_foods_false_for_raw_carrot() -> None:
    assert _easy_foods([_food("raw carrot sticks")]) is False


def test_build_tags_adds_vegetarian() -> None:
    tags = _build_tags({"protein_g": Decimal("0"), "fiber_g": Decimal("0")}, 0, True)
    assert "vegetarian" in tags


def test_build_tags_adds_high_protein() -> None:
    tags = _build_tags({"protein_g": Decimal("25"), "fiber_g": Decimal("0")}, 0, False)
    assert "high_protein" in tags


def test_build_tags_adds_high_fiber() -> None:
    tags = _build_tags({"protein_g": Decimal("0"), "fiber_g": Decimal("8")}, 0, False)
    assert "high_fiber" in tags


def test_build_tags_adds_anti_inflammatory() -> None:
    tags = _build_tags({"protein_g": Decimal("0"), "fiber_g": Decimal("0")}, 6.0, False)
    assert "anti_inflammatory" in tags


def test_build_tags_omits_threshold_tags_below_thresholds() -> None:
    tags = _build_tags({"protein_g": Decimal("24.9"), "fiber_g": Decimal("7.9")}, 5.9, False)
    assert tags == []


def test_food_model_has_needs_review_field() -> None:
    food = _food("submitted food")
    food.needs_review = True
    assert food.needs_review is True


def test_recommendation_log_mode_values_are_plain_strings() -> None:
    assert {"normal", "mixed", "flare_only"} == {"normal", "mixed", "flare_only"}
