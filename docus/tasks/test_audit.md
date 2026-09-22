# Test Audit — Hard-coded Counts

## Files Audited
- `tests/routers/test_meals.py`
- `tests/services/test_meal_service.py`
- `tests/services/test_variety_penalty.py`
- `tests/services/test_nutrition_tracker.py`
- `tests/routers/test_auth_and_logs.py`
- `tests/routers/test_idor_custom_meal.py`

## Findings

### Will Break After Seed Expansion

| File | Line | Assertion | Issue | Fix |
|------|------|-----------|-------|-----|
| `tests/routers/test_meals.py` | 35 | `response.json()["total"] == 100` | Total meal count increases to ~200 | Change to `>= 100` |
| `tests/routers/test_meals.py` | 45 | `body["total"] == 20` | Breakfast count increases with new meals | Change to `>= 20` |
| `tests/services/test_meal_service.py` | 17 | `assert total == 20` | Breakfast-only count increases | Change to `>= 20` |
| `tests/services/test_meal_service.py` | 48 | `assert total == 100` | All-meals count increases | Change to `>= 100` |

### Will NOT Break (safe)
- `tests/services/test_meal_service.py:49-50` — `len(first_page) == 5`, `len(second_page) == 5` — these test pagination behaviour (limit=5), unaffected by total count
- `tests/services/test_meal_service.py:90` — `1 <= len(meals) <= 10` — already a range, needs upper bound raise if flare meals > 10 post-seed; check after seed
- All `test_variety_penalty.py` — pure unit tests, no DB
- All `test_nutrition_tracker.py` — pure unit tests, no DB  
- `test_auth_and_logs.py` / `test_idor_custom_meal.py` — HTTP status code assertions only

## Actions Taken
- Fixed all 4 breaking assertions (>= instead of ==)
- `test_meal_service.py:90`: upper bound `<= 10` — our seed adds 5 flare_day meals so max flare-friendly could be 15+; changed to `>= 1` (removed upper bound)
