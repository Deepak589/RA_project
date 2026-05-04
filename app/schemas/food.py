from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FoodBase(BaseModel):
    external_source: str = "usda"
    external_id: str
    name: str
    brand_name: str | None = None
    category: str | None = None
    serving_size_g: Decimal | None = None
    calories: Decimal | None = None
    protein_g: Decimal | None = None
    carbs_g: Decimal | None = None
    fat_g: Decimal | None = None
    saturated_fat_g: Decimal = Decimal("0")
    fiber_g: Decimal | None = None
    sugar_g: Decimal | None = None
    sodium_mg: Decimal | None = None
    omega3_g: Decimal | None = None
    calcium_mg: Decimal = Decimal("0")
    vitamin_d_ug: Decimal = Decimal("0")
    anti_inflammatory_score: Decimal = Decimal("0")
    ingredients_text: str | None = None
    dietary_tags_jsonb: list[str] = Field(default_factory=list)
    metadata_jsonb: dict[str, Any] = Field(default_factory=dict)
    cooking_state: str = "unspecified"
    conversion_factor: Decimal = Decimal("1.0")
    display_note: str | None = None
    quality_flag: str = "usda_verified"
    manual_override: bool = False


class FoodCreate(FoodBase):
    pass


class FoodResponse(FoodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_calories: float = 0.0
    display_protein_g: float = 0.0
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def compute_display_fields(self) -> "FoodResponse":
        factor = self.conversion_factor or Decimal("1.0")
        self.display_calories = round(float((self.calories or Decimal("0")) * factor), 1)
        self.display_protein_g = round(float((self.protein_g or Decimal("0")) * factor), 1)
        return self


class FoodSearchResponse(BaseModel):
    items: list[FoodResponse]
    total: int
    limit: int
    offset: int


class MealItemBase(BaseModel):
    food_id: UUID
    quantity: Decimal
    unit: str
    grams: Decimal
    sort_order: int = 0


class MealItemCreate(MealItemBase):
    pass


class MealItemResponse(MealItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meal_id: UUID
    created_at: datetime


class MealBase(BaseModel):
    name: str
    description: str | None = None
    meal_type: str
    prep_time_minutes: int = 0
    anti_inflammatory_score: Decimal = Decimal("0")
    protein_g: Decimal | None = None
    fiber_g: Decimal | None = None
    sugar_g: Decimal | None = None
    sodium_mg: Decimal | None = None
    calories: Decimal | None = None
    is_curated: bool = True
    dietary_tags_jsonb: list[str] = Field(default_factory=list)
    reason_tags_jsonb: list[str] = Field(default_factory=list)


class MealCreate(MealBase):
    meal_items: list[MealItemCreate] = Field(default_factory=list)


class MealResponse(MealBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    meal_items: list[MealItemResponse] = Field(default_factory=list)
