from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import AsyncSessionLocal

OUTPUT_PATH = PROJECT_ROOT / "logs" / "week4_verification.txt"

QUERIES = [
    (
        "Query 1 - food catalog final state",
        """
        SELECT category, cooking_state, COUNT(*) AS count, quality_flag
        FROM static.foods
        GROUP BY category, cooking_state, quality_flag
        ORDER BY category;
        """,
    ),
    (
        "Query 2 - no calories = 0 remaining",
        """
        SELECT name, calories
        FROM static.foods
        WHERE calories = 0 OR calories IS NULL;
        """,
    ),
    (
        "Query 3 - meal library summary",
        """
        SELECT meal_type, COUNT(*) AS count,
               ROUND(AVG(anti_inflammatory_score),1) AS avg_score,
               SUM(CASE WHEN is_vegetarian THEN 1 ELSE 0 END) AS veg_count,
               SUM(CASE WHEN is_flare_friendly THEN 1 ELSE 0 END) AS flare_count
        FROM static.meals
        GROUP BY meal_type
        ORDER BY meal_type;
        """,
    ),
    (
        "Query 4 - top 10 scoring meals",
        """
        SELECT name, meal_type, anti_inflammatory_score,
               is_flare_friendly, is_vegetarian
        FROM static.meals
        ORDER BY anti_inflammatory_score DESC
        LIMIT 10;
        """,
    ),
    (
        "Query 5 - ingredient coverage",
        """
        SELECT COUNT(DISTINCT food_id) AS foods_used,
               COUNT(*) AS total_ingredient_rows
        FROM static.meal_ingredients;
        """,
    ),
    (
        "Query 6 - tag distribution",
        """
        SELECT tag, COUNT(*) AS meal_count
        FROM static.meals,
             jsonb_array_elements_text(tags) AS tag
        GROUP BY tag
        ORDER BY meal_count DESC;
        """,
    ),
    (
        "Query 7a - custom meals empty",
        "SELECT COUNT(*) AS custom_meals_count FROM tracking.custom_meals;",
    ),
    (
        "Query 7b - custom meal ingredients empty",
        "SELECT COUNT(*) AS custom_meal_ingredients_count FROM tracking.custom_meal_ingredients;",
    ),
]


async def main() -> None:
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    lines: list[str] = ["Week 4 Verification", ""]
    async with AsyncSessionLocal() as db:
        for title, query in QUERIES:
            result = await db.execute(text(query))
            rows = result.mappings().all()
            lines.append(title)
            if not rows:
                lines.append("(0 rows)")
            else:
                lines.extend(format_rows(rows))
            lines.append("")
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Verification saved: {OUTPUT_PATH}")


def format_rows(rows: list[dict[str, Any]]) -> list[str]:
    headers = list(rows[0].keys())
    widths = {
        header: max(len(str(header)), *(len(str(row.get(header, ""))) for row in rows))
        for header in headers
    }
    output = [" | ".join(header.ljust(widths[header]) for header in headers)]
    output.append("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        output.append(" | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers))
    return output


if __name__ == "__main__":
    asyncio.run(main())
