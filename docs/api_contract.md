# RA App API Contract - Week 7 Frontend Source of Truth

Base path: `/api/v1`

Error response shape:

```json
{ "detail": "human readable message", "code": "machine_readable_code" }
```

FastAPI validation errors return HTTP 422 with FastAPI's validation detail array.

Authentication flow:

1. `POST /auth/login` returns `access_token`, `refresh_token`, `token_type`, and `user`.
2. Store tokens in memory only. Do not use `localStorage`.
3. Send `Authorization: Bearer {access_token}` on protected requests.
4. On `401`, call `POST /auth/refresh` with the refresh token.
5. If refresh succeeds, retry the original request. If refresh fails, redirect to login.

Medical boundary:

The app provides lifestyle support only and does not provide medical advice. Severe symptom logging returns:

```json
{
  "escalation_triggered": true,
  "escalation_message": "Your symptoms sound severe. Please contact your rheumatologist or seek medical advice. This app provides lifestyle support only."
}
```

## Auth

### POST `/auth/register`
Auth required: no
Request body: `{ "email": "string email", "password": "string min 8", "name": "string", "timezone": "string optional" }`
Response: `UserResponse`
Errors: `409` duplicate email, `422` invalid email or weak password
Notes: Creates an empty `user_preferences` row automatically.

### POST `/auth/login`
Auth required: no
Request body: `{ "email": "string email", "password": "string" }`
Response: `{ "access_token": "string", "refresh_token": "string", "token_type": "bearer", "user": UserResponse }`
Errors: `401` invalid credentials
Notes: Stores a hash of the refresh token in `core.authentication_sessions`.

### POST `/auth/refresh`
Auth required: no
Request body: `{ "refresh_token": "string" }`
Response: same as login
Errors: `401` invalid, expired, revoked, or reused refresh token
Notes: Rotates refresh tokens. Old refresh token reuse must fail.

### POST `/auth/logout`
Auth required: yes
Response: `{ "status": "logged_out" }`
Errors: `401` missing or invalid access token

### GET `/auth/me`
Auth required: yes
Response: `UserResponse`
Errors: `401`

### PUT `/auth/me`
Auth required: yes
Request body: `{ "name": "string optional", "height": "number optional", "weight": "number optional" }`
Response: `UserResponse`
Errors: `401`, `422`
Notes: Week 6 stores `name`; height and weight are accepted for frontend compatibility but not persisted until profile fields are added.

### POST `/auth/change-password`
Auth required: yes
Request body: `{ "current_password": "string", "new_password": "string min 8" }`
Response: `{ "status": "password_changed" }`
Errors: `401` wrong current password or invalid token, `422` weak new password

## Profile

### GET `/profile`
Auth required: yes
Response: `{ "user": UserResponse, "preferences": UserPreferencesResponse, "medications": UserMedicationResponse[] }`
Errors: `401`, `404`

### PUT `/profile/preferences`
Auth required: yes
Request body: `{ "dietary_flags": "string[] optional", "allergies": "string[] optional", "goals": "string[] optional", "cuisine_preferences": "string[] optional", "budget_friendly": "boolean optional" }`
Response: `UserPreferencesResponse`
Errors: `401`, `422`

### POST `/profile/medications`
Auth required: yes
Request body: `{ "medication_name": "string", "dosage": "string optional", "frequency": "string optional" }`
Response: `UserMedicationResponse`
Errors: `401`, `422`

### DELETE `/profile/medications/{id}`
Auth required: yes
Response: `{ "status": "removed" }`
Errors: `401`, `404`

## Foods

### GET `/foods/search`
Auth required: no
Query params: `q`, `category`, `limit`, `offset`
Response: `{ "items": FoodResponse[], "total": "int", "limit": "int", "offset": "int" }`
Errors: `422`

### GET `/foods/categories`
Auth required: no
Response: `string[]`

### GET `/foods/{food_id}`
Auth required: no
Response: `FoodResponse`
Errors: `404`

## Meals Curated

### GET `/meals`
Auth required: no
Query params: `meal_type`, `limit`, `offset`
Response: `{ "items": MealResponse[], "total": "int", "limit": "int", "offset": "int" }`

### GET `/meals/flare-safe`
Auth required: no
Response: curated flare-friendly meal list

