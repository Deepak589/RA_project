from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import AsyncSessionLocal

SELECT_SQL = text(
    """
    SELECT id, name, category, protein_g, cooking_state, conversion_factor, display_note
    FROM static.foods
    ORDER BY name
    """
)

UPDATE_SQL = text(
    """
    UPDATE static.foods
    SET cooking_state = :cooking_state,
        conversion_factor = :conversion_factor,
        display_note = :display_note,
        updated_at = NOW()
    WHERE id = :id
    """
)


async def main() -> None:
    report: dict[str, Any] = {"started_at": _now_iso(), "updates": []}
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(SELECT_SQL)).mappings().all()
        for row in rows:
            state = _state_for(row["name"])
            factor = _factor_for(row["name"], row["category"], state)
            note = _display_note(row["name"], row["category"], Decimal(str(row["protein_g"] or 0)), state, factor)
            await db.execute(
                UPDATE_SQL,
                {
                    "id": row["id"],
                    "cooking_state": state,
                    "conversion_factor": factor,
                    "display_note": note,
                },
            )
            print(f"COOKING STATE: {row['name']} | {row['cooking_state']} -> {state} | factor={factor}")
            report["updates"].append(
                {
                    "name": row["name"],
                    "old_cooking_state": row["cooking_state"],
                    "new_cooking_state": state,
                    "old_conversion_factor": _json_decimal(row["conversion_factor"]),
                    "new_conversion_factor": _json_decimal(factor),
                    "display_note": note,
                }
            )
        await db.commit()

    report["finished_at"] = _now_iso()
    path = _save_report(report)
    print(f"Report saved: {path}")


def _state_for(name: str) -> str:
    text_name = name.lower()
    if any(token in text_name for token in ("cooked", "braised", "boiled")):
        return "cooked"
    if "raw" in text_name or "dry" in text_name:
        return "raw"
    if any(token in text_name for token in ("canned", "oil", "yogurt", "blueberr", "avocado", "spice", "walnut")):
        return "ready_to_eat"
    if any(token in text_name for token in ("egg", "tofu", "mayonnaise", "cherries", "anchovies", "ginger ale")):
        return "ready_to_eat"
    if any(token in text_name for token in ("flour", "rice", "oat", "quinoa")):
        return "raw"
    if any(token in text_name for token in ("spinach", "broccoli", "garlic", "ginger root", "sweet potato")):
        return "raw"
    return "ready_to_eat"


def _factor_for(name: str, category: str | None, state: str) -> Decimal:
    if state in {"cooked", "ready_to_eat"}:
        return Decimal("1.000")
    text_name = name.lower()
    category_name = (category or "").lower()
    if category_name == "fish" or any(token in text_name for token in ("salmon", "tuna", "cod", "trout", "herring", "mackerel")):
        return Decimal("1.250")
    if category_name == "protein" or any(token in text_name for token in ("chicken", "beef")):
        return Decimal("1.350")
    if category_name == "vegetable":
        return Decimal("0.850")
    if category_name == "grain":
        return Decimal("2.500")
    if category_name == "legume":
        return Decimal("2.800")
    return Decimal("1.000")


def _display_note(name: str, category: str | None, protein_g: Decimal, state: str, factor: Decimal) -> str | None:
    category_name = (category or "").lower()
    if state in {"cooked", "ready_to_eat"}:
        return None
    if category_name in {"protein", "fish"}:
        cooked_protein = protein_g * factor
        return (
            f"Values are per 100g RAW. When cooked, protein increases to ~{cooked_protein:.1f}g per 100g "
            "as water is lost. Log your cooked portion."
        )
    if category_name in {"grain", "legume"}:
        cooked_weight = Decimal("100") * factor
        return (
            f"Values are per 100g DRY. When cooked, 100g dry expands to ~{cooked_weight:.0f}g cooked. "
            "Log the cooked weight you actually ate."
        )
    if category_name == "vegetable":
        return "Values are per 100g RAW. Cooking slightly concentrates nutrients. Log cooked weight for best accuracy."
    return None


def _save_report(report: dict[str, Any]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"cooking_states_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def _json_decimal(value: Any) -> float:
    return float(value or Decimal("0"))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
