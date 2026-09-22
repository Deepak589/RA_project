from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401  # Register all ORM models before mapper configuration.
from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score


async def rescore_foods() -> Path:
    report: dict[str, object] = {
        "mode": "rescore-foods",
        "started_at": _now_iso(),
        "foods": [],
    }

    async with AsyncSessionLocal() as db:
        foods = list(await db.scalars(select(Food).order_by(Food.name)))
        for food in foods:
            old_score = Decimal(str(food.anti_inflammatory_score or Decimal("0.0")))
            new_score = calculate_anti_inflammatory_score(food)
            difference = new_score - old_score
            food.anti_inflammatory_score = new_score
            food.updated_at = datetime.utcnow()
            print(f"RESCORE: {food.name} | old={old_score} | new={new_score} | diff={difference}")
            report["foods"].append(
                {
                    "id": str(food.id),
                    "name": food.name,
                    "old_score": _json_decimal(old_score),
                    "new_score": _json_decimal(new_score),
                    "difference": _json_decimal(difference),
                }
            )

        await db.commit()

    report["finished_at"] = _now_iso()
    report["food_count"] = len(report["foods"])
    return _save_report(report)


def _save_report(report: dict[str, object]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"rescore_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def _json_decimal(value: Decimal) -> float:
    return float(value)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def main() -> None:
    path = await rescore_foods()
    print(f"Report saved: {path}")


if __name__ == "__main__":
    asyncio.run(main())
