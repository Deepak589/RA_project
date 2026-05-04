from __future__ import annotations

from decimal import Decimal
from typing import Any

ANTI_INFLAMMATORY_CATEGORIES = {"fish", "legume", "vegetable", "fruit", "nut_seed", "spice"}


def calculate_anti_inflammatory_score(food: Any) -> Decimal:
    score = Decimal("5.0")
    omega3_g = _decimal_attr(food, "omega3_g")
    fiber_g = _decimal_attr(food, "fiber_g")
    protein_g = _decimal_attr(food, "protein_g")
    calcium_mg = _decimal_attr(food, "calcium_mg")
    sugar_g = _decimal_attr(food, "sugar_g")
    saturated_fat_g = _decimal_attr(food, "saturated_fat_g")
    sodium_mg = _decimal_attr(food, "sodium_mg")
    category = str(getattr(food, "category", "") or "").lower()

    if omega3_g >= Decimal("1.0"):
        score += Decimal("2.0")
    elif omega3_g >= Decimal("0.3"):
        score += Decimal("1.0")

    if fiber_g >= Decimal("5.0"):
        score += Decimal("1.5")
    elif fiber_g >= Decimal("2.0"):
        score += Decimal("1.0")
    elif fiber_g >= Decimal("1.0"):
        score += Decimal("0.5")

    if category in ANTI_INFLAMMATORY_CATEGORIES:
        score += Decimal("1.0")

    if protein_g >= Decimal("20.0"):
        score += Decimal("0.5")

    if calcium_mg >= Decimal("200.0"):
        score += Decimal("0.5")

    if sugar_g >= Decimal("20.0"):
        score -= Decimal("2.0")
    elif sugar_g >= Decimal("10.0"):
        score -= Decimal("1.0")

    if saturated_fat_g >= Decimal("10.0"):
        score -= Decimal("1.5")
    elif saturated_fat_g >= Decimal("5.0"):
        score -= Decimal("1.0")

    if sodium_mg >= Decimal("600.0"):
        score -= Decimal("1.0")
    elif sodium_mg >= Decimal("300.0"):
        score -= Decimal("0.5")

    return min(Decimal("10.0"), max(Decimal("0.0"), score)).quantize(Decimal("0.1"))


def _decimal_attr(food: Any, name: str) -> Decimal:
    value = getattr(food, name, Decimal("0.0"))
    if value is None:
        return Decimal("0.0")
    return Decimal(str(value))
