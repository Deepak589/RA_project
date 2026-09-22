# Week 5 Summary

## 1. Migration 0005

Added `alembic/versions/0005_food_log_enhancements.py`.

`tracking.food_logs` columns added:
- `log_source`
- `raw_portion_g`
- `cooking_state_at_log`
- `conversion_factor_at_log`
- `display_calories`
- `display_protein_g`
- `recommendation_meal_id`
- `custom_meal_id`

`intelligence.recommendation_logs` columns added:
- `rule_priority_applied`
- `flare_mode_active`
- `daily_nutrition_context_json`

Additional Week 5 endpoint support fields were added to `tracking.symptom_logs` and `tracking.lifestyle_logs` so the requested symptom/lifestyle request shapes can persist cleanly.

## 2. Rule Engine

Implemented `app/services/rule_engine.py` with the Week 5 priority flow:
- Safety allergy hard blocks
- Medication-aware scoring
- Flare-mode reordering
- Daily nutrition gap boosts
- Preference filtering and boosts
- Anti-inflammatory score ranking
- Variety penalties for recent recommendations

Flare behavior was implemented as reorder-first, not removal. The smoke flow confirmed a flare-friendly dinner was ranked first. In the current seeded top 5, all dinner alternatives were also flare-friendly, so non-flare meals were not visible in that limited result even though the sorter keeps them after flare-friendly meals.

Medication rules were implemented in `app/services/medication_filter.py`. Methotrexate, NSAID, corticosteroid, and biologic handling all include `[VERIFY WITH CLINICIAN]` safety comments/log language where relevant.

Example generated explanation:
`Baked salmon with sweet potato and spinach recommended because: you are in flare mode, and this meal is gentle, low effort, and anti-inflammatory, and your omega-3 intake today is low and this meal provides 3.0g. Dominant rule: flare.`

## 3. Endpoints Built

Recommendations:
- `GET /api/v1/recommendations/next`
- `POST /api/v1/recommendations/{recommendation_id}/feedback`
- `GET /api/v1/recommendations/history`

Logs:
- `POST /api/v1/logs/food`
- `GET /api/v1/logs/food/today`
- `GET /api/v1/logs/food/{date}`
- `DELETE /api/v1/logs/food/{log_id}`
- `POST /api/v1/logs/symptoms`
- `GET /api/v1/logs/symptoms/today`
- `GET /api/v1/logs/symptoms/{date}`
- `POST /api/v1/logs/lifestyle`
- `GET /api/v1/logs/lifestyle/today`

Dashboard:
- `GET /api/v1/dashboard/today`
- `GET /api/v1/dashboard/weekly`

## 4. Integration Results

Added and ran `scripts/week5_smoke.py`.

Smoke flow verified:
- Test user creation with methotrexate medication
- Manual breakfast food log creation
- Lunch recommendation saved
- Accepted feedback update
- Low-pain symptom log with no escalation
- Lifestyle log creation
- Today dashboard generation
- Flare dinner recommendation with flare-friendly primary

## 5. Test Results

Current test result:
- `52 passed, 1 warning`

New focused tests:
- `tests/services/test_nutrition_tracker.py`
- `tests/services/test_medication_filter.py`
- `tests/services/test_dashboard_service.py`

## 6. Open Questions for Week 6

- Custom meal builder endpoints are still deferred and should be built against the new `custom_meal_id` food log path.
- Auth flow still deserves a dedicated review before frontend work.
- Rule-engine edge case: top-5 flare recommendations may all be flare-friendly with the current seed data, so a broader response or targeted seed fixture is needed to visibly prove non-flare meals appear after flare meals.

## 7. What Week 6 Needs

- Confirm rule engine API contract for custom meal recommendations.
- Confirm log endpoint shapes before frontend binding.
- Confirm dashboard response shapes before Week 7 UI work.
- Add broader router/integration coverage for Week 5 endpoints if Week 6 depends on those contracts staying stable.
