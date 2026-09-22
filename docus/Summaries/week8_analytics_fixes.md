# Week 8 — Analytics Dashboard Fixes + Meal-Type Selection

Generated: 2026-05-14

## Graph Stats

| Metric      | Previous | Current | Delta |
|-------------|----------|---------|-------|
| Nodes       | 872      | 873     | +1    |
| Edges       | 1829     | 1832    | +3    |
| Communities | 72       | 72      | 0     |
| Files       | 148      | 148     | 0     |

AST-only extraction. Refresh: 2026-05-14.

---

## Bugs Fixed This Session

### 1. PainTrendChart always empty

**Root cause:** Frontend read `data?.pain_trend || data?.symptom_trend`, but backend `WeeklyDashboardResponse` had neither field. Chart always rendered "Log symptoms to see trends" even when symptom data existed.

**Fix:**
- Added `pain_trend: list[dict]` to `WeeklyDashboard` dataclass + `WeeklyDashboardResponse` Pydantic model
- Built from sorted symptoms: `[{"date": "Thu", "pain_score": 5}, ...]`

**Files:** `app/services/dashboard_service.py`, `app/routers/dashboard.py`

---

### 2. Weekly insights used today's nutrition, not weekly

**Root cause:** `generate_weekly_insights` called `get_todays_nutrition(db, user_id)` — only today's snapshot, not the full week.

**Fix:** Refactored to sync function taking weekly `food_logs` + `symptoms` lists already fetched. Computes avg daily sugar/fiber across actual days with food logs. Added pain-based insight (avg pain ≥ 6) and flare count insight (≥ 3 days).

**Files:** `app/services/dashboard_service.py`

---

### 3. MissingGreenlet crash on weekly endpoint

**Root cause:** Weekly query fetched `FoodLog` rows without `selectinload`. When `summarize_food_logs` accessed `log.food`, `log.meal`, `log.custom_meal`, async lazy loading triggered outside greenlet context → 500 error.

**Fix:** Added `selectinload(FoodLog.food)`, `.meal`, `.recommendation_meal`, `.custom_meal` to weekly query.

**Files:** `app/services/dashboard_service.py`

---

### 4. Naive datetime mismatch with timestamptz columns

**Root cause:** First attempt used `datetime.combine(d, time.min, tzinfo=timezone.utc)`. SQLAlchemy maps `Mapped[datetime]` as `TIMESTAMP WITHOUT TIME ZONE` in queries despite DB column being `timestamptz`. asyncpg rejected timezone-aware param: `can't subtract offset-naive and offset-aware datetimes`.

**Fix:** Reverted to naive `datetime.combine(d, time.min)`. DB stores everything in UTC, naive UTC = correct.

**Files:** `app/services/dashboard_service.py`

---

### 5. Week navigation buttons not wired

**Root cause:** AnalyticsPage Previous/Next buttons rendered with no `onClick`. Users could only see current week — no history access. Confused users whose data lived in prior weeks.

**Fix:**
- Backend: `GET /api/v1/dashboard/weekly?week_offset=N` (N ∈ [-52, 0])
- Service: `week_start = today - weekday() + timedelta(weeks=week_offset)`
- API client: `getWeeklyDashboard(weekOffset)` passes param
- Page: `useState(0)` for `weekOffset`, Previous decrements, Next increments (disabled at 0). Label shows "This week" / "Last week" / "N weeks ago".

**Files:** `app/routers/dashboard.py`, `app/services/dashboard_service.py`, `frontend/src/api/dashboard.js`, `frontend/src/pages/AnalyticsPage.jsx`

---

### 6. Null `avg_pain_score` displayed as `0.0`

**Root cause:** `number(data?.avg_pain_score || 0, 1)` — null coalesced to 0, rendered "0.0" giving false impression of zero pain instead of no data.

**Fix:** Render `—` when backend returns null. Same for `recommendation_acceptance_rate`.

**Files:** `frontend/src/pages/AnalyticsPage.jsx`

---

## New Feature — Explicit Meal-Type Selection

**Problem:** `detect_meal_type_by_time` picked meal_type from clock. User logging breakfast at 11am got "lunch" recommendations. Wrong-timezone users got wrong meal type entirely.

**Implementation:**

| File | Change |
|------|--------|
| `app/routers/dashboard.py` | `GET /dashboard/today` accepts `?meal_type=breakfast\|lunch\|snack\|dinner` (regex-validated) |
| `app/services/dashboard_service.py` | `get_today_dashboard(meal_type=None)` — uses explicit param when given, falls back to `detect_meal_type_by_time` otherwise |
| `frontend/src/api/dashboard.js` | `getTodayDashboard(dietOverride, mealType)` builds params conditionally |
| `frontend/src/hooks/useDashboard.js` | `useTodayDashboard(dietOverride, mealType)` — mealType in queryKey for auto-refetch |
| `frontend/src/pages/DashboardPage.jsx` | 4-button grid (Breakfast/Lunch/Snack/Dinner), tap to select, tap again to deselect (reverts to time-based) |

**Rule engine: zero changes.** Variety tracking already keyed per `recommended_for_meal_type`, so each meal type has its own rotation pool.

---

## E2E Test Results (account: spandanprvt12@gmail.com)

**17 / 17 PASS:**

- All 4 meal types return correct recommendations with matching `meal_type` field
- Invalid `meal_type=brunch` → HTTP 422
- 6 consecutive lunch calls returned 6 UNIQUE meals (zero loop)
- Diet override veg + non-veg both filter correctly
- Week offsets -2, -1, 0 return correct data; offsets +1 and -53 rejected with 422
- Recommendation feedback POST returns 200
- API metrics match DB ground truth exactly

**Variety check output (key concern from user):**
```
1. Brown rice with salmon and broccoli
2. Grilled mackerel with sweet potato
3. Black Bean and Avocado Stuffed Pita
4. Egg and avocado salad with spinach
5. Tuna and Quinoa Salad Bowl
6. Edamame Grain Bowl with Miso Dressing
```

---

## Minor Finding (not blocking)

Non-vegetarian meals correctly filtered via `is_vegetarian=false` but their `tags` array lacks a `"non_vegetarian"` string. Vegetarian meals include `"vegetarian"` in tags. Asymmetric data tagging. Only matters if any UI renders dietary badges from tags.

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

---

## Files Touched

```
app/routers/dashboard.py                        (meal_type param + week_offset param + pain_trend field)
app/services/dashboard_service.py               (insights rewrite + selectinload + week_offset + meal_type param + pain_trend)
frontend/src/api/dashboard.js                   (mealType param + weekOffset param)
frontend/src/hooks/useDashboard.js              (mealType in queryKey)
frontend/src/pages/AnalyticsPage.jsx            (week nav state + null-safe display + previous/next buttons)
frontend/src/pages/DashboardPage.jsx            (4 meal-type buttons + hint text)
graphify-out/GRAPH_REPORT.md                    (refreshed)
graphify-out/graph.json                         (refreshed)
graphify-out/graph.html                         (refreshed)
```

---

## Open Items → Week 9

- Add `"non_vegetarian"` tag to non-veg meals in `static.meals` for consistency
- Custom meal `meal_type` selection (currently hardcoded to "lunch" in `acceptMeal`)
- Edge case tests: empty logs, new user, full flare mode, allergy conflicts
- Medical disclaimer banners (Week 9 roadmap item)
- Deploy backend (Render/Railway) + frontend (Vercel/Netlify)

✓ Week 8 analytics dashboard fully functional with historical week navigation, meal-type buttons, and per-week pain trend visualization. All E2E tests pass.
