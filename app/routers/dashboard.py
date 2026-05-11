from __future__ import annotations

from datetime import date

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.log import LifestyleLogResponse, SymptomLogResponse
from app.schemas.recommendation import DailyNutritionSummary, RecommendationResponse
from app.services.dashboard_service import get_today_dashboard, get_weekly_dashboard
from app.services.nutrition_tracker import get_nutrition_gaps

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


class TodayDashboardResponse(BaseModel):
    date: date
    nutrition: DailyNutritionSummary
    symptom_log: SymptomLogResponse | None
    lifestyle_log: LifestyleLogResponse | None
    next_recommendation: RecommendationResponse | None
    flare_active: bool
    escalation_active: bool
    escalation_message: str | None


class WeeklyDashboardResponse(BaseModel):
    week_start: date
    week_end: date
    avg_pain_score: float | None
    avg_fatigue: float | None
    avg_sleep_hours: float | None
    avg_meal_quality_score: float | None
    total_meals_logged: int
    meal_logged_days: int
    recommendation_acceptance_rate: float
    flare_days_count: int
    best_day: date | None
    worst_day: date | None
    insights: list[str]


@router.get("/today", response_model=TodayDashboardResponse)
async def get_today_dashboard_endpoint(
    diet_override: Annotated[str | None, Query(pattern="^(vegetarian|non_vegetarian)$")] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> TodayDashboardResponse:
    dashboard = await get_today_dashboard(db, UUID(user_id), diet_override=diet_override)
    gaps = get_nutrition_gaps(dashboard.nutrition)
    rec = dashboard.next_recommendation
    return TodayDashboardResponse(
        date=dashboard.date,
        nutrition=DailyNutritionSummary(
            calories_consumed=dashboard.nutrition.calories_consumed,
            protein_consumed=dashboard.nutrition.protein_consumed,
            fiber_consumed=dashboard.nutrition.fiber_consumed,
            omega3_consumed=dashboard.nutrition.omega3_consumed,
            is_protein_low=gaps.is_protein_low,
            is_fiber_low=gaps.is_fiber_low,
            is_omega3_low=gaps.is_omega3_low,
            is_sugar_over=gaps.is_sugar_over,
            is_sodium_over=gaps.is_sodium_over,
        ),
        symptom_log=dashboard.symptom_log,
        lifestyle_log=dashboard.lifestyle_log,
        next_recommendation=RecommendationResponse(
            recommended_meal=rec.primary_recommendation,
            primary=rec.primary_recommendation,
            alternatives=rec.alternatives,
            explanation=rec.explanation,
            rule_applied=rec.rule_applied,
            flare_mode_active=rec.flare_mode_active,
            recommendation_mode=rec.recommendation_mode,
            recommendation_log_id=rec.recommendation_log_id,
            nutrition_summary=DailyNutritionSummary(
                calories_consumed=rec.nutrition_context.calories_consumed,
                protein_consumed=rec.nutrition_context.protein_consumed,
                fiber_consumed=rec.nutrition_context.fiber_consumed,
                omega3_consumed=rec.nutrition_context.omega3_consumed,
                is_protein_low=rec.gaps.is_protein_low,
                is_fiber_low=rec.gaps.is_fiber_low,
                is_omega3_low=rec.gaps.is_omega3_low,
                is_sugar_over=rec.gaps.is_sugar_over,
                is_sodium_over=rec.gaps.is_sodium_over,
            ),
        )
        if rec
        else None,
        flare_active=dashboard.flare_active,
        escalation_active=dashboard.escalation_active,
        escalation_message=dashboard.escalation_message,
    )


@router.get("/weekly", response_model=WeeklyDashboardResponse)
async def get_weekly_dashboard_endpoint(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> WeeklyDashboardResponse:
    return await get_weekly_dashboard(db, UUID(user_id))
