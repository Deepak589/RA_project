CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS static;
CREATE SCHEMA IF NOT EXISTS tracking;
CREATE SCHEMA IF NOT EXISTS intelligence;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'flare_level'
          AND n.nspname = 'tracking'
    ) THEN
        CREATE TYPE tracking.flare_level AS ENUM ('none', 'mild', 'moderate', 'severe');
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'feedback_status'
          AND n.nspname = 'intelligence'
    ) THEN
        CREATE TYPE intelligence.feedback_status AS ENUM ('pending', 'accepted', 'skipped', 'replaced');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS core.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    CHECK (char_length(trim(email)) > 3),
    CHECK (char_length(trim(full_name)) > 0),
    CHECK (char_length(trim(timezone)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_core_users_email_lower
    ON core.users (LOWER(email));

CREATE TABLE IF NOT EXISTS core.user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES core.users(id) ON DELETE CASCADE,
    allergies_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    dietary_flags_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    disliked_foods_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    goal_flags_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE,
    disclaimer_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    disclaimer_accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (disclaimer_accepted = FALSE AND disclaimer_accepted_at IS NULL)
        OR (disclaimer_accepted = TRUE AND disclaimer_accepted_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_core_user_preferences_user_id
    ON core.user_preferences (user_id);

CREATE TABLE IF NOT EXISTS core.user_medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    medication_name TEXT NOT NULL,
    schedule_note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (char_length(trim(medication_name)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_core_user_medications_user_id
    ON core.user_medications (user_id);

CREATE INDEX IF NOT EXISTS ix_core_user_medications_user_id_is_active
    ON core.user_medications (user_id, is_active);

CREATE TABLE IF NOT EXISTS core.authentication_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (expires_at > issued_at)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_core_authentication_sessions_refresh_token_hash
    ON core.authentication_sessions (refresh_token_hash);

CREATE INDEX IF NOT EXISTS ix_core_authentication_sessions_user_id
    ON core.authentication_sessions (user_id);

CREATE TABLE IF NOT EXISTS core.account_deletion_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scheduled_for TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (status IN ('pending', 'cancelled', 'completed')),
    CHECK (scheduled_for >= requested_at),
    CHECK (
        processed_at IS NULL
        OR processed_at >= requested_at
    )
);

CREATE INDEX IF NOT EXISTS ix_core_account_deletion_requests_user_id
    ON core.account_deletion_requests (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_core_account_deletion_requests_user_pending
    ON core.account_deletion_requests (user_id)
    WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS static.foods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_source TEXT NOT NULL DEFAULT 'usda',
    external_id TEXT NOT NULL,
    name TEXT NOT NULL,
    brand_name TEXT,
    category TEXT,
    serving_size_g NUMERIC(8, 2),
    calories NUMERIC(8, 2),
    protein_g NUMERIC(8, 2),
    carbs_g NUMERIC(8, 2),
    fat_g NUMERIC(8, 2),
    saturated_fat_g NUMERIC(8, 2) NOT NULL DEFAULT 0,
    fiber_g NUMERIC(8, 2),
    sugar_g NUMERIC(8, 2),
    sodium_mg NUMERIC(10, 2),
    omega3_g NUMERIC(8, 3),
    calcium_mg NUMERIC(10, 2) NOT NULL DEFAULT 0,
    vitamin_d_ug NUMERIC(8, 2) NOT NULL DEFAULT 0,
    anti_inflammatory_score NUMERIC(4, 1) NOT NULL DEFAULT 0,
    ingredients_text TEXT,
    dietary_tags_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_jsonb JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (char_length(trim(name)) > 0),
    CHECK (serving_size_g IS NULL OR serving_size_g >= 0),
    CHECK (calories IS NULL OR calories >= 0),
    CHECK (protein_g IS NULL OR protein_g >= 0),
    CHECK (carbs_g IS NULL OR carbs_g >= 0),
    CHECK (fat_g IS NULL OR fat_g >= 0),
    CHECK (saturated_fat_g >= 0),
    CHECK (fiber_g IS NULL OR fiber_g >= 0),
    CHECK (sugar_g IS NULL OR sugar_g >= 0),
    CHECK (sodium_mg IS NULL OR sodium_mg >= 0),
    CHECK (omega3_g IS NULL OR omega3_g >= 0),
    CHECK (calcium_mg >= 0),
    CHECK (vitamin_d_ug >= 0),
    CHECK (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_static_foods_external_source_external_id
    ON static.foods (external_source, external_id);

CREATE INDEX IF NOT EXISTS ix_static_foods_name_lower
    ON static.foods (LOWER(name));

CREATE TABLE IF NOT EXISTS static.meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    meal_type TEXT NOT NULL,
    prep_time_minutes INTEGER NOT NULL DEFAULT 0,
    anti_inflammatory_score NUMERIC(5, 2) NOT NULL DEFAULT 0,
    protein_g NUMERIC(8, 2),
    fiber_g NUMERIC(8, 2),
    sugar_g NUMERIC(8, 2),
    sodium_mg NUMERIC(10, 2),
    calories NUMERIC(8, 2),
    is_curated BOOLEAN NOT NULL DEFAULT TRUE,
    dietary_tags_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    reason_tags_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'any')),
    CHECK (prep_time_minutes >= 0),
    CHECK (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 100),
    CHECK (protein_g IS NULL OR protein_g >= 0),
    CHECK (fiber_g IS NULL OR fiber_g >= 0),
    CHECK (sugar_g IS NULL OR sugar_g >= 0),
    CHECK (sodium_mg IS NULL OR sodium_mg >= 0),
    CHECK (calories IS NULL OR calories >= 0)
);

CREATE INDEX IF NOT EXISTS ix_static_meals_meal_type
    ON static.meals (meal_type);

CREATE INDEX IF NOT EXISTS ix_static_meals_is_curated
    ON static.meals (is_curated);

CREATE INDEX IF NOT EXISTS ix_static_meals_name_lower
    ON static.meals (LOWER(name));

CREATE TABLE IF NOT EXISTS static.meal_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meal_id UUID NOT NULL REFERENCES static.meals(id) ON DELETE CASCADE,
    food_id UUID NOT NULL REFERENCES static.foods(id) ON DELETE RESTRICT,
    quantity NUMERIC(8, 2) NOT NULL,
    unit TEXT NOT NULL,
    grams NUMERIC(8, 2) NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (quantity > 0),
    CHECK (grams > 0),
    CHECK (char_length(trim(unit)) > 0)
);

CREATE INDEX IF NOT EXISTS ix_static_meal_items_meal_id
    ON static.meal_items (meal_id);

CREATE INDEX IF NOT EXISTS ix_static_meal_items_food_id
    ON static.meal_items (food_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_static_meal_items_meal_id_sort_order
    ON static.meal_items (meal_id, sort_order);

CREATE TABLE IF NOT EXISTS tracking.food_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    food_id UUID REFERENCES static.foods(id) ON DELETE SET NULL,
    meal_id UUID REFERENCES static.meals(id) ON DELETE SET NULL,
    custom_food_name TEXT,
    meal_type TEXT NOT NULL,
    portion_g NUMERIC(8, 2),
    portion_label TEXT,
    notes TEXT,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    CHECK (portion_g IS NULL OR portion_g > 0),
    CHECK (num_nonnulls(food_id, meal_id, custom_food_name) = 1)
);

CREATE INDEX IF NOT EXISTS ix_tracking_food_logs_user_id_logged_at
    ON tracking.food_logs (user_id, logged_at);

CREATE INDEX IF NOT EXISTS ix_tracking_food_logs_logged_at
    ON tracking.food_logs (logged_at);

CREATE TABLE IF NOT EXISTS tracking.symptom_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    pain_score SMALLINT NOT NULL,
    fatigue_score SMALLINT NOT NULL,
    stiffness_score SMALLINT NOT NULL,
    swelling_score SMALLINT NOT NULL,
    flare_level tracking.flare_level NOT NULL DEFAULT 'none',
    note TEXT,
    escalation_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (pain_score BETWEEN 0 AND 10),
    CHECK (fatigue_score BETWEEN 0 AND 10),
    CHECK (stiffness_score BETWEEN 0 AND 10),
    CHECK (swelling_score BETWEEN 0 AND 10)
);

CREATE INDEX IF NOT EXISTS ix_tracking_symptom_logs_user_id_logged_at
    ON tracking.symptom_logs (user_id, logged_at);

CREATE INDEX IF NOT EXISTS ix_tracking_symptom_logs_logged_at
    ON tracking.symptom_logs (logged_at);

CREATE TABLE IF NOT EXISTS tracking.lifestyle_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    log_date DATE NOT NULL,
    sleep_hours NUMERIC(4, 2),
    steps INTEGER,
    water_ml INTEGER,
    stress_level SMALLINT,
    medication_taken BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (sleep_hours IS NULL OR (sleep_hours >= 0 AND sleep_hours <= 24)),
    CHECK (steps IS NULL OR steps >= 0),
    CHECK (water_ml IS NULL OR water_ml >= 0),
    CHECK (stress_level IS NULL OR stress_level BETWEEN 0 AND 10),
    UNIQUE (user_id, log_date)
);

