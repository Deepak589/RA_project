# Plan: Expand Foods + Meals (2x scale, USDA + Manual Curated)

**Goal:** Grow DB from 43 foods → ~90 and 100 meals → ~200. Source: USDA via existing ingest + manual curated for cuisine items USDA lacks (paneer, dosa, roti, dal varieties, etc.). Rules untouched. Tests stay green.

**Constraints:**
- No schema migration. Reuse existing `static.foods`, `static.meals`, `static.meal_ingredients`.
- Existing rule_engine logic untouched.
- Idempotent seed (re-runnable).
- Reversible (unseed script).

---

## Phase 1 — Audit & Prep

1. **Inventory current data** → verify: `SELECT COUNT(*) FROM static.foods; SELECT COUNT(*) FROM static.meals;`
   - verify: counts match expected baseline (43, 100)

2. **Audit tests for hard counts**
   - grep: `tests/` for `len(...) == \d`, `assert.*count.*== \d`, `LIMIT \d`
   - List any test that depends on exact meal/food count
   - verify: list saved to `tasks/test_audit.md`

3. **DB backup**
   - `pg_dump` to `backups/pre_curated_seed_<timestamp>.sql`
   - verify: file exists, non-empty

---

## Phase 2 — Manual Curated Data Files

4. **Create `scripts/data/curated_foods.json`**
   - ~50 manual food entries focused on items USDA weak/missing:
     - Indian: paneer, ghee, urad dal cooked, moong dal cooked, chana dal cooked, masoor dal, rajma cooked, chickpeas cooked (besan), atta whole wheat flour, basmati rice cooked, idli, dosa batter, roti/chapati, naan
     - Asian: tofu firm, tempeh, edamame, miso, seaweed nori, soba noodles cooked
     - Mediterranean: hummus, tahini, feta, halloumi, olives green/black
     - Mexican: black beans cooked, pinto beans cooked, corn tortilla, avocado mash
     - Common gaps: cottage cheese, ricotta, plain greek yogurt full-fat, almond butter, peanut butter natural, chia seeds, flax seeds ground, hemp seeds, pumpkin seeds, sunflower seeds
   - Schema: `external_source="manual"`, `external_id="manual_<slug>"`, full macros, `quality_flag="manual_verified"`, `needs_review=True`, `dietary_tags_jsonb` (e.g. `["vegetarian"]` or `["vegan"]`).
   - verify: JSON parses; every entry has all required fields; no duplicate `external_id`

5. **Create `scripts/data/curated_meals.json`**
   - ~100 manual meal entries spanning meal_types:
     - Breakfast (~25): idli sambar, dosa+chutney, paneer paratha, oats+fruit bowls, smoothie bowls, avocado toast variants, greek yogurt parfaits, scrambled tofu, masala omelette
     - Lunch (~30): dal+rice combos, rajma chawal, chana masala+roti, paneer tikka bowl, hummus+pita+veg, mediterranean grain bowls, burrito bowls, bibimbap-style, soba bowls
     - Dinner (~30): grilled fish + sides (salmon, mackerel, sardines variants), chicken curry+rice, tofu stir-fry, lentil soups, baked cod + veg, tempeh stir-fry, mediterranean salmon plate
     - Snack (~10): yogurt+nuts, hummus+veg sticks, fruit+nut butter, trail mix, seed crackers
     - Flare-day (~5): congee, kitchari, bone broth + soft veg, plain rice + steamed fish, banana oat porridge
   - Schema:
     ```json
     {
       "name": "...", "meal_type": "lunch", "cuisine_type": "indian",
       "is_vegetarian": true, "is_flare_friendly": false,
       "tags": ["vegetarian","high_protein"],
       "dietary_tags_jsonb": ["vegetarian"],
       "reason_tags_jsonb": ["protein_boost"],
       "prep_time_minutes": 25, "effort_level": "medium",
       "serving_size_description": "1 bowl (~350g)",
       "instructions": "...",
       "ingredients": [{"food_name": "paneer", "portion_g": 100}, ...]
     }
     ```
   - verify: every `food_name` resolvable via existing ALIASES or new manual aliases; `meal_type` in valid set; `is_flare_friendly=True` only on flare-day or genuinely gentle meals

---

## Phase 3 — Loader Script

