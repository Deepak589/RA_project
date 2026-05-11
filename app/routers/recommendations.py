from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.models.enums import RecommendationFeedbackStatus
from app.schemas.recommendation import (
    DailyNutritionSummary,
    RecommendationFeedbackUpdate,
    RecommendationHistoryResponse,
    RecommendationResponse,
)
from app.services.recommendation_service import get_next_recommendation, get_recommendation_history, submit_feedback

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/next", response_model=RecommendationResponse)
async def get_next_recommendation_endpoint(
    meal_type: Annotated[str, Query(pattern="^(breakfast|lunch|dinner|snack)$")],
    flare_active: bool = Query(default=False),
    diet_override: Annotated[str | None, Query(pattern="^(vegetarian|non_vegetarian)$")] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> RecommendationResponse:
    result = await get_next_recommendation(db, UUID(user_id), meal_type, flare_active, diet_override=diet_override)
    return RecommendationResponse(
        recommended_meal=result.primary_recommendation,
        primary=result.primary_recommendation,
        alternatives=result.alternatives,
        explanation=result.explanation,
        rule_applied=result.rule_applied,
        flare_mode_active=result.flare_mode_active,
        recommendation_mode=result.recommendation_mode,
        recommendation_log_id=result.recommendation_log_id,
        nutrition_summary=DailyNutritionSummary(
            calories_consumed=result.nutrition_context.calories_consumed,
            protein_consumed=result.nutrition_context.protein_consumed,
            fiber_consumed=result.nutrition_context.fiber_consumed,
            omega3_consumed=result.nutrition_context.omega3_consumed,
            is_protein_low=result.gaps.is_protein_low,
            is_fiber_low=result.gaps.is_fiber_low,
            is_omega3_low=result.gaps.is_omega3_low,
            is_sugar_over=result.gaps.is_sugar_over,
            is_sodium_over=result.gaps.is_sodium_over,
        ),
    )


@router.post("/{recommendation_id}/feedback")
async def submit_recommendation_feedback_endpoint(
    recommendation_id: UUID,
    data: RecommendationFeedbackUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_current_user_id),
) -> dict[str, str]:
    feedback = data.feedback or data.feedback_status or RecommendationFeedbackStatus.PENDING
    return await submit_feedback(db, recommendation_id, feedback, data.replacement_meal_id)


@router.get("/history", response_model=RecommendationHistoryResponse)
async def get_recommendation_history_endpoint(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> RecommendationHistoryResponse:
    items, total = await get_recommendation_history(db, UUID(user_id), limit, offset)
    return RecommendationHistoryResponse(items=items, total=total, limit=limit, offset=offset)
