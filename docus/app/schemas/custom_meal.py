from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomMealIngredientInput(BaseModel):
    food_id: UUID
    portion_g: Decimal = Field(gt=0)
    cooking_state: str = "cooked"


class CustomMealNutrients(BaseModel):
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    total_sugar_g: float
    total_sodium_mg: float
    total_omega3_g: float
    anti_inflammatory_score: float
    is_vegetarian: bool
    is_flare_friendly: bool
    tags: list[str] = Field(default_factory=list)
    missing_ingredients: list[str] = Field(default_factory=list)
    score_note: str | None = None


class CustomMealCalculateRequest(BaseModel):
    name: str
    meal_type: str
    ingredients: list[CustomMealIngredientInput]


class CustomMealCreateRequest(CustomMealCalculateRequest):
    missing_ingredient_names: list[str] = Field(default_factory=list)


class CustomMealIngredientResponse(BaseModel):
    food_id: UUID
    food_name: str
    portion_g: Decimal
    cooking_state: str
    display_note: str | None = None
    calories_contribution: float
    protein_contribution: float


class CustomMealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    meal_type: str | None = None
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
    ingredients: list[CustomMealIngredientResponse] = Field(default_factory=list)
    created_at: datetime


class CustomMealListResponse(BaseModel):
    items: list[CustomMealResponse]
    total: int
    limit: int
    offset: int