CREATE INDEX IF NOT EXISTS ix_tracking_lifestyle_logs_user_id_log_date
    ON tracking.lifestyle_logs (user_id, log_date);

CREATE TABLE IF NOT EXISTS intelligence.recommendation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    meal_id UUID REFERENCES static.meals(id) ON DELETE SET NULL,
    recommended_for_meal_type TEXT NOT NULL,
    recommendation_context_jsonb JSONB NOT NULL DEFAULT '{}'::jsonb,
    explanation_text TEXT NOT NULL,
    alternatives_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    rules_applied_jsonb JSONB NOT NULL DEFAULT '[]'::jsonb,
    shown_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    feedback_status intelligence.feedback_status NOT NULL DEFAULT 'pending',
    feedback_reason TEXT,
    replacement_food_id UUID REFERENCES static.foods(id) ON DELETE SET NULL,
    replacement_meal_id UUID REFERENCES static.meals(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (recommended_for_meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    CHECK (
        feedback_status <> 'replaced'
        OR num_nonnulls(replacement_food_id, replacement_meal_id) = 1
    )
);

CREATE INDEX IF NOT EXISTS ix_intelligence_recommendation_logs_user_id_shown_at
    ON intelligence.recommendation_logs (user_id, shown_at);

CREATE INDEX IF NOT EXISTS ix_intelligence_recommendation_logs_feedback_status
    ON intelligence.recommendation_logs (feedback_status);
