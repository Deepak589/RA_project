from __future__ import annotations

from decimal import Decimal

from app.services.food_normalizer import normalize_usda_food


def test_normal_food_extracts_nutrients_by_id() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 123,
            "description": "Salmon, raw",
            "foodCategory": "Finfish and Shellfish Products",
            "servingSize": 85,
            "servingSizeUnit": "g",
            "foodNutrients": [
                {"nutrientId": 1008, "value": 208},
                {"nutrientId": 1003, "value": 20.4},
                {"nutrientId": 1404, "value": 2.2},
                {"nutrientId": 1258, "value": 3.1},
            ],
        }
    )

    assert food.external_id == "123"
    assert food.category == "fish"
    assert food.serving_size_g == Decimal("85")
    assert food.calories == Decimal("208")
    assert food.protein_g == Decimal("20.4")
    assert food.omega3_g == Decimal("2.2")
    assert food.saturated_fat_g == Decimal("3.1")


def test_missing_nutrients_default_to_zero() -> None:
    food = normalize_usda_food({"fdcId": 456, "description": "Unknown", "foodNutrients": []})

    assert food.calories == Decimal("0.0")
    assert food.fiber_g == Decimal("0.0")
    assert food.omega3_g == Decimal("0.0")
    assert "potentially_incomplete_nutrition_data" in food.metadata_jsonb["quality_flags"]
    assert "[DATA ISSUE: calories missing for Unknown]" in food.metadata_jsonb["quality_flags"]
    assert "[DATA ISSUE: fiber missing for Unknown]" in food.metadata_jsonb["quality_flags"]


def test_zero_values_are_preserved() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 789,
            "description": "Plain water",
            "foodNutrients": [{"nutrientId": 1008, "value": 0}, {"nutrientId": 1003, "value": 0}],
        }
    )

    assert food.calories == Decimal("0")
    assert food.protein_g == Decimal("0")


def test_negative_nutrients_are_clamped_to_zero() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 321,
            "description": "USDA calculated edge case",
            "foodNutrients": [{"nutrientId": 1005, "value": -0.428}],
        }
    )

    assert food.carbs_g == Decimal("0.0")


def test_unknown_category_maps_to_other() -> None:
    food = normalize_usda_food({"fdcId": 999, "description": "Mystery food", "foodCategory": "Unmapped"})

    assert food.category == "other"
    assert food.serving_size_g == Decimal("100.0")


def test_calories_fallback_uses_usda_branded_energy_id() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 111,
            "description": "Chicken breast",
            "foodNutrients": [
                {"nutrientId": 1008, "value": 0},
                {"nutrientId": 2047, "value": 165},
            ],
        }
    )

    assert food.calories == Decimal("165")
    assert "[DATA ISSUE: calories missing for Chicken breast]" not in food.metadata_jsonb.get("quality_flags", [])


def test_calories_fallback_uses_2047_when_1008_missing() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 112,
            "description": "Foundation energy edge case",
            "foodNutrients": [{"nutrientId": 2047, "value": 360}],
        }
    )

    assert food.calories == Decimal("360")


def test_fiber_falls_back_to_2033_when_1079_missing() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 113,
            "description": "Lentils with alternate fiber",
            "foodNutrients": [{"nutrientId": 2033, "value": 10.7}],
        }
    )

    assert food.fiber_g == Decimal("10.7")
    assert "[DATA ISSUE: fiber missing for Lentils with alternate fiber]" not in food.metadata_jsonb.get("quality_flags", [])


def test_fiber_falls_back_to_soluble_plus_insoluble_when_primary_ids_missing() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 114,
            "description": "Split fiber food",
            "foodNutrients": [
                {"nutrientId": 1082, "value": 2.5},
                {"nutrientId": 1084, "value": 4.5},
            ],
        }
    )

    assert food.fiber_g == Decimal("7.0")


def test_omega3_combines_ala_epa_and_dha() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 222,
            "description": "Salmon, raw",
            "foodNutrients": [
                {"nutrientId": 1008, "value": 208},
                {"nutrientId": 1404, "value": 0.2},
                {"nutrientId": 1405, "value": 0.8},
                {"nutrientId": 1406, "value": 0.7},
            ],
        }
    )

    assert food.omega3_g == Decimal("1.7")


def test_omega3_combines_current_usda_foundation_epa_dha_ids() -> None:
    food = normalize_usda_food(
        {
            "fdcId": 333,
            "description": "Salmon, raw",
            "foodNutrients": [
                {"nutrientId": 1008, "value": 197},
                {"nutrientId": 1404, "value": 0.541},
                {"nutrientId": 1278, "value": 0.318},
                {"nutrientId": 1272, "value": 0.585},
                {"nutrientId": 1280, "value": 0.166},
            ],
        }
    )

    assert food.omega3_g == Decimal("1.610")
