from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RecommendationFeedbackStatus
from app.schemas.meal import MealResponse


class RecommendationLogBase(BaseModel):
    meal_id: UUID | None = None
    recommended_for_meal_type: str
    recommendation_context_jsonb: dict[str, Any] = Field(default_factory=dict)
    explanation_text: str
    alternatives_jsonb: list[dict[str, Any]] = Field(default_factory=list)
    rules_applied_jsonb: list[dict[str, Any]] = Field(default_factory=list)
    rule_priority_applied: str | None = None
    flare_mode_active: bool = False
    recommendation_mode: str | None = None
    daily_nutrition_context_json: dict[str, Any] | None = None
    shown_at: datetime | None = None
    feedback_status: RecommendationFeedbackStatus = RecommendationFeedbackStatus.PENDING
    feedback_reason: str | None = None
    replacement_food_id: UUID | None = None
    replacement_meal_id: UUID | None = None


class RecommendationLogCreate(RecommendationLogBase):
    pass


class RecommendationFeedbackUpdate(BaseModel):
    feedback_status: RecommendationFeedbackStatus | None = None
    feedback: RecommendationFeedbackStatus | None = None
    feedback_reason: str | None = None
    replacement_food_id: UUID | None = None
    replacement_meal_id: UUID | None = None


class DailyNutritionSummary(BaseModel):
    calories_consumed: float
    protein_consumed: float
    fiber_consumed: float
    omega3_consumed: float
    is_protein_low: bool
    is_fiber_low: bool
    is_omega3_low: bool
    is_sugar_over: bool
    is_sodium_over: bool


class RecommendationResponse(BaseModel):
    recommended_meal: MealResponse
    primary: MealResponse
    alternatives: list[MealResponse]
    explanation: str
    rule_applied: str
    flare_mode_active: bool
    recommendation_mode: str
    nutrition_summary: DailyNutritionSummary
    recommendation_log_id: UUID | None = None


class RecommendationLogResponse(RecommendationLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    shown_at: datetime
    created_at: datetime
    updated_at: datetime


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationLogResponse]
    total: int
    limit: int
    offset: int
