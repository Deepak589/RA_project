from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FlareLevel, RecommendationFeedbackStatus
from app.models.log import FoodLog, LifestyleLog, SymptomLog
from app.models.recommendation import RecommendationLog
from app.models.user import User
from app.services.log_service import ESCALATION_MESSAGE, get_todays_lifestyle_log, get_todays_symptom_log
from app.services.nutrition_tracker import DailyNutritionState, get_nutrition_gaps, get_todays_nutrition, summarize_food_logs
from app.services.recommendation_service import get_next_recommendation
from app.services.rule_engine import RecommendationResult


@dataclass
class TodayDashboard:
    date: date
    nutrition: DailyNutritionState
    symptom_log: SymptomLog | None
    lifestyle_log: LifestyleLog | None
    next_recommendation: RecommendationResult | None
    flare_active: bool
    escalation_active: bool
    escalation_message: str | None


@dataclass
class WeeklyDashboard:
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
    pain_trend: list[dict]


async def get_today_dashboard(
    db: AsyncSession,
    user_id: UUID,
    diet_override: str | None = None,
    meal_type: str | None = None,
) -> TodayDashboard:
    symptom = await get_todays_symptom_log(db, user_id)
    lifestyle = await get_todays_lifestyle_log(db, user_id)
    nutrition = await get_todays_nutrition(db, user_id)
    user_tz = await db.scalar(select(User.timezone).where(User.id == user_id))
    flare_active = symptom is not None and symptom.flare_level in {FlareLevel.MODERATE, FlareLevel.SEVERE}
    escalation_active = symptom is not None and (symptom.pain_score >= 8 or symptom.flare_level == FlareLevel.SEVERE)
    recommendation = await get_next_recommendation(
        db,
        user_id=user_id,
        meal_type=meal_type if meal_type else detect_meal_type_by_time(user_tz=user_tz),
        flare_active=flare_active,
        diet_override=diet_override,
    )
    return TodayDashboard(
        date=datetime.now(timezone.utc).date(),
        nutrition=nutrition,
        symptom_log=symptom,
        lifestyle_log=lifestyle,
        next_recommendation=recommendation,
        flare_active=flare_active,
        escalation_active=escalation_active,
        escalation_message=ESCALATION_MESSAGE if escalation_active else None,
    )


async def get_weekly_dashboard(db: AsyncSession, user_id: UUID, week_offset: int = 0) -> WeeklyDashboard:
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end = week_start + timedelta(days=6)
    start_dt = datetime.combine(week_start, time.min)
    end_dt = datetime.combine(week_end, time.max)

    symptoms = list(
        await db.scalars(
            select(SymptomLog).where(SymptomLog.user_id == user_id, SymptomLog.logged_at >= start_dt, SymptomLog.logged_at <= end_dt)
        )
    )
    lifestyles = list(await db.scalars(select(LifestyleLog).where(LifestyleLog.user_id == user_id, LifestyleLog.log_date.between(week_start, week_end))))
    food_logs = list(
        await db.scalars(
            select(FoodLog)
            .where(FoodLog.user_id == user_id, FoodLog.logged_at >= start_dt, FoodLog.logged_at <= end_dt)
            .options(
                selectinload(FoodLog.food),
                selectinload(FoodLog.meal),
                selectinload(FoodLog.recommendation_meal),
                selectinload(FoodLog.custom_meal),
            )
        )
    )
    total_meals = len(food_logs)
    meal_logged_days = len({log.logged_at.date() for log in food_logs if log.logged_at is not None})
    recs = list(
        await db.scalars(
            select(RecommendationLog).where(RecommendationLog.user_id == user_id, RecommendationLog.shown_at >= start_dt, RecommendationLog.shown_at <= end_dt)
        )
    )
    decided = [rec for rec in recs if rec.feedback_status != RecommendationFeedbackStatus.PENDING]
    accepted = sum(1 for rec in decided if rec.feedback_status == RecommendationFeedbackStatus.ACCEPTED)
    acceptance = round((accepted / len(decided)) * 100, 1) if decided else 0.0
    avg_pain = _avg([log.pain_score for log in symptoms])
    worst = max(symptoms, key=lambda log: log.pain_score, default=None)
    best = min(symptoms, key=lambda log: log.pain_score, default=None)
    pain_trend = [
        {"date": log.logged_at.date().strftime("%a"), "pain_score": log.pain_score}
        for log in sorted(symptoms, key=lambda s: s.logged_at)
    ]
    insights = generate_weekly_insights(food_logs, symptoms)
    return WeeklyDashboard(
        week_start=week_start,
        week_end=week_end,
        avg_pain_score=avg_pain,
        avg_fatigue=_avg([log.fatigue_score for log in symptoms]),
        avg_sleep_hours=_avg([float(log.sleep_hours) for log in lifestyles if log.sleep_hours is not None]),
        avg_meal_quality_score=None,
        total_meals_logged=total_meals,
        meal_logged_days=meal_logged_days,
        recommendation_acceptance_rate=acceptance,
        flare_days_count=sum(1 for log in symptoms if log.flare_level in {FlareLevel.MODERATE, FlareLevel.SEVERE}),
        best_day=best.logged_at.date() if best else None,
        worst_day=worst.logged_at.date() if worst else None,
        insights=insights,
        pain_trend=pain_trend,
    )


def detect_meal_type_by_time(moment: datetime | None = None, user_tz: str | None = None) -> str:
    base = moment or datetime.now(timezone.utc)
    if user_tz:
        try:
            base = base.astimezone(ZoneInfo(user_tz))
        except ZoneInfoNotFoundError:
            pass
    hour = base.hour
    if hour < 10:
        return "breakfast"
    if hour < 14:
        return "lunch"
    if hour < 18:
        return "snack"
    return "dinner"


def generate_weekly_insights(food_logs: list[FoodLog], symptoms: list[SymptomLog]) -> list[str]:
    insights: list[str] = []
    days_with_food = len({log.logged_at.date() for log in food_logs if log.logged_at is not None})
    if days_with_food > 0:
        weekly_nutrition = summarize_food_logs(food_logs)
        avg_daily_sugar = weekly_nutrition.sugar_consumed / days_with_food
        avg_daily_fiber = weekly_nutrition.fiber_consumed / days_with_food
        if avg_daily_sugar > 30:
            insights.append("Average daily sugar was above target this week — high-sugar days often correlate with next-day symptom flares.")
        if avg_daily_fiber < 25:
            insights.append("Average daily fiber was below target this week — aim for more vegetables, legumes, and whole grains.")
    if symptoms:
        pain_scores = [log.pain_score for log in symptoms]
        avg_pain = sum(pain_scores) / len(pain_scores)
        if avg_pain >= 6:
            insights.append(f"Average pain this week was {avg_pain:.1f}/10 — consider logging lifestyle factors to find patterns.")
        flare_days = sum(1 for log in symptoms if log.flare_level in {FlareLevel.MODERATE, FlareLevel.SEVERE})
        if flare_days >= 3:
            insights.append(f"{flare_days} flare days logged this week — review recent meals and sleep for common triggers.")
    if not insights:
        insights.append("Keep logging meals and symptoms — patterns become visible after a full week of data.")
    return insights[:4]


def _avg(values: list[float | int]) -> float | None:
    if not values:
        return None
    return round(sum(float(value) for value in values) / len(values), 2)
