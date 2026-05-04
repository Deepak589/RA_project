from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import AsyncSessionLocal
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score

DRY_DISPLAY_NOTE = (
    "Values are per 100g DRY. When cooked, 100g dry expands to ~280g cooked. "
    "Log the cooked weight you actually ate."
)

OVERRIDES: list[dict[str, Any]] = [
    {
        "pattern": "%Oil, olive, extra virgin%",
        "values": {
            "calories": Decimal("884"),
            "fat_g": Decimal("100.0"),
            "saturated_fat_g": Decimal("13.8"),
            "omega3_g": Decimal("0.761"),
            "sodium_mg": Decimal("2.0"),
            "cooking_state": "ready_to_eat",
            "conversion_factor": Decimal("1.0"),
            "quality_flag": "manually_verified",
            "manual_override": True,
            "display_note": None,
        },
    },
    {
        "pattern": "%Oil, olive, extra light%",
        "values": {
            "calories": Decimal("884"),
            "fat_g": Decimal("100.0"),
            "saturated_fat_g": Decimal("13.4"),
            "omega3_g": Decimal("0.700"),
            "sodium_mg": Decimal("2.0"),
            "cooking_state": "ready_to_eat",
            "conversion_factor": Decimal("1.0"),
            "quality_flag": "manually_verified",
            "manual_override": True,
            "display_note": None,
        },
    },
    {
        "pattern": "%Beans, Dry, Brown%",
        "values": {
            "calories": Decimal("341"),
            "protein_g": Decimal("21.4"),
            "carbs_g": Decimal("60.1"),
            "fiber_g": Decimal("15.2"),
            "fat_g": Decimal("1.27"),
            "sugar_g": Decimal("2.1"),
            "sodium_mg": Decimal("5.0"),
            "cooking_state": "raw",
            "conversion_factor": Decimal("2.8"),
            "quality_flag": "manually_verified",
            "manual_override": True,
            "display_note": DRY_DISPLAY_NOTE,
        },
    },
    {
        "pattern": "%Beans, Dry, Dark Red Kidney%",
        "values": {
            "calories": Decimal("333"),
            "protein_g": Decimal("23.6"),
            "carbs_g": Decimal("53.3"),
            "fiber_g": Decimal("24.9"),
            "fat_g": Decimal("1.06"),
            "sugar_g": Decimal("3.3"),
            "sodium_mg": Decimal("5.0"),
            "cooking_state": "raw",
            "conversion_factor": Decimal("2.8"),
            "quality_flag": "manually_verified",
            "manual_override": True,
            "display_note": DRY_DISPLAY_NOTE,
        },
    },
    {
        "pattern": "%Beans, Dry, Light Red Kidney%",
        "values": {
            "calories": Decimal("325"),
            "protein_g": Decimal("22.8"),
            "carbs_g": Decimal("55.2"),
            "fiber_g": Decimal("20.0"),
            "fat_g": Decimal("1.10"),
            "sugar_g": Decimal("2.9"),
            "sodium_mg": Decimal("5.0"),
            "cooking_state": "raw",
            "conversion_factor": Decimal("2.8"),
            "quality_flag": "manually_verified",
            "manual_override": True,
            "display_note": DRY_DISPLAY_NOTE,
        },
    },
]

SELECT_SQL = text(
    """
    SELECT id, name, calories, protein_g, carbs_g, fat_g, saturated_fat_g,
           fiber_g, sugar_g, sodium_mg, omega3_g, calcium_mg, category,
           anti_inflammatory_score, cooking_state, conversion_factor,
           display_note, quality_flag, manual_override
    FROM static.foods
    WHERE name ILIKE :pattern
    ORDER BY name
    LIMIT 1
    """
)

UPDATE_SQL = text(
    """
    UPDATE static.foods
    SET calories = :calories,
        protein_g = COALESCE(:protein_g, protein_g),
        carbs_g = COALESCE(:carbs_g, carbs_g),
        fat_g = :fat_g,
        saturated_fat_g = COALESCE(:saturated_fat_g, saturated_fat_g),
        fiber_g = COALESCE(:fiber_g, fiber_g),
        sugar_g = COALESCE(:sugar_g, sugar_g),
        sodium_mg = :sodium_mg,
        omega3_g = COALESCE(:omega3_g, omega3_g),
        anti_inflammatory_score = :anti_inflammatory_score,
        cooking_state = :cooking_state,
        conversion_factor = :conversion_factor,
        display_note = :display_note,
        quality_flag = :quality_flag,
        manual_override = :manual_override,
        updated_at = NOW()
    WHERE id = :id
    RETURNING name, calories, protein_g, carbs_g, fat_g, saturated_fat_g,
              fiber_g, sugar_g, sodium_mg, omega3_g, anti_inflammatory_score,
              cooking_state, conversion_factor, display_note, quality_flag,
              manual_override
    """
)


async def main() -> None:
    report: dict[str, Any] = {"started_at": _now_iso(), "updates": [], "missing": []}
    async with AsyncSessionLocal() as db:
        for override in OVERRIDES:
            row = (await db.execute(SELECT_SQL, {"pattern": override["pattern"]})).mappings().first()
            if row is None:
                message = f"[MISSING FOOD: {override['pattern']}]"
                print(message)
                report["missing"].append(message)
                continue

            before = dict(row)
            values = dict(override["values"])
            score_input = SimpleNamespace(**{**before, **values})
            values["anti_inflammatory_score"] = calculate_anti_inflammatory_score(score_input)
            updated = (
                await db.execute(
                    UPDATE_SQL,
                    {
                        "id": before["id"],
                        "protein_g": None,
                        "carbs_g": None,
                        "fiber_g": None,
                        "sugar_g": None,
                        "saturated_fat_g": None,
                        "omega3_g": None,
                        **values,
                    },
                )
            ).mappings().one()
            await db.commit()
            after = dict(updated)
            print(f"UPDATED: {before['name']}")
            for field, value in values.items():
                print(f"  {field}: {before.get(field)} -> {value}")
            report["updates"].append({"name": before["name"], "before": _jsonable(before), "after": _jsonable(after)})

    report["finished_at"] = _now_iso()
    path = _save_report(report)
    print(f"Report saved: {path}")


def _save_report(report: dict[str, Any]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"manual_override_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    return str(value) if not isinstance(value, (str, int, float, bool, type(None))) else value


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
