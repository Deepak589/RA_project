# Week 8 — Analytics Dashboard + Week 7 Bug Verification

Generated: 2026-05-14

## Graph Stats

| Metric      | Week 7 (post-bugfix) | Week 8  | Delta |
|-------------|----------------------|---------|-------|
| Nodes       | 872                  | 872     | 0     |
| Edges       | 1829                 | 1829    | 0     |
| Communities | 31                   | 72      | +41   |
| Files       | 148                  | 148     | 0     |

Re-extraction: AST only, no LLM. 148 files, 2026-05-14.
Community count rose 31→72 due to tighter Louvain pass — no structural change in code.

---

## Week 7 Bug Status (verified in code, 2026-05-14)

All 10 bugs from the two bugfix passes are confirmed resolved in current source:

| Bug | Description | Verified location |
|-----|-------------|-------------------|
| BUG 1+3 | Meal display showed name only, no ingredients | `FoodLogItem.jsx` fetches meal detail via `useQuery` |
| BUG 2 | Saved meal list stayed visible after logging | `MealLogPage.jsx` — `showSavedMeals` / `loggedMealName` state |
| BUG 4 | Acceptance rate double-counted PENDING logs | `dashboard_service.py` — denominator is `decided` (non-PENDING) only |
| BUG 5 | Lifestyle signals not wired into rule engine | `rule_engine.py` — `get_todays_lifestyle()`, mode escalation block |
| BUG 6 | Duplicate meal log entries collapsed into one | All log lists use `key={log.id}` |
| BUG 7 | Custom meal draft persisted across day boundary | `CustomMealPage.jsx` — `todayKey`/`lastDay` day-rollover `useEffect` |
| BUG 8 | Ingredient text truncated in cards | `MealCard.jsx` + `CustomMealPage.jsx` — wrapped token layout |
| BUG 9 | Custom meal payload sent `grams` not `portion_g` | `CustomMealPage.jsx` — `{ food_id, portion_g }` + `meal_type` |
| BUG 10 | `"no_preference"` triggered dietary filter | `rule_engine.py` — `has_real_preference` excludes `no_preference` |
| Auth | Refresh token in JSON body (flaky session) | `auth.py` — `httpOnly` cookie, `samesite` strict/lax, `COOKIE_NAME` |

### Custom meal persistence (todo.md primary bug)
`log_service.py:53–66` — `log_source == "custom_meal"` path loads `CustomMeal` by ID, writes
`custom_meal_id`, `custom_food_name`, `display_calories`, `display_protein_g` to `tracking.food_logs`. ✓

### Auth session stability
`auth.py:33–37` — refresh token set as `httpOnly` cookie (`ra_refresh`), `secure` from settings,
`samesite` strict in prod / lax in dev. Login, register, and refresh all call `response.set_cookie`. ✓

---

## Week 8 Work Done

### Analytics Dashboard (`AnalyticsPage.jsx`)

- `PainTrendChart` — 7-day pain score trend (Recharts)
- `WeeklyAdherenceChart` — meal logged days bar chart
- Metric grid: avg pain, meal days, total meals, recommendation acceptance rate, flare days
- Weekly insights list from `GET /dashboard/weekly` → `insights: list[str]`
- Previous/Next week navigation buttons (UI only; week offset not yet wired to backend)

### Backend `/dashboard/weekly` endpoint

`dashboard.py` + `dashboard_service.py`:
- `avg_pain_score`, `avg_fatigue`, `avg_sleep_hours`, `avg_meal_quality_score`
- `total_meals_logged`, `meal_logged_days`
- `recommendation_acceptance_rate` — denominator: decided (non-PENDING) only
- `flare_days_count`, `best_day`, `worst_day`
- `insights: list[str]` — simple correlation highlights

### Alembic migration (carried from week 8 schema-drift fix)

`alembic/versions/2dddb02d5f05_add_missing_tables.py` — captures 4 previously ad-hoc tables:
- `static.meal_ingredients`
- `tracking.custom_meals`
- `tracking.custom_meal_ingredients`
- `tracking.missing_ingredients`

Plus real column/constraint drift on `static.foods` and `core.user_preferences`.

---

## God Nodes (unchanged)

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

---

## Open Items Carried to Week 9

- Previous/Next week navigation not wired to backend (UI buttons exist)
- `manual browser click-through` of all screens against live API — not formally recorded
- Docker-backed pytest: last known result `95 passed` (2026-05-04); rerun needed before deploy

---

## Next — Week 9 (Testing + MVP Release)

Per roadmap:
1. Edge case tests: empty logs, new user with no history, full flare mode, allergy conflicts
2. Manually review 20–30 recommendation outputs for quality
3. Medical disclaimer banners + escalation prompts for severe symptom scores
4. Deploy backend → Render.com or Railway (free tier)
5. Deploy frontend → Vercel or Netlify

✓ WEEK 8 COMPLETE — analytics dashboard live, all Week 7 bugs verified resolved in source,
schema migrations captured, graphify refreshed (872 nodes, 1829 edges, 72 communities, 2026-05-14)
