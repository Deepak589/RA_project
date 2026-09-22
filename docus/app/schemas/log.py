from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import FlareLevel


class FoodLogBase(BaseModel):
    food_id: UUID | None = None
    meal_id: UUID | None = None
    recommendation_meal_id: UUID | None = None
    custom_meal_id: UUID | None = None
    custom_food_name: str | None = None
    meal_type: str
    portion_g: Decimal | None = None
    raw_portion_g: Decimal | None = None
    portion_label: str | None = None
    notes: str | None = None
    log_source: str = "manual_log"
    logged_at: datetime | None = None


class FoodLogCreate(FoodLogBase):
    pass


class FoodLogResponse(FoodLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    cooking_state_at_log: str | None = None
    conversion_factor_at_log: Decimal | None = None
    display_calories: Decimal | None = None
    display_protein_g: Decimal | None = None
    logged_at: datetime
    created_at: datetime
    updated_at: datetime


class SymptomLogBase(BaseModel):
    pain_score: int
    fatigue_score: int | None = None
    fatigue: int | None = None
    stiffness_score: int = 0
    stiffness_minutes: int | None = None
    swelling_score: int | None = None
    swelling: bool = False
    flare_level: FlareLevel = FlareLevel.NONE
    note: str | None = None
    notes: str | None = None
    escalation_triggered: bool = False
    mobility_score: int | None = None
    energy_level: int | None = None
    sleep_quality: int | None = None
    mood_score: int | None = None
    logged_at: datetime | None = None


class SymptomLogCreate(SymptomLogBase):
    pass


class SymptomLogUpdateRequest(BaseModel):
    pain_score: int | None = None
    fatigue_score: int | None = None
    fatigue: int | None = None
    stiffness_score: int | None = None
    stiffness_minutes: int | None = None
    swelling_score: int | None = None
    swelling: bool | None = None
    flare_level: FlareLevel | None = None
    note: str | None = None
    notes: str | None = None
    mobility_score: int | None = None
    energy_level: int | None = None
    sleep_quality: int | None = None
    mood_score: int | None = None
    logged_at: datetime | None = None


class SymptomLogResponse(SymptomLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    escalation_message: str | None = None
    logged_at: datetime
    created_at: datetime


class LifestyleLogBase(BaseModel):
    log_date: date
    sleep_hours: Decimal | None = None
    steps: int | None = None
    water_ml: int | None = None
    water_intake_ml: int | None = None
    stress_level: int | None = None
    exercise_type: str | None = None
    exercise_duration_minutes: int | None = None
    smoking: bool = False
    alcohol: bool = False
    medication_taken: bool | None = None
    notes: str | None = None


class LifestyleLogCreate(LifestyleLogBase):
    pass


class LifestyleLogResponse(LifestyleLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