### GET `/meals/by-tag/{tag}`
Auth required: no
Response: curated meal list matching tag

### GET `/meals/{meal_id}`
Auth required: no
Response: `MealResponse`
Errors: `404`

## Custom Meals

### POST `/meals/custom/calculate`
Auth required: yes
Request body: `{ "name": "string", "meal_type": "string", "ingredients": [{ "food_id": "uuid", "portion_g": "number", "cooking_state": "string" }] }`
Response: `CustomMealNutrients`
Errors: `401`, `422`
Notes: No DB write. Missing food IDs are excluded from score.

### POST `/meals/custom`
Auth required: yes
Request body: calculate body plus `{ "missing_ingredient_names": "string[]" }`
Response: `CustomMealResponse`
Errors: `401`, `422`

### GET `/meals/custom`
Auth required: yes
Query params: `limit`, `offset`
Response: `{ "items": CustomMealResponse[], "total": "int", "limit": "int", "offset": "int" }`

### GET `/meals/custom/{meal_id}`
Auth required: yes
Response: `CustomMealResponse`
Errors: `401`, `404`

### DELETE `/meals/custom/{meal_id}`
Auth required: yes
Response: `{ "status": "deleted" }`
Errors: `401`, `403`, `404`

## Ingredients

### POST `/ingredients/search`
Auth required: yes
Request body: `{ "ingredient_name": "string" }`
Response: `{ "found": "boolean", "matches": FoodResponse[], "missing_record": MissingIngredientResponse | null, "suggestion_message": "string | null" }`

### POST `/ingredients/missing`
Auth required: yes
Request body: `MissingIngredientCreate`
Response: `{ "status": "string", "message": "string", "reported_count": "int" }`
Notes: Duplicate active names increment `reported_count`.

### GET `/ingredients/missing`
Auth required: yes, admin
Query params: `status`, `limit`, `offset`
Response: paginated `MissingIngredientResponse[]`

### PATCH `/ingredients/missing/{id}`
Auth required: yes, admin
Request body: `{ "status": "string", "admin_notes": "string optional", "food_id": "uuid optional" }`
Response: `MissingIngredientResponse`

## Recommendations

### GET `/recommendations/next`
Auth required: yes
Query params: `meal_type`, `flare_active`
Response: `{ "primary": MealResponse, "alternatives": MealResponse[], "explanation": "string", "rule_applied": "string", "flare_mode_active": "boolean", "recommendation_mode": "normal|mixed|flare_only", "nutrition_summary": DailyNutritionSummary }`

### POST `/recommendations/{id}/feedback`
Auth required: yes
Request body: `{ "feedback_status": "pending|accepted|skipped|replaced", "feedback_reason": "string optional", "replacement_meal_id": "uuid optional" }`
Response: `{ "status": "ok" }`

### GET `/recommendations/history`
Auth required: yes
Query params: `limit`, `offset`
Response: paginated `RecommendationLogResponse[]`

## Logs

### POST `/logs/food`
Auth required: yes
Request body: `FoodLogCreate`
Response: `FoodLogResponse`
Notes: `log_source` values are `manual_log`, `curated_recommendation`, and `custom_meal`.

### GET `/logs/food/today`
Auth required: yes
Response: `{ "items": FoodLogResponse[], "nutrition_summary": DailyNutritionSummary }`

### GET `/logs/food/{date}`
Auth required: yes
Response: food logs for date

### DELETE `/logs/food/{log_id}`
Auth required: yes
Response: `{ "status": "deleted" }`

### POST `/logs/symptoms`
Auth required: yes
Response: `SymptomLogResponse`, with escalation fields when triggered

### GET `/logs/symptoms/today`
Auth required: yes
Response: `SymptomLogResponse | null`

### GET `/logs/symptoms/{date}`
Auth required: yes
Response: `SymptomLogResponse | null`

### POST `/logs/lifestyle`
Auth required: yes
Response: `LifestyleLogResponse`

### GET `/logs/lifestyle/today`
Auth required: yes
Response: `LifestyleLogResponse | null`

## Dashboard

### GET `/dashboard/today`
Auth required: yes
Response: today's nutrition, symptom, lifestyle, and recommendation summary

### GET `/dashboard/weekly`
Auth required: yes
Response: weekly nutrition and symptom trend summary
