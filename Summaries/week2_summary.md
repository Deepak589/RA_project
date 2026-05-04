# Week 2 Summary

## Final Table Set

The Week 2 database design ships with 12 tables:

1. `core.users`
2. `core.user_preferences`
3. `core.user_medications`
4. `core.authentication_sessions`
5. `core.account_deletion_requests`
6. `static.foods`
7. `static.meals`
8. `static.meal_items`
9. `tracking.food_logs`
10. `tracking.symptom_logs`
11. `tracking.lifestyle_logs`
12. `intelligence.recommendation_logs`

## Key Design Decisions

- [DESIGN DECISION: kept Week 2 at 12 tables instead of splitting `feedback_logs` out as a 13th table.] Week 1 already modeled recommendation feedback directly on `recommendation_logs`, and the Week 2 task list explicitly scoped the ER diagram and migration to 12 tables.
- [REVISIT IN V2: split feedback into a dedicated `feedback_logs` table once recommendation analytics, auditing, or repeated feedback events become heavier.] Merging feedback into `recommendation_logs` is correct for V1, but it will become limiting once analytics need higher event granularity.
- Used four PostgreSQL schemas (`core`, `static`, `tracking`, `intelligence`) to separate identity, reference data, user-generated tracking data, and derived recommendation data.
- Standardized on UUID primary keys, `TIMESTAMPTZ`, and `JSONB` so the API can safely scale across clients and time zones.
- Stored `flare_level` and `feedback_status` as native PostgreSQL enums to make rule-engine and analytics queries safer.
- Added partial uniqueness for pending account deletion requests so a user cannot create multiple active deletion jobs.

## Differences From Week 1 Appendix

- Added `core.account_deletion_requests` because account deletion is in V1 scope.
- Added `metadata_jsonb` to `static.foods` to preserve raw USDA attributes without forcing immediate column growth.
- Added `replacement_meal_id` to `intelligence.recommendation_logs` so a replaced recommendation can point to either a logged food or another curated meal.
- Renamed nothing in the persisted model, but clarified that `authentication_sessions` is the canonical table name behind the Week 1 shorthand of auth sessions.

## Ready For Week 3

- PostgreSQL DDL is defined in `database/schema.sql`.
- Mermaid ER diagram is defined in `database/er_diagram.mmd`.
- Alembic initial migration is in `alembic/versions/0001_initial_schema.py`.
- SQLAlchemy 2.0 models, Pydantic v2 schemas, DB session wiring, security helpers, and Docker setup are scaffolded.
- The live PostgreSQL database is up and verified with 4 schemas and 12 tables.
- `core.alembic_version` is recorded with `0001_initial_schema` as the Week 2 baseline.
- The backend is ready for Week 3 nutrition ingestion and initial CRUD route work.

## Open Questions And Assumptions

- USDA ingestion may need additional normalized nutrient tables if Week 3 wants more than the current V1 nutrient subset.
- [REVISIT IN V2: `user_preferences` currently stores diet and goal arrays in JSONB for V1 flexibility.] If Week 5 rule-engine work or later analytics need cross-user filtering by dietary preference, exclusions, or goals, JSONB array scans will become inefficient and should move to normalized join tables.
- Severity escalation is modeled with `escalation_triggered`; clinician review of copy and thresholds is still required before user testing.
- [DESIGN DECISION: live schema was applied and then aligned to Alembic baseline.] During verification, the canonical SQL in `database/schema.sql` was applied to the Docker PostgreSQL instance and the Alembic baseline was recorded as `0001_initial_schema`.
- [DESIGN DECISION: this project now uses a Docker-first database workflow.] Runtime database access should use `db:5432` from the API and Alembic containers; host-side `localhost` checks were only used for debugging and can hit a different local PostgreSQL instance.
- Docker Postgres currently reflects the credential state from its existing persisted volume. If Week 3 wants Docker credentials to match a newly edited `.env` password exactly, reset the Postgres volume or change the DB user password inside the running instance.
