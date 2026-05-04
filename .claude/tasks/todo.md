# Active Tasks

## Week 7 bugs (blocking Week 8)
- [ ] Fix custom meal builder: chicken/ingredients not persisting to food log (no `log_source: "custom_meal"` rows in `tracking.food_logs`)
- [ ] Investigate flaky auth session — "staying logged in sometimes behaving differently"
- [ ] Manual browser click-through: all 11 Week 7 screens against live API
- [ ] Run full backend pytest suite in real Docker env (was blocked by `db` host resolution)

## Week 8 prep (after bugs cleared)
- [ ] Decide analytics chart priority: nutrition adherence / symptom correlation / flare frequency / recommendation acceptance
- [ ] Decide if backend should set refresh tokens as httpOnly cookies (currently JSON body)
- [ ] Add seed script for first admin account

## Open architecture questions
- [ ] Cooking state — promote from name-inferred to real DB column?
- [ ] Should V2 split `feedback_logs` out of `recommendation_logs`?
- [ ] When does dietary_flags JSONB become a normalized join table?
