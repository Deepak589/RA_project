from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import delete, select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401  # Register ORM models before mapper configuration.
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score
from app.services.food_normalizer import normalize_usda_food

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
DATA_TYPE_PRIORITY = ("Foundation", "SR Legacy")

FISH_TERMS = [
    "tuna cooked",
    "tuna canned in water",
    "sardines canned in oil",
    "mackerel cooked",
    "cod cooked",
    "trout cooked",
    "herring cooked",
]
FISH_KEYWORDS = ("tuna", "sardine", "mackerel", "cod", "trout", "herring")
BAD_EXTERNAL_IDS = ("2685582", "749420", "326196", "746779")


async def main() -> None:
    report: dict[str, Any] = {"started_at": _now_iso(), "terms": [], "foods": []}
    async with httpx.AsyncClient(timeout=30) as client:
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(Food).where(
                    Food.external_source == "usda",
                    Food.external_id.in_(BAD_EXTERNAL_IDS),
                )
            )
            await db.commit()

            for term in FISH_TERMS:
                foods, data_type = await fetch_fish_candidates(client, term)
                report["terms"].append({"term": term, "data_type": data_type, "result_count": len(foods)})
                inserted_for_term = False

                for raw_food in foods:
                    if not is_target_fish(raw_food, term):
                        report["foods"].append(
                            {
                                "term": term,
                                "external_id": str(raw_food.get("fdcId", "")),
                                "name": raw_food.get("description"),
                                "status": "skipped_non_fish_match",
                            }
                        )
                        continue

                    normalized = normalize_usda_food(raw_food)
                    normalized.category = "fish"
                    normalized.anti_inflammatory_score = calculate_anti_inflammatory_score(normalized)

                    existing = await db.scalar(
                        select(Food).where(
                            Food.external_source == normalized.external_source,
                            Food.external_id == normalized.external_id,
                        )
                    )
                    if existing:
                        report["foods"].append(
                            {
                                "term": term,
                                "external_id": normalized.external_id,
                                "name": normalized.name,
                                "status": "skipped_duplicate",
                            }
                        )
                        continue

                    food = Food(**normalized.model_dump())
                    food.cooking_state = "ready_to_eat" if "canned" in term else "cooked"
                    food.conversion_factor = Decimal("1.000")
                    food.display_note = "Fish nutrients are stored per 100g edible cooked or ready-to-eat portion."
                    db.add(food)
                    await db.flush()
                    await db.commit()

                    inserted_for_term = True
                    print(f"INSERT: {food.name} | omega3={food.omega3_g} | score={food.anti_inflammatory_score}")
                    report["foods"].append(
                        {
                            "term": term,
                            "data_type": data_type,
                            "external_id": food.external_id,
                            "name": food.name,
                            "omega3_g": _json_decimal(food.omega3_g),
                            "anti_inflammatory_score": _json_decimal(food.anti_inflammatory_score),
                            "status": "inserted",
                        }
                    )
                    break

                if not inserted_for_term:
                    print(f"[SKIP: no new fish inserted for {term}]")

    report["finished_at"] = _now_iso()
    path = save_report(report)
    print(f"Report saved: {path}")


async def fetch_fish_candidates(client: httpx.AsyncClient, term: str) -> tuple[list[dict[str, Any]], str | None]:
    for data_type in DATA_TYPE_PRIORITY:
        response = await client.get(
            USDA_SEARCH_URL,
            params={
                "query": term,
                "dataType": data_type,
                "pageSize": 10,
                "api_key": settings.usda_api_key,
            },
        )
        response.raise_for_status()
        foods = response.json().get("foods", [])
        filtered_foods = [food for food in foods if is_target_fish(food, term)]
        if filtered_foods:
            return filtered_foods, data_type
    return [], None


def is_target_fish(raw_food: dict[str, Any], term: str) -> bool:
    description = str(raw_food.get("description") or "").lower()
    category = str(raw_food.get("foodCategory") or "").lower()
    requested_keyword = next((keyword for keyword in FISH_KEYWORDS if keyword in term), "")
    if requested_keyword and requested_keyword not in description:
        return False
    if any(keyword in description for keyword in FISH_KEYWORDS):
        return True
    return any(token in category for token in ("fish", "seafood", "shellfish"))


def save_report(report: dict[str, Any]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"additional_fish_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def _json_decimal(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
