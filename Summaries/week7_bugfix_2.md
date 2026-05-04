# Week 7 Bug Fix 2 Summary

## 1. Scope Completed

Second bug-fix pass targeting 5 issues across the meal display pipeline, UI state management,
analytics accuracy, and the lifestyle-to-recommendation signal chain.

Update on 2026-05-04: verified an additional Today&apos;s Logs rendering fix for duplicate meal
entries. The frontend is using the unique `tracking.food_logs.id` value as the React key for
today-log rows, which prevents duplicate logs of the same meal from collapsing into one item.

Additional update on 2026-05-04: refined custom meal creation and ingredient display UX in the
frontend. Custom meal saves now target the corrected backend route, the custom meal builder resets
stale draft state when a new UTC day begins, and both recommendation cards and custom meal log
rows render ingredients with wrapped tokens instead of a single truncated line.

---

## 2. Bugs Fixed

### BUG 1 + 3 — Meal display shows name only (no ingredients)

**Root cause:** `FoodLogItem` only had `meal_id` (a UUID) — no nested ingredient data.
`MealCard` already received `ingredients[]` but never rendered them.

**Files changed:**

- `frontend/src/components/logs/FoodLogItem.jsx` — complete rewrite
  - Derives `mealId` from `log.meal_id || log.recommendation_meal_id`
  - Fetches meal detail via `useQuery(["meals", mealId], getMealById, { staleTime: Infinity })`
  - Renders ingredient list as `food_name Xg · food_name Xg`
  - Falls back to `custom_food_name` → `meal.name` → `log.food?.name` → `"Food log"`

- `frontend/src/api/meals.js` — added `getMealById`
  ```js
  export async function getMealById(mealId) {
    const { data } = await apiClient.get(`/api/v1/meals/${mealId}`);
    return data;
  }
  ```

- `frontend/src/components/meals/MealCard.jsx`
  - Added ingredient list rendering above stats grid when `meal.ingredients?.length > 0`

---

### BUG 2 — Saved meal list stays visible after logging

**Root cause:** No UI state controlling visibility of the saved meals section after a log action.

**File changed:** `frontend/src/pages/MealLogPage.jsx`
- Added `showSavedMeals` and `loggedMealName` state
- After `logCustomMeal` succeeds: `setShowSavedMeals(false)`, `setLoggedMealName(meal.name)`
- Shows `✓ <meal> logged` success card with `+ Add another meal` button to reset state
- List re-appears only when user explicitly taps that button

---

### BUG 4 — Acceptance rate shows two different numbers

**Root cause:** Backend divided accepted count by all recommendation logs including `PENDING`
ones. Analytics page label also said "Accepted" without clarifying the denominator.

**Files changed:**

- `app/services/dashboard_service.py`
  - Changed denominator from `len(recs)` to `len(decided)` where
    `decided = [rec for rec in recs if rec.feedback_status != RecommendationFeedbackStatus.PENDING]`
  - Now: `accepted / decided` → true acceptance rate among acted-upon recommendations

- `frontend/src/pages/AnalyticsPage.jsx`
  - Label changed to `"Accepted (of decisions made)"` to match the corrected denominator

---

### BUG 5 — Lifestyle log signals not wired into recommendation rule engine

**Root cause:** `get_next_meal_recommendation` in `rule_engine.py` never read `LifestyleLog`.
Lifestyle data was saved and returned from the dashboard correctly but had zero influence
on `recommendation_mode` selection.

**Files changed:**

- `app/services/rule_engine.py` — 4 surgical edits:

  1. Added import: `from app.models.log import LifestyleLog, SymptomLog`

  2. Added `get_todays_lifestyle` helper:
     ```python
     async def get_todays_lifestyle(db: AsyncSession, user_id: UUID) -> LifestyleLog | None:
         today = datetime.now(timezone.utc).date()
         return await db.scalar(
             select(LifestyleLog).where(
                 LifestyleLog.user_id == user_id,
                 LifestyleLog.log_date == today,
             )
         )
     ```

  3. Added lifestyle override block in `get_next_meal_recommendation`:
     - `normal` mode + (poor sleep < 6h AND high stress ≥ 7) → `flare_only`
     - `normal` mode + (poor sleep OR high stress) → `mixed`
     - `mixed` mode + (severe sleep < 5h OR extreme stress ≥ 8) → `flare_only`
     - `medication_taken is False` → audit log entry only (no score change; clinician boundary)

  4. Mixed-mode explanation text now includes lifestyle context sentence:
     - Short sleep → `"Your sleep was short today."`
     - High stress → `"Your stress level was high today."`

