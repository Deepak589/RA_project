# Week 7 Summary

## 1. Migration 0007

- Added `alembic/versions/0007_add_user_role.py`.
- Added `core.users.role` with default `user`.
- Added role check values: `user`, `admin`.
- Updated the user ORM/schema with `role`.
- Added `get_current_admin_user` and kept `require_admin_user` as an alias.
- Admin ingredient review endpoints now use the real admin check through `require_admin_user`.

Runtime status:

- `alembic upgrade head` completed successfully after Docker came online.
- Verification SQL confirmed `core.users.role` exists with default `'user'::character varying`.

## 2. React Setup

- Updated `frontend/package.json` with required dependencies:
  - `react-router-dom`
  - `@tanstack/react-query`
  - `axios`
  - `recharts`
  - `lucide-react`
  - `clsx`
  - `tailwindcss`
  - `postcss`
  - `autoprefixer`
- Added Tailwind config and PostCSS config.
- Added `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8000`.
- Updated Vite dev proxy for `/api`.

Runtime status:

- `npm install` could not run because `npm` is not available on PATH in this shell.
- After Node.js was installed, `npm install` completed successfully.
- `npm run build` completed successfully.

## 3. Screens Built

- `LoginPage`
- `RegisterPage`
- `OnboardingPage`
- `DashboardPage`
- `RecommendationPage`
- `MealLogPage`
- `SymptomLogPage`
- `LifestyleLogPage`
- `CustomMealPage`
- `AnalyticsPage`
- `ProfilePage`

No screens were intentionally skipped. Some interactions are first-pass practical implementations pending browser testing.

## 4. Components Built

- UI primitives:
  - `Button`
  - `Card`
  - `Input`
  - `Select`
  - `Slider`
  - `Badge`
  - `Spinner`
  - `EscalationBanner`
- Layout:
  - `AppLayout`
  - `BottomNav`
  - `PageHeader`
- Meals:
  - `MealCard`
  - `MealIngredientList`
  - `FlareBanner`
- Logs:
  - `FoodLogItem`
  - `SymptomSlider`
  - `NutritionSummary`
- Charts:
  - `PainTrendChart`
  - `NutritionBarChart`
  - `WeeklyAdherenceChart`

## 5. Auth Flow

- Added Axios API client with `withCredentials: true`.
- Added in-memory access token handling.
- Added AuthContext with login, logout, refresh, and initial refresh attempt.
- Added 401 retry interceptor.
- No `localStorage` or `sessionStorage` usage.

Known auth limitation:

- The Week 6 backend returns `refresh_token` in the JSON response and does not set an httpOnly cookie yet. The frontend keeps the refresh token in memory only so the current backend contract can still work without browser storage.
- Registration initially failed because `passlib` and the installed `bcrypt` package were incompatible at runtime. Password hashing now uses direct `bcrypt` calls while still storing bcrypt hashes.
- Local frontend development uses the Vite `/api` proxy with an empty `VITE_API_BASE_URL` to avoid CORS preflight failures.

## 6. Manual Test Results

Backend verification completed:

- Full backend suite: `81 passed, 1 warning`.
- The warning is from `passlib` / Python `crypt` deprecation and is not a test failure.
- Frontend build: `npm run build` passed.
- Registration and login were verified directly against the API.
- Registration was also verified through the Vite `/api` proxy at `localhost:5173`.

Manual browser flows could not be run because:

- Browser manual testing still needs to be repeated after the auth registration fixes.
- Vite dev server restarted on `http://localhost:5173` after the proxy/env fix.

Static checks completed:

- Frontend source scan found no `localStorage`, `sessionStorage`, direct `fetch`, or inline `style=` usage.

## 7. Known Limitations

- Full browser click-through testing remains useful, but the registration API path is now verified.
- Refresh-token cookie behavior needs backend support if strict httpOnly-cookie auth is required.
- Admin role migration is applied and verified in the running DB.
- The dashboard/recommendation feedback flow gracefully handles missing recommendation log IDs, but the backend response may need to expose them for perfect feedback binding.
- Analytics screen is intentionally basic; Week 8 should deepen the charting and insight UX.

## 8. Open Questions For Week 8

- Which analytics charts should be added first: nutrition adherence, symptom correlation, flare frequency, or recommendation acceptance?
- Should backend auth be updated to set refresh tokens as httpOnly cookies?
- Should dashboard recommendation responses expose `recommendation_log_id` directly?
- Should admin roles get a seed script for the first admin account?

## 9. What Week 8 Needs

- Run `npm install` and `npm run build` once Node/npm are available.
- Run `alembic upgrade head` once Docker Desktop is available.
- Manually verify the six Week 7 flows in browser.
- Use the current screen structure as the base for Week 8 analytics expansion.

✓ WEEK 7 COMPLETE — frontend built, screens connected to API, runtime manual flows pending local Docker/npm availability, Week 8 analytics structure ready
