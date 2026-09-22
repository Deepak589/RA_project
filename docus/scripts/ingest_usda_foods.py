from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.db.base  # noqa: F401  # Register all ORM models before mapper configuration.
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.food import Food
from app.services.anti_inflammatory_scorer import calculate_anti_inflammatory_score
from app.services.food_normalizer import normalize_usda_food

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_DATA_TYPE_PRIORITY = ("Foundation", "SR Legacy")
DEFAULT_TERMS = [
    "chicken",
    "salmon",
    "spinach",
    "lentils",
    "brown rice",
    "oats",
    "walnuts",
    "olive oil",
    "sweet potato",
    "blueberries",
    "kidney beans",
    "tofu",
    "Greek yogurt",
    "eggs",
    "broccoli",
    "quinoa",
    "avocado",
    "garlic",
    "turmeric",
    "ginger",
]
DRY_RUN_TERMS = ["chicken breast cooked", "salmon"]


async def fetch_foods(
    client: httpx.AsyncClient,
    term: str,
    retries: int = 3,
    data_type_override: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    data_types = (data_type_override,) if data_type_override else USDA_DATA_TYPE_PRIORITY
    for data_type in data_types:
        foods = await _fetch_foods_by_data_type(client, term, data_type, retries=retries)
        if foods:
            return foods, data_type
        print(f"[DATA ISSUE: no {data_type} results for {term}]")
    print(f"[DATA ISSUE: no results for {term}]")
    return [], None


async def _fetch_foods_by_data_type(
    client: httpx.AsyncClient,
    term: str,
    data_type: str,
    retries: int = 3,
) -> list[dict[str, Any]]:
    for attempt in range(retries):
        try:
            response = await client.get(
                USDA_SEARCH_URL,
                params={
                    "query": term,
                    "dataType": data_type,
                    "pageSize": 3,
                    "api_key": settings.usda_api_key,
                },
            )
            if response.status_code == 429:
                await asyncio.sleep(2**attempt)
                continue
            response.raise_for_status()
            return response.json().get("foods", [])
        except httpx.HTTPError as exc:
            if attempt == retries - 1:
                print(f"[DATA ISSUE: USDA API error for {term} ({data_type})] {exc}")
                return []
            await asyncio.sleep(2**attempt)
    return []


async def dry_run() -> dict[str, Any]:
    report: dict[str, Any] = {"mode": "dry-run", "terms": [], "foods": []}
    async with httpx.AsyncClient(timeout=30) as client:
        for term in DRY_RUN_TERMS:
            foods, data_type = await fetch_foods(client, term)
            report["terms"].append({"term": term, "data_type": data_type, "result_count": len(foods)})
            for raw_food in foods[:1]:
                try:
                    normalized = normalize_usda_food(raw_food)
                    normalized.anti_inflammatory_score = calculate_anti_inflammatory_score(normalized)
                    output = normalized.model_dump(mode="json")
                    report["foods"].append(output)
                    print(json.dumps(output, indent=2))
                except Exception as exc:
                    issue = f"[DATA ISSUE: failed to normalize {term}] {exc}"
                    print(issue)
                    report["foods"].append({"term": term, "error": issue})
    return report


async def full_run(terms: list[str], data_type_override: str | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": "full-run", "started_at": _now_iso(), "terms": [], "foods": []}
    async with httpx.AsyncClient(timeout=30) as client:
        async with AsyncSessionLocal() as db:
            for term in terms:
                foods, data_type = await fetch_foods(client, term, data_type_override=data_type_override)
                report["terms"].append({"term": term, "data_type": data_type, "result_count": len(foods)})
                for raw_food in foods:
                    try:
                        normalized = normalize_usda_food(raw_food)
                        normalized.anti_inflammatory_score = calculate_anti_inflammatory_score(normalized)
                        existing = await db.scalar(
                            select(Food).where(
                                Food.external_source == normalized.external_source,
                                Food.external_id == normalized.external_id,
                            )
                        )
                        if existing:
                            message = f"[SKIP: duplicate {normalized.external_id}]"
                            print(message)
                            report["foods"].append(
                                {
                                    "term": term,
                                    "data_type": data_type,
                                    "external_id": normalized.external_id,
                                    "name": normalized.name,
                                    "status": "skipped_duplicate",
                                }
                            )
                            continue

                        food = Food(**normalized.model_dump())
                        db.add(food)
                        await db.flush()
                        await db.commit()
                        print(
                            f"INSERT: {food.name} | calories={food.calories} | "
                            f"protein={food.protein_g} | fiber={food.fiber_g} | score={food.anti_inflammatory_score}"
                        )
                        report["foods"].append(
                            {
                                "term": term,
                                "data_type": data_type,
                                "external_id": food.external_id,
                                "name": food.name,
                                "category": food.category,
                                "anti_inflammatory_score": _json_decimal(food.anti_inflammatory_score),
                                "status": "inserted",
                            }
                        )
                    except Exception as exc:
                        await db.rollback()
                        issue = f"[DATA ISSUE: failed to ingest {term}] {exc}"
                        print(issue)
                        report["foods"].append({"term": term, "status": "error", "error": issue})
    report["finished_at"] = _now_iso()
    return report


def save_report(report: dict[str, Any]) -> Path:
    Path("logs").mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path("logs") / f"usda_ingest_{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest USDA foods into static.foods.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Fetch and normalize sample foods without DB writes.")
    mode.add_argument("--full-run", action="store_true", help="Fetch and insert the full Week 3 search term list.")
    parser.add_argument("--term", action="append", dest="terms", help="Override full-run terms. Can be passed more than once.")
    parser.add_argument("--data-type", choices=USDA_DATA_TYPE_PRIORITY, help="Force one USDA dataType for targeted ingestion.")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.full_run:
        terms = args.terms or DEFAULT_TERMS
        report = await full_run(terms, data_type_override=args.data_type)
    else:
        report = await dry_run()
    path = save_report(report)
    print(f"Report saved: {path}")


def _json_decimal(value: Decimal | None) -> float:
    return float(value or Decimal("0"))


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    asyncio.run(main())
