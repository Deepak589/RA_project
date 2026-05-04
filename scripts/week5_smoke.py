from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import FlareLevel, RecommendationFeedbackStatus
from app.models.food import Food
from app.models.meal import Meal
from app.models.user import User, UserMedication, UserPreferences
from app.schemas.log import FoodLogCreate, LifestyleLogCreate, SymptomLogCreate
from app.services.dashboard_service import get_today_dashboard
from app.services.log_service import create_food_log, create_lifestyle_log, create_symptom_log
from app.services.recommendation_service import get_next_recommendation, submit_feedback


async def main() -> None:
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"week5-smoke-{int(datetime.now(UTC).timestamp())}@example.com",
            full_name="Week 5 Smoke User",
            password_hash="not-used",
            timezone="UTC",
        )
        db.add(user)
        await db.flush()
        db.add(UserPreferences(user_id=user.id, allergies_jsonb=[], dietary_flags_jsonb=[], goal_flags_jsonb=[]))
        db.add(UserMedication(user_id=user.id, medication_name="Methotrexate 10mg", is_active=True))
        await db.commit()
        await db.refresh(user)

        oats = await db.scalar(select(Food).where(Food.name.ilike("%oat%")).limit(1))
        if oats is None:
            oats = await db.scalar(select(Food).limit(1))
        await create_food_log(
            db,
            user.id,
            FoodLogCreate(food_id=oats.id, meal_type="breakfast", portion_g=Decimal("80"), log_source="manual_log"),
        )

        lunch = await get_next_recommendation(db, user.id, "lunch", flare_active=False)
        await submit_feedback(db, lunch.recommendation_log_id, RecommendationFeedbackStatus.ACCEPTED)

        await create_symptom_log(
            db,
            user.id,
            SymptomLogCreate(pain_score=3, fatigue=4, stiffness_score=0, swelling=False, flare_level=FlareLevel.NONE),
        )
        await create_lifestyle_log(
            db,
            user.id,
            LifestyleLogCreate(log_date=datetime.now(UTC).date(), sleep_hours=Decimal("7.5"), steps=4000, medication_taken=True),
        )
        dashboard = await get_today_dashboard(db, user.id)
        flare_dinner = await get_next_recommendation(db, user.id, "dinner", flare_active=True)

        print("✓ WEEK 5 SMOKE COMPLETE")
        print(f"user_id={user.id}")
        print(f"lunch_primary={lunch.primary_recommendation.name}")
        print(f"lunch_recommendation_log_id={lunch.recommendation_log_id}")
        print(f"dashboard_flare_active={dashboard.flare_active}")
        print(f"dashboard_escalation_active={dashboard.escalation_active}")
        print(f"flare_dinner_primary={flare_dinner.primary_recommendation.name}")
        print(f"flare_dinner_is_flare_friendly={flare_dinner.primary_recommendation.is_flare_friendly}")
        non_flare_after = any(not meal.is_flare_friendly for meal in flare_dinner.alternatives)
        print(f"flare_dinner_non_flare_alternative_present={non_flare_after}")


if __name__ == "__main__":
    asyncio.run(main())
