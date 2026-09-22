# Agent Task: Fix 9 Post-Week-7 Bugs — RA Lifestyle App

## Context

You are working on a Rheumatoid Arthritis lifestyle support app. The stack is:
- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL (Docker) + Alembic (currently at migration 0007)
- **Frontend:** React + Vite + TanStack Query + Axios + Tailwind CSS + Recharts
- **Auth:** Bearer access token (in-memory) + refresh token (currently in JSON body — needs to move to httpOnly cookie)
- **DB schemas:** `core`, `static`, `tracking`, `intelligence`
- **Current test count:** 81 backend tests passing, 1 warning (passlib/bcrypt deprecation — ignore it)

The app completed Week 7 (full frontend build). Manual testing revealed 9 bugs. Fix all of them. Do NOT break existing passing tests. Add new tests where indicated.

---

## Bug Fixes Required

### B-01 — Registration does not show "email already exists" error

**Root cause:** Backend returns a generic error; frontend shows a generic banner instead of an inline field error.

**Backend fix — `app/routers/auth.py`:**
In the `POST /auth/register` route, when a duplicate email is detected, raise:
```python
raise HTTPException(
    status_code=409,
    detail={
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "An account with this email already exists.",
    },
)
```
Also raise a structured error for weak passwords:
```python
raise HTTPException(
    status_code=422,
    detail={
        "code": "PASSWORD_TOO_SHORT",
        "message": "Password must be at least 8 characters.",
    },
)
```

**Frontend fix — `src/pages/RegisterPage.jsx`:**
- Use `fieldErrors` state (per-field) separate from `generalError` state.
- On submit, catch `err.response.data.detail.code`:
  - `EMAIL_ALREADY_EXISTS` → set `fieldErrors.email = "An account with this email already exists."`
  - `PASSWORD_TOO_SHORT` → set `fieldErrors.password = detail.message`
  - Anything else → set `generalError`
- Render field errors as small red text directly below the relevant input, not as a banner.
- Clear a field's error as soon as the user starts typing in that field.

---

### B-02 — Page refresh loses auth state (tokens only in memory)

**Root cause:** Refresh token is returned in the JSON body and stored in memory only. On browser refresh, both tokens are lost.

**Backend fix — `app/routers/auth.py`:**

Add a cookie helper:
```python
COOKIE_NAME = "ra_refresh"
COOKIE_KWARGS = dict(
    key=COOKIE_NAME,
    httponly=True,
    secure=False,        # set True in production
    samesite="lax",
    max_age=60 * 60 * 24 * 30,
    path="/",
)
```

- In `POST /auth/register` and `POST /auth/login`: after creating the refresh token, call `response.set_cookie(value=refresh_token, **COOKIE_KWARGS)`. Still return the token in the JSON body too (keeps API backwards-compatible for non-browser clients).
- In `POST /auth/refresh`: read `request.cookies.get("ra_refresh")` first; fall back to `body.refresh_token` if cookie is absent. On success, set a new cookie with the rotated token.
- In `POST /auth/logout`: call `response.delete_cookie(key="ra_refresh", path="/")`.

**FastAPI CORS fix — `main.py`:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # explicit origin required for credentials
    allow_credentials=True,                   # must be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Warning:** `allow_origins=["*"]` with `allow_credentials=True` is rejected by browsers. Use the explicit origin list.

**Frontend fix — `src/context/AuthContext.jsx`:**
- Keep the access token in a `useRef` (in memory).
- On app mount, immediately call `POST /auth/refresh` with `withCredentials: true`. The browser sends the cookie automatically. On success, store the returned access token in the ref and fetch `/profile` to restore the user object. If refresh fails (no cookie / expired), stay logged out silently.
- `login()` and `register()` both use `withCredentials: true` so the browser stores the cookie the backend sets.
- `logout()` calls `POST /auth/logout` with `withCredentials: true` then clears local state.
- Expose `getAccessToken()`, `refreshAccessToken()`, `login()`, `register()`, `logout()`.
- Do NOT use `localStorage` or `sessionStorage` anywhere.

