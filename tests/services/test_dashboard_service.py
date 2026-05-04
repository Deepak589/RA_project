from __future__ import annotations

from datetime import UTC, datetime

from app.services.dashboard_service import detect_meal_type_by_time


def test_meal_type_detected_correctly_by_time_of_day() -> None:
    assert detect_meal_type_by_time(datetime(2026, 4, 22, 8, tzinfo=UTC)) == "breakfast"
    assert detect_meal_type_by_time(datetime(2026, 4, 22, 12, tzinfo=UTC)) == "lunch"
    assert detect_meal_type_by_time(datetime(2026, 4, 22, 16, tzinfo=UTC)) == "snack"
    assert detect_meal_type_by_time(datetime(2026, 4, 22, 19, tzinfo=UTC)) == "dinner"
