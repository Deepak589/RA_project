# Week 7 Bug 3 Summary

## 1. Scope Completed

- Fixed the recommendation-engine ranking loop in normal, mixed, and flare-only modes.
- Updated the service contract tests to reflect the new shuffle-first ranking behavior.
- Refreshed the Graphify code graph successfully using the installed Python CLI instead of the broken `npx` path.

---

## 2. Bug Fixed

### BUG 3 — Recommendation engine keeps surfacing the same meals in a loop

**Root cause:** `app/services/rule_engine.py` seeded every candidate meal with
`adjusted_score = _score(meal)` before ranking. That made `anti_inflammatory_score` the
default tie-breaker even in normal mode, so the same high-score meals kept floating back to the
top instead of showing natural variety.

**Files changed:**

- `app/services/rule_engine.py`
  - Added `import random`.
  - Removed the early loop that preloaded `adjusted_score` from `_score(meal)` before ranking.
  - Changed the explicit `flare_active` query override so:
    - `flare_active=True` immediately forces `recommendation_mode = "flare_only"`
    - the mode is set before any symptom-log lookup path is used
    - an audit log entry is appended: `[QUERY: flare_active=true → flare_only mode]`
  - Tightened `_apply_preferences(...)` so dietary flags are a true hard filter:
    - `has_real_preference = bool(active_dietary_flags) and "no_preference" not in flags`
    - meals that do not match an active dietary preference are removed from the candidate list
    - no fallback score penalty is applied when the preference is active
  - Reworked `_final_rank(...)`:
    - `normal` mode now shuffles meals within equal-priority groups instead of score-sorting
    - `flare_only` now keeps flare-friendly meals first, then shuffles within flare and non-flare groups
    - `mixed` now puts all flare-friendly meals first, then shuffles within flare and non-flare groups
  - Added `_priority_delta(meal)` so ranking still respects actual rule-driven score adjustments:
    - medication boosts
    - nutrition gap boosts
    - cuisine / budget preference boosts
    - variety penalty adjustments
    - while no longer using raw anti-inflammatory score as the normal-mode default ordering key

**Behavior after fix:**

- Dietary preference remains a hard eligibility filter.
- Symptom/lifestyle rule selection still controls `normal`, `mixed`, and `flare_only`.
- Nutrition and medication adjustments still matter.
- Variety penalty still matters.
- Raw anti-inflammatory score no longer causes the same meals to dominate normal-mode results.

---

## 3. Tests Updated

- `tests/services/test_week6_contracts.py`
  - Replaced the old score-order assumptions with deterministic shuffle-based expectations by monkeypatching `random.shuffle`.
  - Verified:
    - normal mode shuffles the full list
    - flare-only keeps flare-friendly meals first, then shuffles within groups
    - mixed keeps all flare-friendly meals before non-flare meals, then shuffles within groups

---

## 4. Verification Results

- Docker-backed service verification passed:
  - `docker compose exec -T api pytest tests/services/test_variety_penalty.py -x -q`
  - Result: `8 passed`
- Remaining service verification passed:
  - `docker compose exec -T api pytest tests/services/ -x -q --ignore=tests/services/test_variety_penalty.py`
  - Result: `70 passed`

---

## 5. Graph Update

- Graphify refresh succeeded on 2026-05-07 using:
  - `C:\Users\Deepak\AppData\Local\Programs\Python\Python312\python.exe -m graphify update .`
- This bypassed the earlier broken `npx graphify update .` path.
- Updated graph output was regenerated in `graphify-out/`.
- Current code-graph snapshot after the refresh:
  - `723 nodes`
  - `1409 edges`
  - `69 communities`

---

## 6. Key Takeaway

- The recommendation engine now uses shuffle-based variety for user-facing ranking while still
  honoring real rule-based boosts and repeat-meal penalties.
- This keeps the V1 rule system deterministic where it needs to be, but stops normal mode from
  behaving like a fixed anti-inflammatory leaderboard.

---

✓ WEEK 7 BUG 3 COMPLETE — recommendation ranking no longer defaults to anti-inflammatory score in normal mode, dietary preference remains a hard filter, explicit flare query override is honored, service tests pass in Docker, and Graphify was successfully refreshed
