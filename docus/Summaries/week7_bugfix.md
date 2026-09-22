# Week 7 Bug Fix Summary

## 1. Scope Completed

- Continued the post-Week-7 bug-fix pass from the in-progress changes already in the repo.
- Finished the main backend/frontend contract alignment needed for auth refresh, recommendations, symptom updates, food search, and diet preferences.
- Added the missing shared frontend components required by the bug list:
  - `frontend/src/components/FoodSearch.jsx`
  - `frontend/src/components/DietPreferences.jsx`

## 2. Backend Fixes Finalized

- `app/routers/auth.py`
  - Duplicate email now returns structured `409` with code `EMAIL_ALREADY_EXISTS`.
  - Weak password route handling remains aligned with structured `422` response.
  - Refresh token cookie flow is present with `ra_refresh`.
- `app/main.py`
  - CORS is configured with explicit `http://localhost:5173` and `allow_credentials=True`.
- `app/routers/logs.py`
  - `GET /api/v1/logs/symptoms/today` is present.
  - `PATCH /api/v1/logs/symptoms/today` is present.
- `app/services/log_service.py`
  - Today symptom upsert behavior is in place.
  - Escalation message logic uses the required fixed message.
- `app/services/rule_engine.py`
  - Recommendation response now carries the saved `recommendation_log_id`.
  - Stronger variety penalty logic was added for recent repeated recommendations.
  - Dietary filtering now supports:
    - `vegetarian`
    - `pescatarian`
    - `vegan`
    - `gluten_free`
    - `dairy_free`
    - `low_sodium`
- `app/schemas/recommendation.py`
  - Added `recommended_meal`.
  - Added `recommendation_log_id`.
- `app/routers/recommendations.py`
  - Returns the updated recommendation shape expected by the frontend.
- `app/routers/dashboard.py`
  - Dashboard recommendation payload now matches the updated recommendation shape.
  - Weekly dashboard response now exposes `meal_logged_days` alongside `total_meals_logged`.
- `app/services/dashboard_service.py`
  - Weekly analytics now keeps two separate meal metrics:
    - `total_meals_logged` = number of meal log entries in the week
    - `meal_logged_days` = number of distinct days out of 7 with at least one meal log
  - Weekly meal analytics are confirmed to use `tracking.food_logs`, not `recommendation_logs`.
  - `meal_logged_days` is derived directly from the returned weekly `FoodLog` rows for consistency.
  - `recommendation_acceptance_rate` is now returned as a true percentage value instead of a 0-1 fraction.
- `app/schemas/user.py`
  - Restored `RegisterRequest.password` minimum length validation to keep the existing weak-password contract intact.

## 3. Frontend Fixes Finalized

- `frontend/src/api/client.js`
  - Reworked the Axios auth wiring around `configureApiToken()` and `configureApiAuth()`.
  - Added queued refresh retry behavior for concurrent `401` responses.
  - Kept `withCredentials: true`.
- `frontend/src/context/AuthContext.jsx`
  - Access token now lives in memory through a ref-based flow.
  - App bootstrap now attempts silent refresh and then restores the current user.
  - Login, register, logout, and refresh wiring now match the cookie-based backend contract.
- `frontend/src/pages/auth/RegisterPage.jsx`
  - Added field-level error handling for duplicate email and weak password responses.
  - Added separate general error handling.
  - Field errors clear as the user edits.
- `frontend/src/components/FoodSearch.jsx`
  - Added debounced search.
  - Added dropdown results.
  - Added keyboard navigation.
  - Added clear button.
  - Added loading and empty states.
  - Added outside-click close behavior.
  - Added cooked/raw badges.
- `frontend/src/pages/MealLogPage.jsx`
  - Replaced the old inline search flow with the new `FoodSearch` component.
  - Added `Build my own meal` CTA.
  - Shows today’s logs on the page.
  - Uses the updated query invalidation flow.
  - After a successful meal log, now invalidates:
    - `["food-logs", "today"]`
    - `["dashboard", "today"]`
    - `["dashboard", "weekly"]`
- `frontend/src/pages/RecommendationPage.jsx`
  - Renders the primary recommendation from the updated backend shape.
  - Renders all alternatives.
  - Wires feedback using `recommendation_log_id`.
  - Added `Build my own meal` CTA.