- `frontend/src/pages/LifestyleLogPage.jsx`
  - Removed `useNavigate` import + `navigate("/dashboard")` call after save
  - Added `saved` state + success message `✓ Lifestyle log saved`
  - Added `queryClient.invalidateQueries` for `["dashboard","today"]`,
    `["dashboard","weekly"]`, and `["recommendation"]` so next recommendation
    re-fetches with updated lifestyle signals immediately

---

### BUG 6 — Logging the same meal twice only shows one entry in Today&apos;s Logs

**Root cause:** Earlier versions of the Today&apos;s Logs render path used `meal_id` /
`recommendation_meal_id` as the React list key. Those IDs are shared by repeated logs of the
same curated meal, so React reused the same row instead of rendering both log entries.

**Verification status in current frontend source:**

- `frontend/src/pages/MealLogPage.jsx`
  - Today&apos;s Logs rows render with `key={log.id}`
- `frontend/src/pages/CustomMealPage.jsx`
  - Today&apos;s Logs rows render with `key={log.id}`
- `testing and responses.txt`
  - Confirmed `GET /api/v1/logs/food/today` already returns a unique `"id"` field per entry
- Backend
  - No change needed; the API contract already exposes the correct unique log UUID

---

### BUG 7 — Custom meal save route and same-day draft state drift

**Root cause:** The custom meal builder was posting to the older custom-meals endpoint path, and
its local draft state could persist across day boundaries in the same browser session.

**Files changed:**

- `frontend/src/pages/CustomMealPage.jsx`
  - Changed custom meal creation POST from `/api/v1/custom-meals` to `/api/v1/meals/custom`
  - Added `todayKey` / `lastDay` tracking
  - Added a day rollover `useEffect` that clears `basket`, `name`, success state, and error
    state when the current UTC date changes

---

### BUG 8 — Ingredient text truncates in meal cards and custom meal log rows

**Root cause:** Ingredient lists were rendered as one joined string inside a truncated paragraph,
which hid later ingredients on narrower screens and reduced scanability.

**Files changed:**

- `frontend/src/components/meals/MealCard.jsx`
  - Replaced the truncated ingredient paragraph with a wrapped token layout
  - Each ingredient now shows the food name plus a styled gram amount with separators

- `frontend/src/pages/CustomMealPage.jsx`
  - Updated `CustomMealLogItem` to use the same wrapped token layout for ingredient display

---

## 3. Tests

- `tests/services/test_variety_penalty.py` — 7 unit tests + 1 integration test (added in bugfix pass 1, verified here)
- All 95 tests passed: `pytest tests/ -v` → `95 passed, 2 warnings`

---

## 4. Build Verification

- `npm run build` in `frontend/` — clean build, no errors, no type errors
  - 2026-05-04 latest verified rerun:
    - `dist/assets/index-C95emtMf.js 682.70 kB`
    - `dist/assets/index-Billdmla.css 16.94 kB`
    - build completed in `5.11s`
  - Earlier 2026-05-04 verified output in this bugfix session:
    - `dist/assets/index-Cx8gaaI7.js 682.48 kB` after `CustomMealPage.jsx` updates
  - Chunk size warning only; builds completed successfully
- `docker exec ra_project-api-1 pytest tests/ -v` — 95/95 passed, no regressions

---

## 5. Graph Update

- Attempted to run `graphify update .` on 2026-05-04
- Still blocked in this environment because the repo hook expects
  `node_modules/.bin/graphify`, but that executable is not present in this workspace
- Confirmed `frontend/node_modules/.bin` also does not contain a `graphify` binary
- The installed `graphify` package is not exposing the expected project CLI here
- Existing checked-in graph output remains the latest available snapshot:
  - `graphify-out/GRAPH_REPORT.md` timestamp: 2026-05-03
  - Snapshot metrics: **719 nodes, 1399 edges, 69 communities**

---

## 6. Signal Flow After BUG 5 Fix

```
User saves LifestyleLog (sleep_hours, stress_level, medication_taken)
  → frontend invalidates ["recommendation"] query
  → GET /api/v1/recommendations/next fires
  → get_next_meal_recommendation reads LifestyleLog for today
  → escalates recommendation_mode: normal → mixed → flare_only
  → explanation_text reflects lifestyle context
  → RecommendationPage renders updated meal with context note
```

---

✓ WEEK 7 BUG FIX PASS 2 COMPLETE — meal ingredient display, saved-meal UX state,
analytics acceptance rate denominator, lifestyle-to-recommendation signal chain,
duplicate Today&apos;s Logs rendering, custom meal route correction, day-rollover draft reset,
and wrapped ingredient presentation are verified; frontend builds are clean and the remaining
graph-refresh issue is environmental rather than application code
