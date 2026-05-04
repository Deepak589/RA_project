from __future__ import annotations

from decimal import Decimal

from app.models.meal import Meal
from app.services.medication_filter import apply_medication_filter


def _meal(name: str, score: str = "5.0", sodium: str = "100", sugar: str = "2", protein: str = "10", omega3: str = "0") -> Meal:
    return Meal(
        name=name,
        meal_type="lunch",
        anti_inflammatory_score=Decimal(score),
        total_sodium_mg=Decimal(sodium),
        total_sugar_g=Decimal(sugar),
        total_protein_g=Decimal(protein),
        total_omega3_g=Decimal(omega3),
        tags=[],
    )


def test_methotrexate_boosts_spinach_lentil_meals() -> None:
    spinach = _meal("Spinach lentil bowl")
    plain = _meal("Plain rice bowl")

    result = apply_medication_filter([spinach, plain], ["Methotrexate 10mg"])

    assert result.filtered_meals == [spinach, plain]
    assert spinach.adjusted_score > plain.adjusted_score
    assert "methotrexate_friendly" in spinach.medication_tags


def test_nsaids_penalise_high_sodium_meals() -> None:
    salty = _meal("Salty soup", sodium="650")
    lower = _meal("Fresh salad", sodium="80")

    apply_medication_filter([salty, lower], ["Ibuprofen 400mg"])

    assert salty.adjusted_score < lower.adjusted_score


def test_corticosteroids_boost_high_protein_meals() -> None:
    high_protein = _meal("High protein tofu bowl", protein="32")
    low_protein = _meal("Fruit cup", protein="3")

    apply_medication_filter([high_protein, low_protein], ["Prednisone 5mg"])

    assert high_protein.adjusted_score > low_protein.adjusted_score


def test_corticosteroids_penalise_high_sugar_meals() -> None:
    sweet = _meal("Sweet smoothie", sugar="24")
    savory = _meal("Savory bowl", sugar="3")

    apply_medication_filter([sweet, savory], ["Prednisone 5mg"])

    assert sweet.adjusted_score < savory.adjusted_score


def test_no_medications_returns_meals_unchanged() -> None:
    meal = _meal("Simple bowl")

    result = apply_medication_filter([meal], [])

    assert result.filtered_meals == [meal]
    assert result.applied_rules == []


def test_unknown_medication_returns_meals_unchanged_with_verify_log() -> None:
    meal = _meal("Simple bowl")

    result = apply_medication_filter([meal], ["Unknown Drug"])

    assert result.filtered_meals == [meal]
    assert result.applied_rules == ["[VERIFY WITH CLINICIAN] unknown medication has no V1 food rule"]
