from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.schemas.food import FoodCreate

NUTRIENT_ID_TO_FIELD = {
    1003: "protein_g",
    1005: "carbs_g",
    2000: "sugar_g",
    1093: "sodium_mg",
    1004: "fat_g",
    1258: "saturated_fat_g",
    1087: "calcium_mg",
    1114: "vitamin_d_ug",
}
CALORIES_PRIMARY_ID = 1008
CALORIES_FALLBACK_ID = 2047
FIBER_PRIMARY_ID = 1079
FIBER_FALLBACK_ID = 2033
SOLUBLE_FIBER_ID = 1082
INSOLUBLE_FIBER_ID = 1084
OMEGA3_NUTRIENT_IDS = (1404, 1405, 1406, 1278, 1272, 1280)

ZERO = Decimal("0.0")
DEFAULT_SERVING_SIZE_G = Decimal("100.0")


def normalize_usda_food(raw_food: dict[str, Any]) -> FoodCreate:
    nutrient_values = _extract_nutrients(raw_food.get("foodNutrients", []))
    category = map_usda_category(raw_food.get("foodCategory"))
    serving_size_g = _extract_serving_size_g(raw_food)
    metadata = dict(raw_food)
    food_name = _clean_text(raw_food.get("description")) or "Unknown USDA food"

    if nutrient_values["omega3_g"] == ZERO and nutrient_values["fiber_g"] == ZERO:
        metadata.setdefault("quality_flags", []).append("potentially_incomplete_nutrition_data")
    if nutrient_values["calories"] == ZERO:
        metadata.setdefault("quality_flags", []).append(f"[DATA ISSUE: calories missing for {food_name}]")
    if nutrient_values["fiber_g"] == ZERO:
        metadata.setdefault("quality_flags", []).append(f"[DATA ISSUE: fiber missing for {food_name}]")

    return FoodCreate(
        external_source="usda",
        external_id=str(raw_food.get("fdcId", "")),
        name=food_name,
        brand_name=_clean_text(raw_food.get("brandOwner") or raw_food.get("brandName")),
        category=category,
        serving_size_g=serving_size_g,
        ingredients_text=_clean_text(raw_food.get("ingredients")),
        dietary_tags_jsonb=[],
        metadata_jsonb=metadata,
        **nutrient_values,
    )


def map_usda_category(food_category: str | None) -> str:
    if not food_category:
        return "other"

    category = food_category.lower()
    if any(token in category for token in ("poultry", "beef", "pork", "lamb", "meat", "egg")):
        return "protein"
    if any(token in category for token in ("fish", "shellfish", "seafood")):
        return "fish"
    if any(token in category for token in ("legume", "bean", "pea", "lentil", "soy")):
        return "legume"
    if "vegetable" in category:
        return "vegetable"
    if "fruit" in category or "berries" in category:
        return "fruit"
    if any(token in category for token in ("cereal", "grain", "pasta", "rice", "oat")):
        return "grain"
    if any(token in category for token in ("dairy", "milk", "cheese", "yogurt")):
        return "dairy"
    if any(token in category for token in ("nut", "seed")):
        return "nut_seed"
    if any(token in category for token in ("oil", "fat")):
        return "oil"
    if any(token in category for token in ("spice", "herb")):
        return "spice"
    return "other"


def _extract_nutrients(food_nutrients: list[dict[str, Any]]) -> dict[str, Decimal]:
    values = {field: ZERO for field in (*NUTRIENT_ID_TO_FIELD.values(), "calories", "omega3_g")}
    nutrient_lookup: dict[int, Decimal] = {}
    for nutrient in food_nutrients or []:
        nutrient_id = _extract_nutrient_id(nutrient)
        if nutrient_id is None:
            continue
        nutrient_lookup[nutrient_id] = max(_to_decimal(nutrient.get("value")), ZERO)
        if nutrient_id in NUTRIENT_ID_TO_FIELD:
            values[NUTRIENT_ID_TO_FIELD[nutrient_id]] = nutrient_lookup[nutrient_id]

    values["calories"] = nutrient_lookup.get(CALORIES_PRIMARY_ID, ZERO)
    if values["calories"] == ZERO:
        values["calories"] = nutrient_lookup.get(CALORIES_FALLBACK_ID, ZERO)

    values["fiber_g"] = nutrient_lookup.get(FIBER_PRIMARY_ID, ZERO)
    if values["fiber_g"] == ZERO:
        values["fiber_g"] = nutrient_lookup.get(FIBER_FALLBACK_ID, ZERO)
    if values["fiber_g"] == ZERO:
        values["fiber_g"] = nutrient_lookup.get(SOLUBLE_FIBER_ID, ZERO) + nutrient_lookup.get(INSOLUBLE_FIBER_ID, ZERO)

    values["omega3_g"] = sum((nutrient_lookup.get(nutrient_id, ZERO) for nutrient_id in OMEGA3_NUTRIENT_IDS), ZERO)
    return values


def _extract_nutrient_id(nutrient: dict[str, Any]) -> int | None:
    for key in ("nutrientId", "nutrient_id"):
        if key in nutrient:
            return _to_int(nutrient.get(key))

    nested = nutrient.get("nutrient")
    if isinstance(nested, dict):
        for key in ("id", "number", "nutrientId"):
            nutrient_id = _to_int(nested.get(key))
            if nutrient_id is not None:
                return nutrient_id
    return None


def _extract_serving_size_g(raw_food: dict[str, Any]) -> Decimal:
    serving_size = _to_decimal(raw_food.get("servingSize"))
    serving_unit = str(raw_food.get("servingSizeUnit") or "").lower()
    if serving_size is not None and serving_size > ZERO and serving_unit in {"g", "gram", "grams"}:
        return serving_size
    return DEFAULT_SERVING_SIZE_G


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return ZERO
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ZERO


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
