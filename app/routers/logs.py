from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_current_user_id
from app.db.session import get_db_session
from app.schemas.log import (
    FoodLogCreate,
    FoodLogResponse,
    LifestyleLogCreate,
    LifestyleLogResponse,
    SymptomLogCreate,
    SymptomLogResponse,
    SymptomLogUpdateRequest,
)
from app.schemas.recommendation import DailyNutritionSummary
from app.services.log_service import (
    create_food_log,
    create_lifestyle_log,
    create_symptom_log,
    delete_food_log,
    get_food_logs_by_date,
    get_lifestyle_log_by_date,
    get_symptom_log_by_date,
    get_todays_food_logs,
    get_todays_lifestyle_log,
    get_todays_symptom_log,
    upsert_todays_symptom_log,
)
from app.services.nutrition_tracker import get_nutrition_gaps, summarize_food_logs

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


class FoodLogsWithSummary(BaseModel):
    items: list[FoodLogResponse]
    nutrition_summary: DailyNutritionSummary


@router.post("/food", response_model=FoodLogResponse)
async def create_food_log_endpoint(
    data: FoodLogCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> FoodLogResponse:
    return await create_food_log(db, UUID(user_id), data)


@router.get("/food/today", response_model=FoodLogsWithSummary)
async def get_todays_food_logs_endpoint(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> FoodLogsWithSummary:
    logs = await get_todays_food_logs(db, UUID(user_id))
    return _food_logs_response(logs)


@router.get("/food/{log_date}", response_model=FoodLogsWithSummary)
async def get_food_logs_by_date_endpoint(
    log_date: date,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> FoodLogsWithSummary:
    logs = await get_food_logs_by_date(db, UUID(user_id), log_date)
    return _food_logs_response(logs)


@router.delete("/food/{log_id}")
async def delete_food_log_endpoint(
    log_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> dict[str, str]:
    return await delete_food_log(db, UUID(user_id), log_id)


@router.post("/symptoms", response_model=SymptomLogResponse)
async def create_symptom_log_endpoint(
    data: SymptomLogCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> SymptomLogResponse:
    return await create_symptom_log(db, UUID(user_id), data)


@router.get("/symptoms/today", response_model=SymptomLogResponse | None)
async def get_todays_symptom_log_endpoint(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
):
    return await get_todays_symptom_log(db, UUID(user_id))


@router.patch("/symptoms/today", response_model=SymptomLogResponse)
async def patch_todays_symptom_log_endpoint(
    data: SymptomLogUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> SymptomLogResponse:
    return await upsert_todays_symptom_log(db, UUID(user_id), data)


@router.get("/symptoms/{log_date}", response_model=SymptomLogResponse | None)
async def get_symptom_log_by_date_endpoint(
    log_date: date,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
):
    return await get_symptom_log_by_date(db, UUID(user_id), log_date)


@router.post("/lifestyle", response_model=LifestyleLogResponse)
async def create_lifestyle_log_endpoint(
    data: LifestyleLogCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
) -> LifestyleLogResponse:
    return await create_lifestyle_log(db, UUID(user_id), data)


@router.get("/lifestyle/today", response_model=LifestyleLogResponse | None)
async def get_todays_lifestyle_log_endpoint(
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_current_user_id),
):
    return await get_todays_lifestyle_log(db, UUID(user_id))


def _food_logs_response(logs) -> FoodLogsWithSummary:
    state = summarize_food_logs(logs)
    gaps = get_nutrition_gaps(state)
    return FoodLogsWithSummary(
        items=logs,
        nutrition_summary=DailyNutritionSummary(
            calories_consumed=state.calories_consumed,
            protein_consumed=state.protein_consumed,
            fiber_consumed=state.fiber_consumed,
            omega3_consumed=state.omega3_consumed,
            is_protein_low=gaps.is_protein_low,
            is_fiber_low=gaps.is_fiber_low,
            is_omega3_low=gaps.is_omega3_low,
            is_sugar_over=gaps.is_sugar_over,
            is_sodium_over=gaps.is_sodium_over,
        ),
    )
