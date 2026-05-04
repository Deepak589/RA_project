# Lessons (most recent at bottom — Claude reads last 10 lines)

## Format
- One lesson per line, format: `YYYY-MM-DD: <terse rule, imperative voice>`
- Keep <120 chars. Old lessons archive to lessons.archive.md when file >200 lines.
- Only "things we shouldn't repeat" — not general knowledge. Graphify handles general state.

---
2026-04-15: Don't use passlib's bcrypt wrapper — incompatible at runtime; call bcrypt directly, still produces bcrypt hashes.
2026-04-16: Frontend Vite proxy needs VITE_API_BASE_URL empty (use /api proxy) — full URL triggers CORS preflight failures.
2026-04-10: Docker Postgres is `db:5432` from API container, `localhost` only from host shell. Don't mix.
2026-04-12: Alembic — never reuse migration numbers. If chain has 0003_food_source already, next is 0004, not another 0003.
2026-04-22: Route order matters in FastAPI — define `/search` and `/categories` BEFORE `/{food_id}` or path conflicts win.
2026-04-25: Recommendation logs need `recommendation_log_id` returned in response — frontend feedback POST silently fails without it.
2026-04-28: CORS allow_credentials=true requires explicit allow_origins, NOT wildcard ["*"]. Browser blocks otherwise.
2026-04-30: USDA Foundation foods inconsistent — always provide nutrient ID fallbacks (1008→2047 for calories, etc.).
2026-05-01: Variety penalty tiers must be strong (-2, -4, -6) — weak penalties (-0.5) ignored by ranking, salmon dominates.
2026-05-02: Always invalidate ["dashboard","weekly"] AND ["dashboard","today"] AND ["food-logs","today"] after any log mutation.