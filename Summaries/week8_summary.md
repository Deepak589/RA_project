# Week 8 — Schema Drift Fix + Graphify Refresh

Generated: 2026-05-11

## Graph Stats

| Metric      | Before (Week 7) | After   | Delta |
|-------------|-----------------|---------|-------|
| Nodes       | 776             | 871     | +95   |
| Edges       | 1591            | 1827    | +236  |
| Communities | 68              | 29      | -39   |
| Files       | 141             | 148     | +7    |

Re-extraction: AST only, no LLM. 148 files processed.

## Work Done This Week

### 1. Alembic Migration — Schema Drift Captured

**Problem:** 4 tables existed in DB but had no Alembic migration. Created ad-hoc outside migration history. Fresh deploy would miss them.

**Migration created:** `alembic/versions/2dddb02d5f05_add_missing_tables.py`  
**Revises:** `0007_add_user_role`

Tables captured:
- `static.meal_ingredients` — per-meal food portions with cooking state
- `tracking.custom_meals` — user-created meals with computed nutrition totals
- `tracking.custom_meal_ingredients` — ingredients for custom meals
- `tracking.missing_ingredients` — user-reported missing foods with review workflow

Additional real schema drift fixed:
- `static.foods.cooking_state`: `VARCHAR(20)` → `Text`
- `static.foods.quality_flag`: `VARCHAR(30)` → `Text`
- `core.user_preferences`: constraint rename (`user_preferences_user_id_key` → `ix_core_user_preferences_user_id` unique)
- `tracking.lifestyle_logs`: constraint rename (`lifestyle_logs_user_id_log_date_key` → `uq_tracking_lifestyle_logs_user_log_date`)

**False positives stripped:** ~50 `TIMESTAMP(timezone=True) → DateTime()` alter columns autogenerate would have generated — would have broken timezone awareness across all tables.

Migration applied and verified: `alembic current` = `2dddb02d5f05 (head)`

### 2. Token Optimisation — Removed Duplicate Skills

Deleted 3 project-level skill duplicates from `.claude/skills/`:
- `caveman-commit/SKILL.md`
- `caveman-review/SKILL.md`
- `caveman-help/SKILL.md`

Plugin already provides these. ~220 tokens saved per message.

## God Nodes (post-refresh)

| Rank | Node | Edges |
|------|------|-------|
| 1 | `Meal` | 72 |
| 2 | `Select()` | 53 |
| 3 | `Food` | 50 |
| 4 | `RecommendationLog` | 37 |
| 5 | `DailyNutritionState` | 29 |
| 6 | `get_next_meal_recommendation()` | 28 |
| 7 | `NutritionGaps` | 24 |
| 8 | `main()` | 24 |
| 9 | `FoodLog` | 23 |
| 10 | `normalize_usda_food()` | 22 |

## New Migration in Graph

Community 31 now appears: `add_missing_tables  Revision ID: 2dddb02d5f05`

## Files Touched

```
alembic/versions/2dddb02d5f05_add_missing_tables.py   (new)
.claude/skills/caveman-commit/SKILL.md                 (deleted)
.claude/skills/caveman-review/SKILL.md                 (deleted)
.claude/skills/caveman-help/SKILL.md                   (deleted)
graphify-out/GRAPH_REPORT.md                           (updated)
graphify-out/graph.json                                (updated)
graphify-out/graph.html                                (updated)
```