- `frontend/src/pages/DashboardPage.jsx`
  - Reads the updated recommendation payload shape.
  - Added `Build meal` quick action.
  - Removed the old non-compliant escalation fallback copy and uses backend message only.
- `frontend/src/pages/SymptomLogPage.jsx`
  - Loads today’s existing symptom log.
  - Prefills the form when today’s log exists.
  - Switches between create and update behavior.
  - Shows the escalation warning before save.
  - Shows temporary success confirmation after save.
  - Weekly dashboard data is invalidated after symptom updates.
- `frontend/src/pages/LifestyleLogPage.jsx`
  - Weekly dashboard data is invalidated after lifestyle log saves.
- `frontend/src/pages/AnalyticsPage.jsx`
  - Uses the exact weekly query key `["dashboard", "weekly"]`.
  - Uses `staleTime: 0` so invalidation forces a fresh refetch.
  - Reads the separate weekly metrics correctly:
    - `meal_logged_days`
    - `total_meals_logged`
  - Weekly insights card now distinguishes:
    - meal days
    - total meals logged
  - Weekly adherence bar now uses the correct day-based value for “X out of 7 days”.
- `frontend/src/components/DietPreferences.jsx`
  - Added the 7-option multi-select grid.
  - `No preference` behaves exclusively.
- `frontend/src/hooks/useLogs.js`
  - Food log query key is aligned to `["food-logs", "today"]`.
  - Dashboard invalidation now targets weekly and daily dashboard keys explicitly.
- `frontend/src/main.jsx`
  - Added `refetchOnWindowFocus: true` to the default query behavior so stale analytics data refreshes when the user returns to the tab.
- `frontend/src/pages/auth/OnboardingPage.jsx`
  - Replaced the one-option diet flow with `DietPreferences`.
- `frontend/src/pages/ProfilePage.jsx`
  - Replaced the one-option diet flow with `DietPreferences`.
- `frontend/src/App.jsx`
  - Added `/custom-meal` route alias alongside the existing custom meal route.

## 4. Verification Results

- `npm run build` completed successfully in `frontend/`.
- `graphify update .` completed successfully using the project virtualenv executable.
- Targeted backend contract test passed:
  - `tests/services/test_week6_contracts.py::test_register_request_rejects_weak_password`
- Weekly dashboard endpoint was queried directly after backend restart and returned live corrected values, including:
  - `total_meals_logged: 5`
  - `meal_logged_days: 1`
  - `recommendation_acceptance_rate: 4.5`
  - `flare_days_count: 0`
- Backend API container was restarted with `docker compose restart api`.
- Frontend Vite dev server was restarted so the browser could pick up the fresh analytics bundle.

## 5. Verification Limits

- Full backend `pytest` could not be verified end-to-end in this shell because the configured PostgreSQL host `db` was not resolvable here.
- The database-backed tests failed for environment connectivity, not from a confirmed application regression.
- A stray inaccessible cache-like directory (`pytest-cache-files-71hldhro`) also required scoping test commands to `tests/`.
- Browser-side manual verification still depends on reloading the live UI against the restarted frontend session.

## 6. Remaining Risks

- Backend DB-backed tests still need to be rerun in the normal Docker-backed environment.
- The recommendation variety behavior should still be manually checked in-browser with real seeded recommendation history.
- The new food search and diet preference flows should still get a quick browser click-through after the backend environment is available.
- The weekly insights UI should be manually rechecked after reload to confirm the browser now shows:
  - meal days from `meal_logged_days`
  - total meals from `total_meals_logged`
  - correct acceptance percentage formatting

## 7. What To Verify Next

- Login, refresh the page, and confirm session restoration still works.
- Recommendation page shows one primary meal plus alternatives.
- Meal log page shows the new autocomplete and today’s logs immediately after submission.
- Symptom page loads an existing same-day log and updates it correctly.
- Onboarding and profile both show all diet preference options.
- Analytics page shows:
  - `Meals logged` based on total meal entries
  - `Meal days` based on distinct logged days in the week
  - weekly adherence text like `1 out of 7 days` when meals were logged on one day
  - acceptance rate as a real percent value
- Run the full backend test suite once the local DB/Docker environment is available.

✓ WEEK 7 BUG FIX PASS COMPLETE — core auth, recommendation, symptom, food search, diet preference, and weekly analytics fixes are in place; frontend build passed; live weekly API values were verified after restart; full DB-backed backend verification still needs the normal local runtime environment
