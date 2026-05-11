from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import FlareLevel
from app.models.food import Food
from app.models.log import FoodLog, LifestyleLog, SymptomLog
from app.models.meal import CustomMeal, Meal
from app.schemas.log import FoodLogCreate, LifestyleLogCreate, SymptomLogCreate, SymptomLogUpdateRequest


ESCALATION_MESSAGE = (
    "You logged symptoms that may need medical attention. This app cannot assess urgent health problems or tell "
    "you how to treat a flare. If this pain or flare is severe, unusual for you, getting worse, or you are worried "
    "about your safety, please contact your clinician, urgent care, or local emergency services as appropriate."
)


async def create_food_log(db: AsyncSession, user_id: UUID, data: FoodLogCreate) -> FoodLog:
    log_source = data.log_source
    values: dict[str, object] = {
        "user_id": user_id,
        "food_id": data.food_id,
        "meal_id": data.meal_id,
        "custom_food_name": data.custom_food_name,
        "meal_type": data.meal_type,
        "portion_g": data.portion_g,
        "raw_portion_g": data.raw_portion_g,
        "portion_label": data.portion_label,
        "notes": data.notes,
        "log_source": log_source,
        "logged_at": data.logged_at or datetime.now(timezone.utc).replace(tzinfo=None),
    }
    if log_source == "curated_recommendation":
        meal_id = data.recommendation_meal_id or data.meal_id
        meal = await _get_or_404(db, Meal, meal_id, "Meal not found")
        values.update(
            {
                "meal_id": meal.id,
                "recommendation_meal_id": meal.id,
                "display_calories": meal.total_calories,
                "display_protein_g": meal.total_protein_g,
                "custom_food_name": None,
            }
        )
    elif log_source == "custom_meal":
        if data.custom_meal_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Custom meal not found")
        custom_meal = await db.scalar(
            select(CustomMeal).where(CustomMeal.id == data.custom_meal_id, CustomMeal.user_id == user_id)
        )
        if custom_meal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom meal not found")
        values.update(
            {
                "custom_meal_id": custom_meal.id,
                "custom_food_name": custom_meal.name,
                "display_calories": custom_meal.total_calories,
                "display_protein_g": custom_meal.total_protein_g,
                "raw_portion_g": data.raw_portion_g or data.portion_g,
                "cooking_state_at_log": "cooked",
                "conversion_factor_at_log": Decimal("1.0"),
            }
        )
    else:
        food = await _get_or_404(db, Food, data.food_id, "Food not found")
        factor = food.conversion_factor or Decimal("1.0")
        values.update(
            {
                "cooking_state_at_log": food.cooking_state if food.cooking_state != "unspecified" else None,
                "conversion_factor_at_log": factor,
                "display_calories": _scaled(food.calories, data.portion_g, food.serving_size_g, factor),
                "display_protein_g": _scaled(food.protein_g, data.portion_g, food.serving_size_g, factor),
            }
        )
    log = FoodLog(**values)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return await _load_food_log(db, log.id)


async def get_todays_food_logs(db: AsyncSession, user_id: UUID) -> list[FoodLog]:
    return await get_food_logs_by_date(db, user_id, datetime.now(timezone.utc).date())


async def get_food_logs_by_date(db: AsyncSession, user_id: UUID, log_date: date) -> list[FoodLog]:
    start = datetime.combine(log_date, time.min)
    end = datetime.combine(log_date, time.max)
    result = await db.scalars(
        select(FoodLog)
        .where(FoodLog.user_id == user_id, FoodLog.logged_at >= start, FoodLog.logged_at <= end)
        .options(selectinload(FoodLog.food), selectinload(FoodLog.meal), selectinload(FoodLog.custom_meal))
        .order_by(FoodLog.logged_at)
    )
    return list(result)


