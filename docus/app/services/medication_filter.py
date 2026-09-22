from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import Meal
from app.models.user import UserMedication


@dataclass
class MedicationFilterResult:
    filtered_meals: list[Meal]
    applied_rules: list[str] = field(default_factory=list)
    flagged_meals: list[str] = field(default_factory=list)


async def get_user_medications(db: AsyncSession, user_id: UUID) -> list[str]:
    result = await db.scalars(
        select(UserMedication.medication_name).where(UserMedication.user_id == user_id, UserMedication.is_active.is_(True))
    )
    return list(result)


def apply_medication_filter(meals: list[Meal], medications: list[str]) -> MedicationFilterResult:
    if not medications:
        return MedicationFilterResult(filtered_meals=meals)

    lowered = [medication.lower() for medication in medications]
    applied_rules: list[str] = []
    flagged_meals: list[str] = []

    for meal in meals:
        setattr(meal, "adjusted_score", _current_score(meal))

    if any("methotrexate" in medication for medication in lowered):
        applied_rules.append("methotrexate_folate_support")
        for meal in meals:
            if _meal_has_any(meal, {"spinach", "lentil", "bean", "beans", "avocado"}):
                _bump(meal, 0.8)
                tags = list(getattr(meal, "medication_tags", []) or [])
                if "methotrexate_friendly" not in tags:
                    tags.append("methotrexate_friendly")
                    setattr(meal, "medication_tags", tags)
            if _meal_has_any(meal, {"wine", "beer", "alcohol"}):
                flagged_meals.append(meal.name)

    if any("ibuprofen" in medication or "naproxen" in medication for medication in lowered):
        applied_rules.append("nsaid_sodium_and_omega3")
        for meal in meals:
            if _number(meal, "total_sodium_mg", "sodium_mg") > 400:
                _bump(meal, -0.8)
            if _number(meal, "total_omega3_g") >= 0.5:
                _bump(meal, 0.7)

    if any("prednisone" in medication or "corticosteroid" in medication for medication in lowered):
        applied_rules.append("corticosteroid_calcium_protein_sugar")
        for meal in meals:
            if _number(meal, "total_protein_g", "protein_g") >= 25:
                _bump(meal, 0.6)
            if _meal_has_any(meal, {"yogurt", "milk", "tofu", "sardine", "salmon", "kale"}):
                _bump(meal, 0.6)
            if _number(meal, "total_sugar_g", "sugar_g") >= 15:
                _bump(meal, -1.0)

    # [VERIFY WITH CLINICIAN] Biologics have no specific V1 food filter; user should verify individual guidance.
    if any("adalimumab" in medication or "etanercept" in medication for medication in lowered):
        applied_rules.append("biologic_no_specific_v1_food_rule")

    known = ("methotrexate", "ibuprofen", "naproxen", "prednisone", "corticosteroid", "adalimumab", "etanercept")
    if not any(any(marker in medication for marker in known) for medication in lowered):
        applied_rules.append("[VERIFY WITH CLINICIAN] unknown medication has no V1 food rule")

    return MedicationFilterResult(filtered_meals=meals, applied_rules=applied_rules, flagged_meals=flagged_meals)


def _meal_has_any(meal: Meal, needles: set[str]) -> bool:
    haystack = " ".join(
        [
            meal.name or "",
            meal.description or "",
            " ".join(getattr(meal, "tags", []) or []),
            " ".join(getattr(meal, "dietary_tags_jsonb", []) or []),
            " ".join(getattr(meal, "reason_tags_jsonb", []) or []),
        ]
    ).lower()
    for ingredient in getattr(meal, "ingredients", []) or []:
        food = getattr(ingredient, "food", None)
        haystack += f" {getattr(food, 'name', '')}".lower()
    return any(needle in haystack for needle in needles)


def _current_score(meal: Meal) -> float:
    return float(getattr(meal, "adjusted_score", meal.anti_inflammatory_score or 0))


def _bump(meal: Meal, delta: float) -> None:
    setattr(meal, "adjusted_score", max(0.0, min(10.0, _current_score(meal) + delta)))


def _number(meal: Meal, *names: str) -> float:
    for name in names:
        value = getattr(meal, name, None)
        if value is not None:
            return float(value)
    return 0.0
