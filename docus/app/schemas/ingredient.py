from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.food import FoodResponse


class MissingIngredientCreate(BaseModel):
    ingredient_name: str = Field(min_length=1)
    submitted_calories: Decimal | None = None
    submitted_protein_g: Decimal | None = None
    submitted_carbs_g: Decimal | None = None
    submitted_fat_g: Decimal | None = None
    submitted_fiber_g: Decimal | None = None
    submitted_sugar_g: Decimal | None = None
    submitted_sodium_mg: Decimal | None = None
    submitted_source: str | None = None


class IngredientSearchRequest(BaseModel):
    ingredient_name: str = Field(min_length=1)
    submitted_values: MissingIngredientCreate | None = None


class MissingIngredientAdminUpdate(BaseModel):
    status: str
    admin_notes: str | None = None
    food_id: UUID | None = None


class MissingIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    ingredient_name: str
    status: str
    submitted_calories: Decimal | None = None
    submitted_protein_g: Decimal | None = None
    submitted_carbs_g: Decimal | None = None
    submitted_fat_g: Decimal | None = None
    submitted_fiber_g: Decimal | None = None
    submitted_sugar_g: Decimal | None = None
    submitted_sodium_mg: Decimal | None = None
    submitted_source: str | None = None
    reported_count: int
    admin_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    food_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class IngredientSearchResult(BaseModel):
    found: bool
    matches: list[FoodResponse] = Field(default_factory=list)
    missing_record: MissingIngredientResponse | None = None
    suggestion_message: str | None = None


class MissingIngredientCreateResponse(BaseModel):
    status: str
    message: str
    reported_count: int


class MissingIngredientListResponse(BaseModel):
    items: list[MissingIngredientResponse]
    total: int
    limit: int
    offset: int