async def delete_food_log(db: AsyncSession, user_id: UUID, log_id: UUID) -> dict[str, str]:
    log = await db.get(FoodLog, log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    if log.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Food log belongs to another user")
    await db.delete(log)
    await db.commit()
    return {"status": "deleted"}


async def create_symptom_log(db: AsyncSession, user_id: UUID, data: SymptomLogCreate) -> SymptomLog:
    fatigue = data.fatigue_score if data.fatigue_score is not None else data.fatigue or 0
    swelling_score = data.swelling_score if data.swelling_score is not None else (10 if data.swelling else 0)
    note = data.note if data.note is not None else data.notes
    escalation = _should_escalate(data.pain_score, data.flare_level)
    log = SymptomLog(
        user_id=user_id,
        pain_score=data.pain_score,
        fatigue_score=fatigue,
        stiffness_score=data.stiffness_score,
        stiffness_minutes=data.stiffness_minutes,
        swelling_score=swelling_score,
        flare_level=data.flare_level,
        note=note,
        escalation_triggered=escalation,
        mobility_score=data.mobility_score,
        energy_level=data.energy_level,
        sleep_quality=data.sleep_quality,
        mood_score=data.mood_score,
        logged_at=data.logged_at or datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return _with_escalation_message(log)


async def upsert_todays_symptom_log(db: AsyncSession, user_id: UUID, data: SymptomLogUpdateRequest) -> SymptomLog:
    log = await get_todays_symptom_log(db, user_id)
    if log is None:
        payload = data.model_dump(exclude_none=True)
        pain_score = payload.pop("pain_score", 0)
        flare_level = payload.pop("flare_level", FlareLevel.NONE)
        create_data = SymptomLogCreate(pain_score=pain_score, flare_level=flare_level, **payload)
        return await create_symptom_log(db, user_id, create_data)

    updates = data.model_dump(exclude_none=True)
    if "fatigue" in updates and "fatigue_score" not in updates:
        updates["fatigue_score"] = updates.pop("fatigue")
    if "swelling" in updates and "swelling_score" not in updates:
        updates["swelling_score"] = 10 if updates.pop("swelling") else 0
    if "notes" in updates and "note" not in updates:
        updates["note"] = updates.pop("notes")

    for field, value in updates.items():
        setattr(log, field, value)

    pain_score = log.pain_score if log.pain_score is not None else 0
    flare_level = log.flare_level or FlareLevel.NONE
    log.escalation_triggered = _should_escalate(pain_score, flare_level)
    if log.logged_at is None:
        log.logged_at = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()
    await db.refresh(log)
    return _with_escalation_message(log)


async def get_todays_symptom_log(db: AsyncSession, user_id: UUID) -> SymptomLog | None:
    return await get_symptom_log_by_date(db, user_id, datetime.now(timezone.utc).date())


async def get_symptom_log_by_date(db: AsyncSession, user_id: UUID, log_date: date) -> SymptomLog | None:
    start = datetime.combine(log_date, time.min)
    end = datetime.combine(log_date, time.max)
    log = await db.scalar(
        select(SymptomLog)
        .where(SymptomLog.user_id == user_id, SymptomLog.logged_at >= start, SymptomLog.logged_at <= end)
        .order_by(SymptomLog.logged_at.desc())
    )
    return _with_escalation_message(log)


async def create_lifestyle_log(db: AsyncSession, user_id: UUID, data: LifestyleLogCreate) -> LifestyleLog:
    water_ml = data.water_ml if data.water_ml is not None else data.water_intake_ml
    log = await db.scalar(select(LifestyleLog).where(LifestyleLog.user_id == user_id, LifestyleLog.log_date == data.log_date))
    if log is None:
        log = LifestyleLog(user_id=user_id, log_date=data.log_date)
        db.add(log)
    log.sleep_hours = data.sleep_hours
    log.steps = data.steps
    log.water_ml = water_ml
    log.stress_level = data.stress_level
    log.exercise_type = data.exercise_type
    log.exercise_duration_minutes = data.exercise_duration_minutes
    log.smoking = data.smoking
    log.alcohol = data.alcohol
    log.medication_taken = data.medication_taken
    log.notes = data.notes
    await db.commit()
    await db.refresh(log)
    return log


async def get_todays_lifestyle_log(db: AsyncSession, user_id: UUID) -> LifestyleLog | None:
    return await get_lifestyle_log_by_date(db, user_id, datetime.now(timezone.utc).date())


async def get_lifestyle_log_by_date(db: AsyncSession, user_id: UUID, log_date: date) -> LifestyleLog | None:
    return await db.scalar(select(LifestyleLog).where(LifestyleLog.user_id == user_id, LifestyleLog.log_date == log_date))


async def _load_food_log(db: AsyncSession, log_id: UUID) -> FoodLog:
    log = await db.scalar(
        select(FoodLog)
        .where(FoodLog.id == log_id)
        .options(selectinload(FoodLog.food), selectinload(FoodLog.meal), selectinload(FoodLog.custom_meal))
    )
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food log not found")
    return log


async def _get_or_404(db: AsyncSession, model: type, item_id: UUID | None, message: str):
    if item_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
    item = await db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return item


def _scaled(value: Decimal | None, portion_g: Decimal | None, serving_size_g: Decimal | None, conversion_factor: Decimal) -> Decimal | None:
    if value is None:
        return None
    serving = serving_size_g or Decimal("100")
    portion = portion_g or serving
    return (value * portion / serving * conversion_factor).quantize(Decimal("0.01"))


def _should_escalate(pain_score: int, flare_level: FlareLevel) -> bool:
    flare = getattr(flare_level, "value", flare_level)
    return pain_score >= 8 or flare in {FlareLevel.MODERATE.value, FlareLevel.SEVERE.value}


def _with_escalation_message(log: SymptomLog | None) -> SymptomLog | None:
    if log is not None:
        setattr(log, "escalation_message", ESCALATION_MESSAGE if log.escalation_triggered else None)
    return log
