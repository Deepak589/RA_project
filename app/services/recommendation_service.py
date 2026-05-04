from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import RecommendationFeedbackStatus
from app.models.recommendation import RecommendationLog
from app.services.rule_engine import RecommendationResult, get_next_meal_recommendation


async def get_next_recommendation(
    db: AsyncSession,
    user_id: UUID,
    meal_type: str,
    flare_active: bool = False,
) -> RecommendationResult:
    return await get_next_meal_recommendation(db, user_id=user_id, meal_type=meal_type, flare_active=flare_active, limit=5)


async def submit_feedback(
    db: AsyncSession,
    recommendation_id: UUID,
    feedback: RecommendationFeedbackStatus | str,
    replacement_meal_id: UUID | None = None,
) -> dict[str, str]:
    log = await db.get(RecommendationLog, recommendation_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    feedback_status = RecommendationFeedbackStatus(feedback)
    log.feedback_status = feedback_status
    if feedback_status == RecommendationFeedbackStatus.REPLACED:
        log.replacement_meal_id = replacement_meal_id
    await db.commit()
    return {"status": "ok"}


async def get_recommendation_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[RecommendationLog], int]:
    statement = select(RecommendationLog).where(RecommendationLog.user_id == user_id)
    total = int(await db.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    result = await db.scalars(
        statement.options(selectinload(RecommendationLog.recommended_meal))
        .order_by(RecommendationLog.shown_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result), total
