# Recommendation Loop Fix — Report

## Summary

The `_apply_variety_penalty` full-reset path was wiping all variety penalties when the eligible pool dropped below 3, allowing the highest-scoring repeat-offender meal to win indefinitely. Two targeted changes — a partial reset that preserves penalties on repeat offenders, and 1-decimal bucket rounding in `_priority_delta` — resolved the loop. All 7 tests pass consistently.

## Baseline (before changes)

| Test | Status | Notes |
|------|--------|-------|
| T1 small_pool_no_repeat | PASS | Variety penalty fires correctly for pool >= 3 |
| T2 flare_only_no_consecutive_repeats | **FAIL** | Flare pool of 3 shrinks to eligible=2 after 1 pick; full reset fires; top meal wins all 5 calls |
| T3 vegetarian_filter_loop | PASS | Only 3 veg meals but variety penalty rotates them correctly (eligible >= 3 from full pool) |
| T4 tied_score_jitter | PASS | Random shuffle distributes tied-score meals |
| T5 repeat_offender_demoted_on_third_call | **FAIL** | Full reset fires (eligible_pool=2 < 3); meal_X (score 9.0) wins despite being in recent x2 |
| T6 healthy_pool_regression | PASS | Large pool, variety penalty works fine |
| T7 single_meal_pool_returns_same_meal | PASS | Single meal: same meal returned both calls (expected) |

```
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-8.4.2, pluggy-1.6.0
asyncio: mode=Mode.AUTO
collecting ... collected 7 items

tests/services/test_recommendation_loop.py::test_small_pool_no_repeat PASSED
tests/services/test_recommendation_loop.py::test_flare_only_no_consecutive_repeats FAILED
tests/services/test_recommendation_loop.py::test_vegetarian_filter_loop PASSED
tests/services/test_recommendation_loop.py::test_tied_score_jitter PASSED
tests/services/test_recommendation_loop.py::test_repeat_offender_demoted_on_third_call FAILED
tests/services/test_recommendation_loop.py::test_healthy_pool_regression PASSED
tests/services/test_recommendation_loop.py::test_single_meal_pool_returns_same_meal PASSED

2 failed, 5 passed
```

## Changes applied

- **Change A — partial reset** (`app/services/rule_engine.py`, `_apply_variety_penalty`, lines ~348-353):
  Replaced the blanket reset block with a targeted partial reset. When `eligible_pool < MIN_ELIGIBLE_POOL_SIZE`, meals that appear `>= 2` times in `recent_ids` are classified as `repeat_offenders` and keep their variety penalty. Only non-offender meals have their `adjusted_score` reset to base score. Returns `"variety_pool_reset_partial"` instead of `"variety_pool_reset"`.

- **Change A (caller)** (`app/services/rule_engine.py`, `get_next_meal_recommendation`, lines ~145-149):
  Added handling for `"variety_pool_reset_partial"` — sets `dominant_rule = "variety_pool_reset"` and appends `[VARIETY: partial reset — repeat offenders penalized]` to logs.

- **Change B — wider priority buckets** (`app/services/rule_engine.py`, `_priority_delta`, line ~479):
  Changed `round(..., 6)` to `round(..., 1)`. This prevents micro-score differences from splitting meals into separate buckets, ensuring the shuffle randomization within each bucket distributes tied-priority meals more effectively.

## After changes

| Test | Status | Notes |
|------|--------|-------|
| T1 small_pool_no_repeat | PASS | |
| T2 flare_only_no_consecutive_repeats | PASS | Partial reset keeps penalty on repeat offender; other flare meals win |
| T3 vegetarian_filter_loop | PASS | |
| T4 tied_score_jitter | PASS | |
| T5 repeat_offender_demoted_on_third_call | PASS | meal_X stays penalised; Other A/B win |
| T6 healthy_pool_regression | PASS | |
| T7 single_meal_pool_returns_same_meal | PASS | |

```
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-8.4.2, pluggy-1.6.0
asyncio: mode=Mode.AUTO
collecting ... collected 7 items

tests/services/test_recommendation_loop.py::test_small_pool_no_repeat PASSED
tests/services/test_recommendation_loop.py::test_flare_only_no_consecutive_repeats PASSED
tests/services/test_recommendation_loop.py::test_vegetarian_filter_loop PASSED
tests/services/test_recommendation_loop.py::test_tied_score_jitter PASSED
tests/services/test_recommendation_loop.py::test_repeat_offender_demoted_on_third_call PASSED
tests/services/test_recommendation_loop.py::test_healthy_pool_regression PASSED
tests/services/test_recommendation_loop.py::test_single_meal_pool_returns_same_meal PASSED

7 passed in 1.25s
```

## Regression check