6. **Create `scripts/seed_curated.py`**
   - CLI flags: `--dry-run`, `--foods-only`, `--meals-only`, `--limit N`
   - Steps:
     a. Load JSON files; validate schema (raise on missing fields, invalid meal_type, score out of range, cooking_state invalid)
     b. **Foods**: for each, upsert into `static.foods` ON CONFLICT (`external_source`, `external_id`) DO UPDATE. After insert, run `calculate_anti_inflammatory_score(food)` → write back.
     c. Build manual alias map: `{slug: food_id}` for ingredient lookup
     d. **Meals**: for each, check `LOWER(name)` not in existing meal names → skip if dup. Compute totals from `MealIngredient(portion_g) × Food(per-100g macros)` (mirror logic in `seed_meals.py`). Compute meal AI score from ingredient scores (avg or use existing helper).
     e. **Animal-ingredient guard**: if any ingredient food has category in {"meat","fish","poultry","dairy_egg"} OR name matches animal whitelist (chicken|fish|salmon|tuna|egg|cod|tilapia|prawn|shrimp|mackerel|sardine|trout|herring|beef|pork|lamb|chicken broth|bone broth) → force `is_vegetarian=False`, strip `vegetarian`/`vegan` from `tags` + `dietary_tags_jsonb`. Log warning.
     f. Wrap whole run in single transaction. Print summary: foods inserted/updated/skipped, meals inserted/skipped.
   - verify: `--dry-run` prints plan w/o writing; real run leaves DB consistent

7. **Create `scripts/unseed_curated.py`**
   - Delete meals WHERE name IN (curated_meals.json names) AND no row in `recommendation_logs` references them; print blocked deletes.
   - Delete foods WHERE `external_source='manual'` AND no row in `meal_ingredients` / `food_logs` references them; print blocked.
   - verify: dry-run flag; transactional

---

## Phase 4 — Test Adjustments

8. **Fix tests broken by audit**
   - Replace hard-coded counts with `>=` assertions where appropriate
   - For tests requiring fixed seed: gate via `pytest` fixture using minimal in-memory dataset rather than full prod seed
   - verify: `pytest tests/` green before + after seed

9. **Add new test `tests/scripts/test_seed_curated.py`**
   - Cases:
     - Loader rejects invalid meal_type
     - Loader rejects out-of-range score
     - Animal-ingredient guard flips `is_vegetarian` to False
     - Idempotent: run twice → same row counts
     - Unseed removes only manual rows; preserves USDA/seed_meals data
   - verify: all pass

---

## Phase 5 — Run + Verify

10. **Run loader on dev DB**
    - `python scripts/seed_curated.py --dry-run` → review output
    - `python scripts/seed_curated.py` → execute
    - verify: counts increased to ~90 foods, ~200 meals; no constraint violations in logs

11. **Smoke recommendation loop**
    - `python scripts/week6_smoke.py` (or equivalent)
    - Hit `/recommendations/next` for each meal_type with vegetarian + non-vegetarian users
    - verify: returns valid meal; no 500s; diet filter respected; new manual meals appear in pool

12. **Test suite**
    - `pytest tests/`
    - verify: all green

13. **Frontend smoke**
    - Open `MealLogPage`, `RecommendationPage` in browser
    - verify: new meals render; no console errors

---

## Phase 6 — Wrap

14. **Update `Summaries/week7_curated_seed.md`**
    - What added, file list, run commands, rollback steps

15. **Mark tasks complete in this file**

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Manual macros wrong → bad ranking | `quality_flag=manual_verified` + `needs_review=True`; future audit |
| Diet flag wrong → vegetarian gets meat | Animal-ingredient guard in loader |
| Test count assertions break | Phase 1 audit, Phase 4 fixes |
| Seed not idempotent | Upsert foods, name-dedupe meals |
| FK blocks cleanup | Unseed script checks `recommendation_logs`/`food_logs` first |
| Constraint violations mid-run | Pre-validate JSON; transactional |
| AI score drift | Always recompute via `calculate_anti_inflammatory_score`; never hardcode |

---

## Sonnet Agent Dispatch

After plan approval, launch sonnet subagent with:
- Scope: Phases 2 → 5 (data files, loader, unseed, tests, run)
- Context handoff: this plan + project CLAUDE.md
- Stop conditions: dry-run output reviewed before real run; pytest must pass before declaring done
- Out of scope: rule_engine.py, schema, migrations, recommendation_service.py

---

## Review Section
(Populated when complete)
- Foods added: TBD
- Meals added: TBD
- Tests modified: TBD
- Issues encountered: TBD
