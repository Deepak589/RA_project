# Week 7 — Graphify Refresh + Recommendation/Dashboard Changes

Generated: 2026-05-09

## Graph Stats (graphify-out/GRAPH_REPORT.md)

| Metric       | Before     | After      | Delta |
|--------------|-----------|-----------|-------|
| Nodes        | 733       | 776       | +43   |
| Edges        | 1432      | 1591      | +159  |
| Communities  | 29        | 68        | +39   |
| Files        | 139       | 141       | +2    |

Re-extraction: AST only, no LLM. Cache hits dominant — 9 new chunk entries in `graphify-out/cache/`.

## Code Changes Summary

### 1. Diet Override (per-request)

New optional query param `diet_override ∈ {vegetarian, non_vegetarian}` on:
- `GET /api/v1/dashboard/today` (`app/routers/dashboard.py`)
- `GET /api/v1/recommendations/next` (`app/routers/recommendations.py`)

Threaded through:
- `dashboard_service.get_today_dashboard(..., diet_override)`
- `recommendation_service.get_next_recommendation(..., diet_override)`
- `rule_engine.get_next_meal_recommendation(..., diet_override)`

Behavior in `_apply_preferences` (`app/services/rule_engine.py`):
- Override only applies when user has no real dietary flags. Stored prefs win.
- Whitelist via `VALID_DIET_OVERRIDES = {"vegetarian", "non_vegetarian"}`.
- If override filter empties pool → log warning, fallback to full pool.
- Adds `[PREFERENCE OVERRIDE: diet_override=...]` to rule trace logs.

### 2. `non_vegetarian` Flag Matching

`_meal_matches_dietary_flags` (`rule_engine.py:493`):
- New branch: meal excluded if `meal.is_vegetarian` true OR tags contain `vegetarian`/`vegan`.

### 3. Variety Penalty — Partial Reset

`_apply_variety_penalty` (`rule_engine.py:358`):
- `VARIETY_LOOKBACK_COUNT`: 4 → **8**.
- When eligible pool < 3, only repeat offenders (id appears ≥2 in recent logs) keep penalty; others reset to base.
- New return `"variety_pool_reset_partial"` + log line `[VARIETY: partial reset — repeat offenders penalized]`.

### 4. Timezone-aware Meal Detection

`detect_meal_type_by_time(moment, user_tz)` (`dashboard_service.py:128`):
- Reads `User.timezone` via `select(User.timezone)`.
- Converts UTC `now` to user TZ via `ZoneInfo`. Falls back silently on `ZoneInfoNotFoundError`.

### 5. Misc

- `_priority_delta` rounding: 6 → 1 decimal (`rule_engine.py:494`).
- `docker-compose.yml`: app service now runs `alembic upgrade head && uvicorn ...` on boot.

## New Tests (`tests/services/`)

- `test_diet_flag_matching.py` — `non_vegetarian` exclusion semantics.
- `test_diet_override.py` — override application + fallback when pool empties.
- `test_recommendation_loop.py` — variety partial-reset + repeat-offender penalty.

## God Nodes (post-refresh, top by edge count)

See `graphify-out/GRAPH_REPORT.md` for full list. Hot spots unchanged: `Select()`, `get_next_meal_recommendation()`, `FoodLog`, `Meal`, `RecommendationLog`, `normalize_usda_food()`.

## Files Touched

```
app/routers/dashboard.py
app/routers/recommendations.py
app/services/dashboard_service.py
app/services/recommendation_service.py
app/services/rule_engine.py
docker-compose.yml
tests/services/test_diet_flag_matching.py        (new)
tests/services/test_diet_override.py              (new)
tests/services/test_recommendation_loop.py        (new)
```