T6 (`test_healthy_pool_regression`) passed both before and after the fix. The broader `tests/services/` suite shows 10 pre-existing failures, all due to missing DB connection (`socket.gaierror: [Errno 11001] getaddrinfo failed`):
- `tests/services/test_meal_service.py` — 9 tests (require live DB)
- `tests/services/test_variety_penalty.py::test_variety_penalty_demotes_repeated_meal` — 1 test (requires live DB)

These failures existed before this change and are unrelated to it. All pure-unit tests in the suite continue to pass.

## Edge cases

T7 (`test_single_meal_pool_returns_same_meal`): when only 1 meal survives all filters, the system has no alternative. Both calls return the same meal. This is expected behaviour — not a bug — and is documented rather than asserted as broken. The partial reset handles this gracefully: if that 1 meal is a repeat offender, it keeps its penalty but still wins because there's nothing else.

## Files modified

- `app/services/rule_engine.py` — Change A (partial reset logic + caller branch) and Change B (round to 1dp)
- `tests/services/test_recommendation_loop.py` (new) — 7 test scenarios, pure unit tests using mock AsyncSession
- `tasks/recommendation_loop_report.md` (new) — this file

---

# Diet Override Toggle — Investigation + Fix

## Bug analysis

| ID | Description | Verdict | Fixed |
|----|-------------|---------|-------|
| a | Empty pool 404: breakfast/snack non-veg toggle (0 non-veg meals) → hard filter empties candidates → 404 | Real bug | Yes — `_apply_preferences` now falls back to full pool + logs warning when override empties result |
| b | Toggle hidden in `DashboardPage.jsx` when user has real diet preference (`hasRealDietPreference`) | UX choice, not bug | No — intentional design |
| c | `has_real_preference` logic broken: flags `["vegetarian","no_preference"]` → `False` → override wrongly takes over real preference | Real bug | Yes — line 301 simplified to `bool(active_dietary_flags)` |
| d | `activeOverride = showDietToggle ? dietOverride : null` discards localStorage when toggle hidden | UX, intentional | No |
| e | `chooseDiet` clicking same button clears override (toggle-off) | UX | No |
| f | `_meal_matches_dietary_flags` had no explicit `non_vegetarian` branch (relied on `is_vegetarian` exclusion) | Existed but works; explicit branch added for clarity | Yes — added branch line 525-527 |

## DB backfill

```sql
UPDATE static.meals SET dietary_tags_jsonb = dietary_tags_jsonb || '["non_vegetarian"]'::jsonb
WHERE is_vegetarian = false AND NOT dietary_tags_jsonb @> '["non_vegetarian"]'::jsonb;
```
Result: 30/30 non-veg meals tagged.

| meal_type | total | non-veg | flare-friendly non-veg |
|-----------|-------|---------|------------------------|
| breakfast | 20 | 0 | 0 |
| dinner | 25 | 18 | 10 |
| flare_day | 15 | 0 | 0 |
| lunch | 25 | 12 | 3 |
| snack | 15 | 0 | 0 |

## Test results

11 new tests, all pass:

- `tests/services/test_diet_override.py` — D1–D6 (6 scenarios)
- `tests/services/test_diet_flag_matching.py` — 5 unit tests for `_meal_matches_dietary_flags`

`docker exec ra_project-api-1 pytest tests/services/test_diet_override.py tests/services/test_diet_flag_matching.py tests/services/test_recommendation_loop.py -v` → **18/18 PASS** in 3.00s.

## Code changes

- `app/services/rule_engine.py:300-301` — fix `has_real_preference` logic
- `app/services/rule_engine.py:308-318` — empty-pool fallback when override drove filter
- `app/services/rule_engine.py:523-527` — explicit `non_vegetarian` branch in `_meal_matches_dietary_flags`
- `app/routers/dashboard.py`, `app/routers/recommendations.py` — `diet_override` query param plumbing
- `app/services/dashboard_service.py`, `app/services/recommendation_service.py` — pass-through

## Manual / API verification

- `npm run build` in `frontend/` → succeeded (vite 5.4.21, 2526 modules, 20.26s).
- Browser session not driven (no Playwright in repo, no auth fixture available without seeded user).
- Recommended manual smoke test: log in as user with no dietary preference, open dashboard, click Veg → recommendation should be vegetarian; click Non-Veg → recommendation should be non-vegetarian. Test on `lunch`/`dinner` (have non-veg pool) and `breakfast`/`snack` (zero non-veg → falls back to full pool, not 404).

## Open UX issues (not fixed)

- Bug (b): toggle hidden when user has explicit dietary preference in profile. If product wants override available always, change `showDietToggle` to ignore preference.
- Bug (e): clicking same button clears override silently. Consider explicit "Clear" button or 3-state radio.
- Breakfast/snack/flare_day non-veg fallback returns the **full pool** (likely all veg). User clicks Non-Veg, still gets veg meal. Backend logs warning but frontend has no signal. Future: surface the fallback in `recommendation_context_jsonb` so frontend can show "No non-veg breakfast options — showing full menu".
