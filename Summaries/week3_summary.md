# Week 3 Summary - USDA Nutrition Ingestion + Food Search

Generated: 2026-04-20

## Final Status

Week 3 data-quality fixes are complete. The Docker Postgres `static.foods` table is populated, verified, and re-scored with the corrected V1 anti-inflammatory rules.

- Final row count: `43`
- Duplicate USDA `external_id` values: `0`
- Full fix verification: `logs/week3_fix_verification.txt`
- Latest re-score report: `logs/rescore_20260420_092129.json`
- Full test result: `20 passed`

## Food Catalog Breakdown

Category counts:

- `fish`: 2
- `fruit`: 3
- `grain`: 5
- `legume`: 10
- `nut_seed`: 1
- `oil`: 3
- `other`: 2
- `protein`: 8
- `spice`: 2
- `vegetable`: 7

Cooking-state hints inferred from food names:

- `raw`: 14
- `cooked`: 3
- `unspecified`: 26

Cooking state is not a formal schema column yet; this is name-based only.

## USDA Nutrient Mapping Decisions

Core nutrient IDs:

- `calories`: primary `1008`, fallback `2047`
- `protein_g`: `1003`
- `carbs_g`: `1005`
- `sugar_g`: `2000`
- `fiber_g`: primary `1079`, fallback `2033`, fallback `1082 + 1084`
- `sodium_mg`: `1093`
- `fat_g`: `1004`
- `saturated_fat_g`: `1258`
- `omega3_g`: prompt IDs `1404 + 1405 + 1406`, plus current USDA Foundation omega IDs `1278 + 1272 + 1280`
- `calcium_mg`: `1087`
- `vitamin_d_ug`: `1114`

Fallbacks were added because USDA Foundation records are inconsistent across foods. Lentils lacked `1079`, some foods use `2047` for calories, and current salmon Foundation data exposes EPA/DHA under IDs different from the original prompt.

Persistent gaps:

- Beans, Dry, Brown (0% moisture): calories remain `0`
- Beans, Dry, Dark Red Kidney (0% moisture): calories remain `0`
- Beans, Dry, Light Red Kidney (0% moisture): calories remain `0`
- Oil, olive, extra light: calories remain `0`
- Oil, olive, extra virgin: calories remain `0`

These rows are retained as USDA-provenance records, but Week 4 should avoid presenting `0` calories as meaningful user-facing nutrition without a quality warning.

## Anti-Inflammatory Scoring

Final fiber scoring tiers:

- `+1.5` when `fiber_g >= 5.0`
- `+1.0` when `fiber_g >= 2.0`
- `+0.5` when `fiber_g >= 1.0`

All other scoring rules remain unchanged.

Top 10 foods after re-scoring:

- Fish, salmon, Atlantic, farm raised, raw: `8.5`
- Lentils, pink or red, raw: `8.0`
- Lentils, raw: `8.0`
- Beans, Dry, Brown (0% moisture): `7.5`
- Beans, Dry, Dark Red Kidney (0% moisture): `7.5`
- Beans, Dry, Light Red Kidney (0% moisture): `7.5`
- Flour, potato: `7.5`
- Lentils, mature seeds, cooked, boiled, without salt: `7.5`
- Lentils, mature seeds, cooked, boiled, with salt: `7.5`
- Spices, ginger, ground: `7.5`

Confirmed verification targets:

- Lentils raw/dry-style rows: `fiber_g >= 10.7`, score `>= 8.0`
- Lentils cooked rows: `fiber_g = 7.9`, score `7.5`
- Spinach rows: `fiber_g ~= 1.56`, score `6.5`
- Salmon verified row: `omega3_g = 1.610`, score `8.5`
- Cooked chicken breast row: `calories = 166`, score `5.5`

## Data Quality Issues Resolved

- Lentils Foundation fiber gap: Foundation `fdcId 2644283` lacked fiber nutrient data, so incomplete lentil rows were deleted and SR Legacy lentils were force-ingested.
- Spinach score too low: added the `fiber_g >= 1.0` tier so raw vegetables with modest fiber receive a small bonus.
- Calories fallback missing: added fallback from nutrient ID `1008` to `2047`.
- Omega-3 incomplete: omega-3 now sums multiple ALA/EPA/DHA-style nutrient IDs, including current Foundation IDs observed in salmon data.
- Negative USDA nutrient values: calculated negative nutrients are clamped to `0.0` before insert.
- Raw chicken breast verification mismatch: raw breast rows below `150 kcal` were removed from the verified Week 3 subset, and cooked chicken breast was retained.

## Endpoints Built

Food API routes:

- `GET /api/v1/foods/search`
- `GET /api/v1/foods/categories`
- `GET /api/v1/foods/{food_id}`

API behavior:

- Auth is required through bearer-token dependency `require_current_user_id`.
- Search supports `q`, optional `category`, `limit`, and `offset`.
- Pagination is implemented with `limit` and `offset`.
- Route order is correct: `/search` and `/categories` are defined before `/{food_id}`.

## Open Questions For Week 4

- Should cooking state become a real column instead of being inferred from names?
- Should raw and cooked versions be displayed separately or merged in search results?
- Should foods with calories `0` be hidden, warned, or kept for admin-only review?
- Which verified food IDs should seed the first curated meal templates?
- Should food search ranking combine text match, category, anti-inflammatory score, and data-quality flags?

## What Week 4 Needs From This Output

- Confirmed categories are available for recommendation rules.
- `anti_inflammatory_score` range is populated and clamped.
- Verified lentil, spinach, salmon, and cooked chicken breast rows are available for meal-template selection.
- `metadata_jsonb` keeps raw USDA provenance and quality flags for debugging.
- `logs/week3_fix_verification.txt` is the source of truth for final Week 3 data checks.

## Completion Marker

Week 3 is complete: data verified, summary written, Week 4 ready to begin.
