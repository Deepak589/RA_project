from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import FlareLevel
from app.models.food import Food
from app.models.user import User, UserMedication, UserPreferences
from app.schemas.custom_meal import CustomMealCreateRequest, CustomMealIngredientInput
from app.schemas.ingredient import MissingIngredientCreate
from app.schemas.log import FoodLogCreate, SymptomLogCreate
from app.schemas.user import UserPreferencesUpdate
from app.services.custom_meal_service import calculate_custom_meal, create_custom_meal
from app.services.dashboard_service import get_weekly_dashboard
from app.services.ingredient_service import create_missing_ingredient, search_or_flag_ingredient
from app.services.log_service import create_food_log, create_symptom_log
from app.services.profile_service import add_medication, update_preferences
from app.schemas.user import UserMedicationCreateRequest
from app.services.recommendation_service import get_next_recommendation


def _food_query(name: str):
    return select(Food).where(Food.name.ilike(f"%{name}%")).limit(1)


async def main() -> None:
    output: dict[str, object] = {"steps": []}
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    async with AsyncSessionLocal() as db:
        user = User(
            email=f"week6-smoke-{timestamp}@example.com",
            full_name="Week 6 Smoke User",
            password_hash="not-used",
            timezone="UTC",
        )
        db.add(user)
        await db.flush()
        db.add(UserPreferences(user_id=user.id))
        await db.commit()
        await db.refresh(user)
        output["user_id"] = str(user.id)
        output["steps"].append("registered user with preferences")

        await update_preferences(
            db,
            user.id,
            UserPreferencesUpdate(dietary_flags=["vegetarian"], allergies=[], goals=["reduce_inflammation"]),
        )
        await add_medication(db, user.id, UserMedicationCreateRequest(medication_name="Methotrexate 10mg"))
        output["steps"].append("set preferences and medication")

        spinach_search = await search_or_flag_ingredient(db, user.id, "spinach")
        output["spinach_found"] = spinach_search.found
        await search_or_flag_ingredient(db, user.id, "dragonfruit")
        dragonfruit = await create_missing_ingredient(db, user.id, MissingIngredientCreate(ingredient_name="dragonfruit"))
        papaya = await create_missing_ingredient(
            db,
            user.id,
            MissingIngredientCreate(
                ingredient_name="papaya",
                submitted_calories=Decimal("43"),
                submitted_protein_g=Decimal("0.5"),
                submitted_fiber_g=Decimal("1.7"),
            ),
        )
        output["missing_statuses"] = {"dragonfruit": dragonfruit.status, "papaya": papaya.status}

        chicken = await db.scalar(_food_query("chicken")) or await db.scalar(select(Food).limit(1))
        spinach = await db.scalar(_food_query("spinach")) or await db.scalar(select(Food).offset(1).limit(1))
        olive_oil = await db.scalar(_food_query("olive oil")) or await db.scalar(select(Food).offset(2).limit(1))
        ingredients = [
            CustomMealIngredientInput(food_id=chicken.id, portion_g=Decimal("150")),
            CustomMealIngredientInput(food_id=spinach.id, portion_g=Decimal("80")),
            CustomMealIngredientInput(food_id=olive_oil.id, portion_g=Decimal("10")),
        ]
        preview = await calculate_custom_meal(db, ingredients)
        custom_meal = await create_custom_meal(
            db,
            user.id,
            CustomMealCreateRequest(
                name="My protein lunch",
                meal_type="lunch",
                ingredients=ingredients,
                missing_ingredient_names=[],
            ),
        )
        output["custom_meal"] = {
            "preview_calories": preview.total_calories,
            "saved_id": str(custom_meal.id),
            "score": float(custom_meal.anti_inflammatory_score or 0),
        }
        await create_food_log(
            db,
            user.id,
            FoodLogCreate(custom_meal_id=custom_meal.id, meal_type="lunch", portion_g=Decimal("1"), log_source="custom_meal"),
        )

        await create_symptom_log(db, user.id, SymptomLogCreate(pain_score=7, fatigue=4, stiffness_score=3, swelling=False, flare_level=FlareLevel.MODERATE))
        flare = await get_next_recommendation(db, user.id, "dinner")
        output["flare_only"] = {
            "mode": flare.recommendation_mode,
            "all_flare_friendly": all(meal.is_flare_friendly for meal in [flare.primary_recommendation, *flare.alternatives]),
        }

        await create_symptom_log(db, user.id, SymptomLogCreate(pain_score=4, fatigue=3, stiffness_score=2, swelling=False, flare_level=FlareLevel.MILD))
        mixed = await get_next_recommendation(db, user.id, "lunch")
        mixed_meals = [mixed.primary_recommendation, *mixed.alternatives]
        output["mixed"] = {
            "mode": mixed.recommendation_mode,
            "first_two_flare": [meal.is_flare_friendly for meal in mixed_meals[:2]],
        }

        await create_symptom_log(db, user.id, SymptomLogCreate(pain_score=2, fatigue=2, stiffness_score=1, swelling=False, flare_level=FlareLevel.NONE))
        normal = await get_next_recommendation(db, user.id, "breakfast")
        output["normal"] = {"mode": normal.recommendation_mode}
        dashboard = await get_weekly_dashboard(db, user.id)
        output["weekly_dashboard_present"] = dashboard is not None

    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    output_path = logs_dir / f"week6_smoke_{timestamp}.json"
    output_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"✓ WEEK 6 SMOKE COMPLETE: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
