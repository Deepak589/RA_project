"""food log enhancements and week 5 tracking fields

Revision ID: 0005_food_log_enhancements
Revises: 0004_meal_library
Create Date: 2026-04-22 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005_food_log_enhancements"
down_revision = "0004_meal_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("food_logs", sa.Column("log_source", sa.String(30), nullable=False, server_default="manual_log"), schema="tracking")
    op.add_column("food_logs", sa.Column("raw_portion_g", sa.Numeric(8, 2), nullable=True), schema="tracking")
    op.add_column("food_logs", sa.Column("cooking_state_at_log", sa.String(20), nullable=True), schema="tracking")
    op.add_column("food_logs", sa.Column("conversion_factor_at_log", sa.Numeric(5, 3), nullable=True), schema="tracking")
    op.add_column("food_logs", sa.Column("display_calories", sa.Numeric(8, 2), nullable=True), schema="tracking")
    op.add_column("food_logs", sa.Column("display_protein_g", sa.Numeric(6, 2), nullable=True), schema="tracking")
    op.add_column(
        "food_logs",
        sa.Column("recommendation_meal_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="tracking",
    )
    op.add_column("food_logs", sa.Column("custom_meal_id", postgresql.UUID(as_uuid=True), nullable=True), schema="tracking")
    op.create_foreign_key(
        "fk_tracking_food_logs_recommendation_meal_id",
        "food_logs",
        "meals",
        ["recommendation_meal_id"],
        ["id"],
        source_schema="tracking",
        referent_schema="static",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tracking_food_logs_custom_meal_id",
        "food_logs",
        "custom_meals",
        ["custom_meal_id"],
        ["id"],
        source_schema="tracking",
        referent_schema="tracking",
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_tracking_food_logs_log_source",
        "food_logs",
        "log_source IN ('curated_recommendation', 'custom_meal', 'manual_log')",
        schema="tracking",
    )
    op.create_check_constraint(
        "ck_tracking_food_logs_cooking_state_at_log",
        "food_logs",
        "cooking_state_at_log IS NULL OR cooking_state_at_log IN ('raw', 'cooked', 'ready_to_eat')",
        schema="tracking",
    )

    op.add_column("recommendation_logs", sa.Column("rule_priority_applied", sa.String(30), nullable=True), schema="intelligence")
    op.add_column(
        "recommendation_logs",
        sa.Column("flare_mode_active", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        schema="intelligence",
    )
    op.add_column(
        "recommendation_logs",
        sa.Column("daily_nutrition_context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="intelligence",
    )
    op.create_check_constraint(
        "ck_intelligence_recommendation_logs_rule_priority",
        "recommendation_logs",
        "rule_priority_applied IS NULL OR rule_priority_applied IN "
        "('safety', 'medication', 'flare', 'nutrition', 'preference', 'score', 'variety')",
        schema="intelligence",
    )

    op.add_column("symptom_logs", sa.Column("stiffness_minutes", sa.Integer(), nullable=True), schema="tracking")
    op.add_column("symptom_logs", sa.Column("mobility_score", sa.SmallInteger(), nullable=True), schema="tracking")
    op.add_column("symptom_logs", sa.Column("energy_level", sa.SmallInteger(), nullable=True), schema="tracking")
    op.add_column("symptom_logs", sa.Column("sleep_quality", sa.SmallInteger(), nullable=True), schema="tracking")
    op.add_column("symptom_logs", sa.Column("mood_score", sa.SmallInteger(), nullable=True), schema="tracking")
    op.create_check_constraint(
        "ck_tracking_symptom_logs_mobility_score",
        "symptom_logs",
        "mobility_score IS NULL OR mobility_score BETWEEN 0 AND 10",
        schema="tracking",
    )
    op.create_check_constraint(
        "ck_tracking_symptom_logs_energy_level",
        "symptom_logs",
        "energy_level IS NULL OR energy_level BETWEEN 0 AND 10",
        schema="tracking",
    )
    op.create_check_constraint(
        "ck_tracking_symptom_logs_sleep_quality",
        "symptom_logs",
        "sleep_quality IS NULL OR sleep_quality BETWEEN 0 AND 10",
        schema="tracking",
    )
    op.create_check_constraint(
        "ck_tracking_symptom_logs_mood_score",
        "symptom_logs",
        "mood_score IS NULL OR mood_score BETWEEN 0 AND 10",
        schema="tracking",
    )

    op.add_column("lifestyle_logs", sa.Column("exercise_type", sa.String(80), nullable=True), schema="tracking")
    op.add_column("lifestyle_logs", sa.Column("exercise_duration_minutes", sa.Integer(), nullable=True), schema="tracking")
    op.add_column("lifestyle_logs", sa.Column("smoking", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")), schema="tracking")
    op.add_column("lifestyle_logs", sa.Column("alcohol", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")), schema="tracking")


def downgrade() -> None:
    op.drop_column("lifestyle_logs", "alcohol", schema="tracking")
    op.drop_column("lifestyle_logs", "smoking", schema="tracking")
    op.drop_column("lifestyle_logs", "exercise_duration_minutes", schema="tracking")
    op.drop_column("lifestyle_logs", "exercise_type", schema="tracking")

    op.drop_constraint("ck_tracking_symptom_logs_mood_score", "symptom_logs", schema="tracking", type_="check")
    op.drop_constraint("ck_tracking_symptom_logs_sleep_quality", "symptom_logs", schema="tracking", type_="check")
    op.drop_constraint("ck_tracking_symptom_logs_energy_level", "symptom_logs", schema="tracking", type_="check")
    op.drop_constraint("ck_tracking_symptom_logs_mobility_score", "symptom_logs", schema="tracking", type_="check")
    op.drop_column("symptom_logs", "mood_score", schema="tracking")
    op.drop_column("symptom_logs", "sleep_quality", schema="tracking")
    op.drop_column("symptom_logs", "energy_level", schema="tracking")
    op.drop_column("symptom_logs", "mobility_score", schema="tracking")
    op.drop_column("symptom_logs", "stiffness_minutes", schema="tracking")

    op.drop_constraint("ck_intelligence_recommendation_logs_rule_priority", "recommendation_logs", schema="intelligence", type_="check")
    op.drop_column("recommendation_logs", "daily_nutrition_context_json", schema="intelligence")
    op.drop_column("recommendation_logs", "flare_mode_active", schema="intelligence")
    op.drop_column("recommendation_logs", "rule_priority_applied", schema="intelligence")

    op.drop_constraint("ck_tracking_food_logs_cooking_state_at_log", "food_logs", schema="tracking", type_="check")
    op.drop_constraint("ck_tracking_food_logs_log_source", "food_logs", schema="tracking", type_="check")
    op.drop_constraint("fk_tracking_food_logs_custom_meal_id", "food_logs", schema="tracking", type_="foreignkey")
    op.drop_constraint("fk_tracking_food_logs_recommendation_meal_id", "food_logs", schema="tracking", type_="foreignkey")
    op.drop_column("food_logs", "custom_meal_id", schema="tracking")
    op.drop_column("food_logs", "recommendation_meal_id", schema="tracking")
    op.drop_column("food_logs", "display_protein_g", schema="tracking")
    op.drop_column("food_logs", "display_calories", schema="tracking")
    op.drop_column("food_logs", "conversion_factor_at_log", schema="tracking")
    op.drop_column("food_logs", "cooking_state_at_log", schema="tracking")
    op.drop_column("food_logs", "raw_portion_g", schema="tracking")
    op.drop_column("food_logs", "log_source", schema="tracking")
