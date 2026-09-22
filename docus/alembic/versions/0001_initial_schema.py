"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-18 12:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


flare_level_enum = postgresql.ENUM(
    "none",
    "mild",
    "moderate",
    "severe",
    name="flare_level",
    schema="tracking",
    create_type=False,
)

feedback_status_enum = postgresql.ENUM(
    "pending",
    "accepted",
    "skipped",
    "replaced",
    name="feedback_status",
    schema="intelligence",
    create_type=False,
)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS static")
    op.execute("CREATE SCHEMA IF NOT EXISTS tracking")
    op.execute("CREATE SCHEMA IF NOT EXISTS intelligence")

    flare_level_enum.create(op.get_bind(), checkfirst=True)
    feedback_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False, server_default=sa.text("'UTC'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(trim(email)) > 3", name="email_length"),
        sa.CheckConstraint("char_length(trim(full_name)) > 0", name="full_name_not_blank"),
        sa.CheckConstraint("char_length(trim(timezone)) > 0", name="timezone_not_blank"),
        schema="core",
    )
    op.create_index(
        "ix_core_users_email_lower",
        "users",
        [sa.text("LOWER(email)")],
        unique=True,
        schema="core",
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("allergies_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("dietary_flags_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("disliked_foods_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("goal_flags_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("disclaimer_accepted", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("disclaimer_accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "((disclaimer_accepted = FALSE AND disclaimer_accepted_at IS NULL) OR "
            "(disclaimer_accepted = TRUE AND disclaimer_accepted_at IS NOT NULL))",
            name="disclaimer_acceptance_consistent",
        ),
        sa.UniqueConstraint("user_id", name="uq_core_user_preferences_user_id"),
        schema="core",
    )

    op.create_table(
        "user_medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("medication_name", sa.Text(), nullable=False),
        sa.Column("schedule_note", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("char_length(trim(medication_name)) > 0", name="medication_name_not_blank"),
        schema="core",
    )
    op.create_index("ix_core_user_medications_user_id", "user_medications", ["user_id"], unique=False, schema="core")
    op.create_index(
        "ix_core_user_medications_user_id_is_active",
        "user_medications",
        ["user_id", "is_active"],
        unique=False,
        schema="core",
    )

    op.create_table(
        "authentication_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.Text(), nullable=False),
        sa.Column("issued_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("expires_at > issued_at", name="expires_after_issue"),
        schema="core",
    )
    op.create_index(
        "ix_core_authentication_sessions_refresh_token_hash",
        "authentication_sessions",
        ["refresh_token_hash"],
        unique=True,
        schema="core",
    )
    op.create_index("ix_core_authentication_sessions_user_id", "authentication_sessions", ["user_id"], unique=False, schema="core")

    op.create_table(
        "account_deletion_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("requested_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("scheduled_for", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('pending', 'cancelled', 'completed')", name="valid_status"),
        sa.CheckConstraint("scheduled_for >= requested_at", name="scheduled_after_request"),
        sa.CheckConstraint("(processed_at IS NULL OR processed_at >= requested_at)", name="processed_after_request"),
        schema="core",
    )
    op.create_index("ix_core_account_deletion_requests_user_id", "account_deletion_requests", ["user_id"], unique=False, schema="core")
    op.create_index(
        "ux_core_account_deletion_requests_user_pending",
        "account_deletion_requests",
        ["user_id"],
        unique=True,
        schema="core",
        postgresql_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "foods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("external_source", sa.Text(), nullable=False, server_default=sa.text("'usda_fdc'")),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("brand_name", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("serving_size_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("calories", sa.Numeric(8, 2), nullable=True),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("fiber_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(10, 2), nullable=True),
        sa.Column("omega3_g", sa.Numeric(8, 3), nullable=True),
        sa.Column("ingredients_text", sa.Text(), nullable=True),
        sa.Column("dietary_tags_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("char_length(trim(name)) > 0", name="food_name_not_blank"),
        sa.CheckConstraint("(serving_size_g IS NULL OR serving_size_g >= 0)", name="serving_size_non_negative"),
        sa.CheckConstraint("(calories IS NULL OR calories >= 0)", name="calories_non_negative"),
        sa.CheckConstraint("(protein_g IS NULL OR protein_g >= 0)", name="protein_non_negative"),
        sa.CheckConstraint("(carbs_g IS NULL OR carbs_g >= 0)", name="carbs_non_negative"),
        sa.CheckConstraint("(fat_g IS NULL OR fat_g >= 0)", name="fat_non_negative"),
        sa.CheckConstraint("(fiber_g IS NULL OR fiber_g >= 0)", name="fiber_non_negative"),
        sa.CheckConstraint("(sugar_g IS NULL OR sugar_g >= 0)", name="sugar_non_negative"),
        sa.CheckConstraint("(sodium_mg IS NULL OR sodium_mg >= 0)", name="sodium_non_negative"),
        sa.CheckConstraint("(omega3_g IS NULL OR omega3_g >= 0)", name="omega3_non_negative"),
        schema="static",
    )
    op.create_index(
        "ux_static_foods_external_source_external_id",
        "foods",
        ["external_source", "external_id"],
        unique=True,
        schema="static",
    )
    op.create_index("ix_static_foods_name_lower", "foods", [sa.text("LOWER(name)")], unique=False, schema="static")

    op.create_table(
        "meals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("meal_type", sa.Text(), nullable=False),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("anti_inflammatory_score", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("fiber_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(10, 2), nullable=True),
        sa.Column("calories", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_curated", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("dietary_tags_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reason_tags_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'any')", name="valid_meal_type"),
        sa.CheckConstraint("prep_time_minutes >= 0", name="prep_time_non_negative"),
        sa.CheckConstraint("(anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 100)", name="score_between_0_100"),
        sa.CheckConstraint("(protein_g IS NULL OR protein_g >= 0)", name="meal_protein_non_negative"),
        sa.CheckConstraint("(fiber_g IS NULL OR fiber_g >= 0)", name="meal_fiber_non_negative"),
        sa.CheckConstraint("(sugar_g IS NULL OR sugar_g >= 0)", name="meal_sugar_non_negative"),
        sa.CheckConstraint("(sodium_mg IS NULL OR sodium_mg >= 0)", name="meal_sodium_non_negative"),
        sa.CheckConstraint("(calories IS NULL OR calories >= 0)", name="meal_calories_non_negative"),
        schema="static",
    )
    op.create_index("ix_static_meals_meal_type", "meals", ["meal_type"], unique=False, schema="static")
    op.create_index("ix_static_meals_is_curated", "meals", ["is_curated"], unique=False, schema="static")
    op.create_index("ix_static_meals_name_lower", "meals", [sa.text("LOWER(name)")], unique=False, schema="static")

    op.create_table(
        "meal_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.meals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(8, 2), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("grams", sa.Numeric(8, 2), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("quantity > 0", name="quantity_positive"),
        sa.CheckConstraint("grams > 0", name="grams_positive"),
        sa.CheckConstraint("char_length(trim(unit)) > 0", name="unit_not_blank"),
        schema="static",
    )
    op.create_index("ix_static_meal_items_meal_id", "meal_items", ["meal_id"], unique=False, schema="static")
    op.create_index("ix_static_meal_items_food_id", "meal_items", ["food_id"], unique=False, schema="static")
    op.create_index(
        "ux_static_meal_items_meal_id_sort_order",
        "meal_items",
        ["meal_id", "sort_order"],
        unique=True,
        schema="static",
    )

    op.create_table(
        "food_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.foods.id", ondelete="SET NULL"), nullable=True),
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("custom_food_name", sa.Text(), nullable=True),
        sa.Column("meal_type", sa.Text(), nullable=False),
        sa.Column("portion_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("portion_label", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("logged_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')", name="valid_food_log_meal_type"),
        sa.CheckConstraint("(portion_g IS NULL OR portion_g > 0)", name="portion_positive"),
        sa.CheckConstraint("num_nonnulls(food_id, meal_id, custom_food_name) = 1", name="single_log_source"),
        schema="tracking",
    )
    op.create_index("ix_tracking_food_logs_logged_at", "food_logs", ["logged_at"], unique=False, schema="tracking")
    op.create_index(
        "ix_tracking_food_logs_user_id_logged_at",
        "food_logs",
        ["user_id", "logged_at"],
        unique=False,
        schema="tracking",
    )

    op.create_table(
        "symptom_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pain_score", sa.SmallInteger(), nullable=False),
        sa.Column("fatigue_score", sa.SmallInteger(), nullable=False),
        sa.Column("stiffness_score", sa.SmallInteger(), nullable=False),
        sa.Column("swelling_score", sa.SmallInteger(), nullable=False),
        sa.Column("flare_level", flare_level_enum, nullable=False, server_default=sa.text("'none'")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("escalation_triggered", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("logged_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("pain_score BETWEEN 0 AND 10", name="pain_score_range"),
        sa.CheckConstraint("fatigue_score BETWEEN 0 AND 10", name="fatigue_score_range"),
        sa.CheckConstraint("stiffness_score BETWEEN 0 AND 10", name="stiffness_score_range"),
        sa.CheckConstraint("swelling_score BETWEEN 0 AND 10", name="swelling_score_range"),
        schema="tracking",
    )
    op.create_index("ix_tracking_symptom_logs_logged_at", "symptom_logs", ["logged_at"], unique=False, schema="tracking")
    op.create_index(
        "ix_tracking_symptom_logs_user_id_logged_at",
        "symptom_logs",
        ["user_id", "logged_at"],
        unique=False,
        schema="tracking",
    )

    op.create_table(
        "lifestyle_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("sleep_hours", sa.Numeric(4, 2), nullable=True),
        sa.Column("steps", sa.Integer(), nullable=True),
        sa.Column("water_ml", sa.Integer(), nullable=True),
        sa.Column("stress_level", sa.SmallInteger(), nullable=True),
        sa.Column("medication_taken", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("(sleep_hours IS NULL OR (sleep_hours >= 0 AND sleep_hours <= 24))", name="sleep_hours_range"),
        sa.CheckConstraint("(steps IS NULL OR steps >= 0)", name="steps_non_negative"),
        sa.CheckConstraint("(water_ml IS NULL OR water_ml >= 0)", name="water_non_negative"),
        sa.CheckConstraint("(stress_level IS NULL OR stress_level BETWEEN 0 AND 10)", name="stress_range"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_tracking_lifestyle_logs_user_log_date"),
        schema="tracking",
    )
    op.create_index(
        "ix_tracking_lifestyle_logs_user_id_log_date",
        "lifestyle_logs",
        ["user_id", "log_date"],
        unique=False,
        schema="tracking",
    )

    op.create_table(
        "recommendation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommended_for_meal_type", sa.Text(), nullable=False),
        sa.Column("recommendation_context_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("explanation_text", sa.Text(), nullable=False),
        sa.Column("alternatives_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("rules_applied_jsonb", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("shown_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("feedback_status", feedback_status_enum, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("feedback_reason", sa.Text(), nullable=True),
        sa.Column("replacement_food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.foods.id", ondelete="SET NULL"), nullable=True),
        sa.Column("replacement_meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.meals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "recommended_for_meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')",
            name="valid_recommendation_meal_type",
        ),
        sa.CheckConstraint(
            "(feedback_status <> 'replaced' OR num_nonnulls(replacement_food_id, replacement_meal_id) = 1)",
            name="replacement_target_required",
        ),
        schema="intelligence",
    )
    op.create_index(
        "ix_intelligence_recommendation_logs_feedback_status",
        "recommendation_logs",
        ["feedback_status"],
        unique=False,
        schema="intelligence",
    )
    op.create_index(
        "ix_intelligence_recommendation_logs_user_id_shown_at",
        "recommendation_logs",
        ["user_id", "shown_at"],
        unique=False,
        schema="intelligence",
    )


def downgrade() -> None:
    op.drop_index("ix_intelligence_recommendation_logs_user_id_shown_at", table_name="recommendation_logs", schema="intelligence")
    op.drop_index("ix_intelligence_recommendation_logs_feedback_status", table_name="recommendation_logs", schema="intelligence")
    op.drop_table("recommendation_logs", schema="intelligence")

    op.drop_index("ix_tracking_lifestyle_logs_user_id_log_date", table_name="lifestyle_logs", schema="tracking")
    op.drop_table("lifestyle_logs", schema="tracking")

    op.drop_index("ix_tracking_symptom_logs_user_id_logged_at", table_name="symptom_logs", schema="tracking")
    op.drop_index("ix_tracking_symptom_logs_logged_at", table_name="symptom_logs", schema="tracking")
    op.drop_table("symptom_logs", schema="tracking")

    op.drop_index("ix_tracking_food_logs_user_id_logged_at", table_name="food_logs", schema="tracking")
    op.drop_index("ix_tracking_food_logs_logged_at", table_name="food_logs", schema="tracking")
    op.drop_table("food_logs", schema="tracking")

    op.drop_index("ux_static_meal_items_meal_id_sort_order", table_name="meal_items", schema="static")
    op.drop_index("ix_static_meal_items_food_id", table_name="meal_items", schema="static")
    op.drop_index("ix_static_meal_items_meal_id", table_name="meal_items", schema="static")
    op.drop_table("meal_items", schema="static")

    op.drop_index("ix_static_meals_name_lower", table_name="meals", schema="static")
    op.drop_index("ix_static_meals_is_curated", table_name="meals", schema="static")
    op.drop_index("ix_static_meals_meal_type", table_name="meals", schema="static")
    op.drop_table("meals", schema="static")

    op.drop_index("ix_static_foods_name_lower", table_name="foods", schema="static")
    op.drop_index("ux_static_foods_external_source_external_id", table_name="foods", schema="static")
    op.drop_table("foods", schema="static")

    op.drop_index("ux_core_account_deletion_requests_user_pending", table_name="account_deletion_requests", schema="core")
    op.drop_index("ix_core_account_deletion_requests_user_id", table_name="account_deletion_requests", schema="core")
    op.drop_table("account_deletion_requests", schema="core")

    op.drop_index("ix_core_authentication_sessions_user_id", table_name="authentication_sessions", schema="core")
    op.drop_index("ix_core_authentication_sessions_refresh_token_hash", table_name="authentication_sessions", schema="core")
    op.drop_table("authentication_sessions", schema="core")

    op.drop_index("ix_core_user_medications_user_id_is_active", table_name="user_medications", schema="core")
    op.drop_index("ix_core_user_medications_user_id", table_name="user_medications", schema="core")
    op.drop_table("user_medications", schema="core")

    op.drop_table("user_preferences", schema="core")

    op.drop_index("ix_core_users_email_lower", table_name="users", schema="core")
    op.drop_table("users", schema="core")

    feedback_status_enum.drop(op.get_bind(), checkfirst=True)
    flare_level_enum.drop(op.get_bind(), checkfirst=True)

    op.execute("DROP SCHEMA IF EXISTS intelligence")
    op.execute("DROP SCHEMA IF EXISTS tracking")
    op.execute("DROP SCHEMA IF EXISTS static")
    op.execute("DROP SCHEMA IF EXISTS core")