**Frontend fix — `src/api/client.js`:**
- Create an Axios instance with `withCredentials: true` globally.
- Add a request interceptor that reads `getAccessToken()` and sets `Authorization: Bearer <token>`.
- Add a response interceptor: on 401, if not already retrying (`_retried` flag), call `refreshAccessToken()`, update the header, and retry the original request once. Use a queue to handle concurrent 401s (don't fire multiple refresh calls simultaneously). If refresh fails, call `logout()`.
- Export `configureApiAuth(refreshFn, logoutFn)` and `configureApiToken(getTokenFn)` so the auth context can wire these up after mount without circular imports.

---

### B-03 — Food autocomplete only triggers after full item is entered (not on keystroke)

**Root cause:** The search input is bound to form submit, not `onChange`.

**Frontend fix — `src/components/FoodSearch.jsx` (new component):**
- Create a standalone `FoodSearch` component.
- On every `onChange` event, debounce 300ms, then call `GET /api/v1/foods/search?q=<value>&limit=10` if input length ≥ 2 characters.
- Render results in an absolutely-positioned dropdown below the input.
- Support keyboard navigation: ArrowDown/ArrowUp moves selection, Enter confirms, Escape closes.
- Show a clear (×) button when the input has a value.
- Show a loading indicator during the API call.
- Show an empty state message when query ≥ 2 chars but no results found.
- Close the dropdown on outside click (use a `ref` + `mousedown` listener on `document`).
- Call `onSelect(food)` prop when user picks a result.

---

### B-04 — Autocomplete only shows raw foods, not cooked versions

**Root cause:** `cooking_state` is stored in `static.foods` (added in migration 0004) but not returned in the search API response or shown in the UI.

**Backend fix — `app/routers/foods.py`:**
Ensure `GET /foods/search` response includes `cooking_state` for each result. Add it to the Pydantic response schema if missing.

**Frontend fix — inside `FoodSearch.jsx`:**
Show a small badge next to each result's name indicating `cooking_state`:
- `"cooked"` → teal/green badge
- `"raw"` → blue badge
- `"unspecified"` or absent → no badge

---

### B-05 — Recommendation always returns salmon / only one item shown

Two separate sub-bugs:

**Sub-bug A — Backend (rule engine variety penalty too weak):**

In `app/services/rule_engine.py`, replace the existing variety penalty logic with stronger tiers:

```python
VARIETY_PENALTY_WINDOW_HOURS = 48

VARIETY_PENALTY_TIERS = [
    (1, -2.0),   # recommended once in last 48h
    (2, -4.0),   # twice
    (3, -6.0),   # three or more times — effectively removes from pool
]

def apply_variety_penalty(score: float, meal_id: str, recent_ids: list[str]) -> float:
    count = recent_ids.count(meal_id)
    penalty = 0.0
    for threshold, p in VARIETY_PENALTY_TIERS:
        if count >= threshold:
            penalty = p
    return max(0.0, score + penalty)
```

Fetch recent recommended meal IDs once at the start of recommendation generation:
```python
from datetime import datetime, timedelta, timezone

cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
recent_ids = [
    str(r.meal_id)
    for r in db.query(RecommendationLog.meal_id)
        .filter(RecommendationLog.user_id == user_id, RecommendationLog.shown_at >= cutoff)
        .all()
]
```

Apply `apply_variety_penalty()` to every candidate meal's score before ranking. After sorting, ensure `GET /recommendations/next` returns:
- `recommended_meal`: the top-ranked meal object
- `alternatives`: a list of at least 3 runner-up meal objects (not just the top 1)
- `explanation`: string
- `recommendation_log_id`: the UUID of the saved `intelligence.recommendation_logs` row (needed for feedback)

**Sub-bug B — Frontend (`src/pages/RecommendationPage.jsx`):**
The page currently only renders `data.recommended_meal`. Fix it to also map and render `data.alternatives` as a list of alternative meal cards below the primary recommendation.

Structure:
1. Meal type selector (breakfast / lunch / dinner / snack)
2. Primary recommendation card (highlighted with an info border) — includes explanation text and "Looks good / Show another" feedback buttons
3. "Alternatives" section heading
4. List of alternative meal cards (render all items in the `alternatives` array)
5. "Build my own meal" CTA button at the bottom (routes to `/custom-meal`) — fixes B-06

---

### B-06 — No visible button to create a custom meal

**Root cause:** `CustomMealPage` exists but is not linked from the meal log flow or dashboard.

**Frontend fixes:**
- In `src/pages/MealLogPage.jsx`: add a "Build my own meal" button below the food search area (between search and the log form), routing to `/custom-meal`.
- In `src/pages/RecommendationPage.jsx`: add the same CTA at the bottom (already described in B-05 above).
- In `src/pages/DashboardPage.jsx`: add "Build meal" as a quick action card alongside the existing log actions.

The button style should be secondary/dashed — it's an alternative path, not the primary action.

---

### B-07 — Food logs only visible in Meals section, not in Logs section

**Root cause:** The Logs view (or dashboard) does not call `GET /logs/food/today` and therefore the food log entries never appear there.

**Frontend fix — `src/pages/MealLogPage.jsx`:**
- Add a `useQuery` call for `GET /logs/food/today`.
- Render the returned `entries` array as a "Today's logs" list at the bottom of the page.
- Each entry shows: food name, meal type, portion (if set), time logged.
- Include a delete (×) button per entry that calls `DELETE /logs/food/{log_id}` and invalidates the query.
- After a successful new log submission (`logMeal.onSuccess`), also invalidate `["food-logs-today"]` and `["dashboard"]`.

---

### B-08 — Update today's symptoms not working

**Root cause:** `tracking.symptom_logs` is append-only (no upsert). There is no endpoint to update the current day's log, and the frontend always shows an empty form with no indication a log already exists.

**Backend fix — `app/routers/logs.py` (or equivalent):**

Add a new endpoint:
```
PATCH /api/v1/logs/symptoms/today
```

Request body (all fields optional — partial update):
```json
{
  "pain_score": 0-10,
  "fatigue_score": 0-10,
  "stiffness_score": 0-10,
  "swelling_score": 0-10,
  "flare_level": "none|mild|moderate|severe",
  "note": "string"
}
```

Logic:
1. Query `tracking.symptom_logs` for the most recent row where `user_id = current_user` AND `logged_at` is within today (UTC midnight to 23:59:59).
2. If a row exists: update only the fields that were provided in the request body (`exclude_none=True`).
3. If no row exists: create a new one with `logged_at = now()`.
4. Recalculate `escalation_triggered`: `pain_score >= 8` OR `flare_level in ("moderate", "severe")`.
5. Commit and return the full updated record including `escalation_triggered`.

Also confirm `GET /logs/symptoms/today` exists as a convenience route. If only `GET /logs/symptoms/{date}` exists, add:
```python
@router.get("/symptoms/today")
def get_todays_symptoms(user_id = Depends(...), db = Depends(...)):
    return get_symptoms_by_date(user_id, date.today(), db)
```

**Frontend fix — `src/pages/SymptomLogPage.jsx`:**
- On mount, call `GET /logs/symptoms/today`.
- If a log is returned: pre-fill all sliders with the existing values, change the page heading to "Update today's symptoms", add a hint: "Your earlier log for today has been loaded. Adjust any values and save.", change the submit button label to "Update symptoms".
- If no log: show the empty form with heading "Log symptoms" and button "Save symptoms".
- On submit: if a log already existed, call `PATCH /logs/symptoms/today`; otherwise call `POST /logs/symptoms`.
- Show the escalation banner (amber warning box with the medical escalation message) if `pain_score >= 8` OR `flare_level` is `"moderate"` or `"severe"` — show it before the save button, not after. The escalation banner must NOT block saving.
- Show a success confirmation ("✓ Symptoms updated." or "✓ Symptoms logged.") for 3 seconds after a successful save.

---

### B-09 — Diet preferences only show "vegetarian"

**Root cause:** The onboarding and profile screens only render one diet option.

**Frontend fix — `src/components/DietPreferences.jsx` (new component):**

Create a multi-select grid component with these options:
```
No preference    — "I eat everything" — exclusive (clears all others when selected)
Vegetarian       — "No meat or fish"
Pescatarian      — "No meat, fish is fine"
Vegan            — "No animal products"
Gluten-free      — "Avoiding gluten"
Dairy-free       — "No dairy products"
Low-sodium       — "Reducing salt intake"
```

- Render as a responsive grid of toggle buttons (2–3 columns).
- Each button shows the label and a short description.
- Active state: info-colored border + background.
- "No preference" is exclusive — selecting it deselects everything else; selecting any other option deselects "No preference".
- Props: `value: string[]`, `onChange: (keys: string[]) => void`.
- The `value` array is stored in `user_preferences.dietary_flags_json` — no migration needed, the field is already JSONB.

**Use this component in:**
- `src/pages/OnboardingPage.jsx` — replace the existing diet step
- `src/pages/ProfilePage.jsx` — replace the existing diet preference section

**Backend rule engine fix — `app/services/rule_engine.py`:**
The preference filter currently only handles `"vegetarian"`. Extend it to handle all 6 new dietary flags: `pescatarian`, `vegan`, `gluten_free`, `dairy_free`, `low_sodium`. Each flag should filter or downrank meals whose `dietary_tags_json` does not include the matching tag.

---

## Files to Create or Modify

### New files
- `src/components/FoodSearch.jsx`
- `src/components/DietPreferences.jsx`

### Modified backend files
- `app/routers/auth.py` — B-01 structured errors, B-02 httpOnly cookie
- `app/main.py` — B-02 CORS credentials fix
- `app/routers/logs.py` — B-08 PATCH /logs/symptoms/today + GET /logs/symptoms/today
- `app/services/rule_engine.py` — B-05 variety penalty tiers + B-09 dietary flag handling

### Modified frontend files
- `src/context/AuthContext.jsx` — B-02 silent refresh on mount
- `src/api/client.js` — B-02 withCredentials + 401 retry queue
- `src/pages/RegisterPage.jsx` — B-01 inline field errors
- `src/pages/MealLogPage.jsx` — B-03/B-04 FoodSearch, B-06 custom meal CTA, B-07 today's logs list
- `src/pages/RecommendationPage.jsx` — B-05 alternatives list, B-06 custom meal CTA
- `src/pages/DashboardPage.jsx` — B-06 "Build meal" quick action
- `src/pages/SymptomLogPage.jsx` — B-08 detect + pre-fill existing log, PATCH on update
- `src/pages/OnboardingPage.jsx` — B-09 DietPreferences component
- `src/pages/ProfilePage.jsx` — B-09 DietPreferences component

---

## Constraints

1. Do NOT break any of the 81 currently passing backend tests.
2. Do NOT use `localStorage` or `sessionStorage` anywhere in the frontend.
3. Do NOT use `allow_origins=["*"]` with `allow_credentials=True` — it will break in all browsers.
4. Do NOT add medical advice, diagnosis, or treatment language anywhere in the UI.
5. All symptom escalation messages must use this exact text: *"You logged symptoms that may need medical attention. This app cannot assess urgent health problems or tell you how to treat a flare. If this pain or flare is severe, unusual for you, getting worse, or you are worried about your safety, please contact your clinician, urgent care, or local emergency services as appropriate."*
6. The escalation message must be shown but must NOT prevent the user from saving their log.
7. Add at minimum these new backend tests after completing the fixes:
   - B-01: POST /auth/register with duplicate email returns 409 with `code: EMAIL_ALREADY_EXISTS`
   - B-02: POST /auth/login sets the `ra_refresh` cookie in the response
   - B-02: POST /auth/refresh with a valid cookie returns a new access token and rotates the cookie
   - B-08: PATCH /logs/symptoms/today creates a new log when none exists today
   - B-08: PATCH /logs/symptoms/today updates the existing log when one already exists today
   - B-08: PATCH /logs/symptoms/today sets escalation_triggered=True when pain_score >= 8

---

## Apply fixes in this order (each depends on the previous)

1. B-02 backend (httpOnly cookie + CORS) — everything else is unverifiable until auth works on refresh
2. B-02 frontend (AuthContext + axios client)
3. B-01 (duplicate email error — backend structured error + frontend inline display)
4. B-03 + B-04 (FoodSearch component — debounce + cooking state)
5. B-08 backend (PATCH /logs/symptoms/today + GET /logs/symptoms/today)
6. B-05 backend (variety penalty tiers + alternatives in response)
7. B-07 + B-06 + B-05 frontend (MealLogPage, RecommendationPage, DashboardPage)
8. B-08 frontend (SymptomLogPage pre-fill + PATCH)
9. B-09 (DietPreferences component + OnboardingPage + ProfilePage + rule engine dietary flags)

Run `pytest` after each backend change. Run `npm run build` after completing all frontend changes.

---

## Verification checklist (run these manual checks at the end)

- [ ] Register with an existing email → inline red error appears under the email field, no page reload
- [ ] Login → refresh the browser page → still logged in, dashboard loads
- [ ] Type 3 characters in food search → dropdown appears within ~300ms, results show cooked/raw badges
- [ ] Recommendation page → primary meal shown + at least 2 alternatives listed below it
- [ ] Recommendation page → salmon does not appear every single time (variety working)
- [ ] Meal log page → "Build my own meal" button visible without scrolling
- [ ] Meal log page → after logging a meal, it appears immediately in "Today's logs" on the same page
- [ ] Symptom page → log a symptom, leave the page, come back → sliders show previous values, button says "Update today's symptoms"
- [ ] Symptom page → set pain to 9 → amber escalation warning appears before the save button
- [ ] Onboarding / profile → diet preferences show 7 options including Pescatarian, Vegan, Gluten-free
