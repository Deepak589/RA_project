from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MealIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    food_id: UUID
    food_name: str
    portion_g: Decimal
    cooking_state: str
    display_note: str | None = None

    @model_validator(mode="before")
    @classmethod
    def add_food_name(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return value
        food = getattr(value, "food", None)
        return {
            "food_id": getattr(value, "food_id"),
            "food_name": getattr(food, "name", ""),
            "portion_g": getattr(value, "portion_g"),
            "cooking_state": getattr(value, "cooking_state"),
            "display_note": getattr(value, "display_note"),
        }


class MealBase(BaseModel):
    name: str
    meal_type: str
    cuisine_type: str | None = None
    prep_time_minutes: int | None = None
    effort_level: str = "medium"


class MealCreate(MealBase):
    serving_size_description: str | None = None
    tags: list[str] = Field(default_factory=list)
    instructions: str | None = None


class MealResponse(MealBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    serving_size_description: str | None = None
    total_calories: Decimal | None = None
    total_protein_g: Decimal | None = None
    total_carbs_g: Decimal | None = None
    total_fat_g: Decimal | None = None
    total_fiber_g: Decimal | None = None
    total_sugar_g: Decimal | None = None
    total_sodium_mg: Decimal | None = None
    total_omega3_g: Decimal | None = None
    anti_inflammatory_score: Decimal
    is_vegetarian: bool
    is_flare_friendly: bool
    tags: list[str] = Field(default_factory=list)
    instructions: str | None = None
    ingredients: list[MealIngredientResponse] = Field(default_factory=list)
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _fallback_ingredients_from_meal_items(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return value
        try:
            ingredients = list(value.ingredients or [])
        except Exception:
            return value
        if ingredients:
            return value
        try:
            meal_items = list(value.meal_items or [])
        except Exception:
            return value
        if not meal_items:
            return value
        data = {k: getattr(value, k, None) for k in cls.model_fields if k != "ingredients"}
        data["ingredients"] = [
            {
                "food_id": item.food_id,
                "food_name": item.food.name if getattr(item, "food", None) else "",
                "portion_g": item.grams,
                "cooking_state": item.food.cooking_state if getattr(item, "food", None) else "unspecified",
                "display_note": None,
            }
            for item in meal_items
        ]
        return data


class MealSearchResponse(BaseModel):
    items: list[MealResponse]
    total: int
    limit: int
    offset: int


class CustomMealBase(BaseModel):
    name: str
    meal_type: str | None = None


class CustomMealResponse(CustomMealBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    total_calories: Decimal | None = None
    total_protein_g: Decimal | None = None
    total_carbs_g: Decimal | None = None
    total_fat_g: Decimal | None = None
    total_fiber_g: Decimal | None = None
    total_sugar_g: Decimal | None = None
    total_sodium_mg: Decimal | None = None
    total_omega3_g: Decimal | None = None
    anti_inflammatory_score: Decimal | None = None
    is_vegetarian: bool
    is_flare_friendly: bool
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
