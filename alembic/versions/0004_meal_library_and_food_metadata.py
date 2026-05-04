"""meal library and food metadata

Revision ID: 0004_meal_library
Revises: 0003_food_source
Create Date: 2026-04-21 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_meal_library"
down_revision = "0003_food_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("foods", sa.Column("cooking_state", sa.String(20), nullable=False, server_default="unspecified"), schema="static")
    op.add_column("foods", sa.Column("conversion_factor", sa.Numeric(5, 3), nullable=False, server_default="1.0"), schema="static")
    op.add_column("foods", sa.Column("display_note", sa.Text(), nullable=True), schema="static")
    op.add_column("foods", sa.Column("quality_flag", sa.String(30), nullable=False, server_default="usda_verified"), schema="static")
    op.add_column("foods", sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")), schema="static")
    op.create_check_constraint(
        "ck_foods_cooking_state",
        "foods",
        "cooking_state IN ('raw', 'cooked', 'ready_to_eat', 'unspecified')",
        schema="static",
    )
    op.create_check_constraint(
        "ck_foods_quality_flag",
        "foods",
        "quality_flag IN ('usda_verified', 'manually_verified', 'incomplete', 'under_review')",
        schema="static",
    )
    op.create_check_constraint("ck_foods_conversion_factor_positive", "foods", "conversion_factor > 0", schema="static")

    _extend_static_meals()

    op.create_table(
        "meal_ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.meals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("portion_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("cooking_state", sa.String(20), nullable=False, server_default="cooked"),
        sa.Column("display_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("portion_g > 0", name="ck_static_meal_ingredients_portion_positive"),
        sa.CheckConstraint("cooking_state IN ('raw', 'cooked', 'ready_to_eat', 'unspecified')", name="ck_static_meal_ingredients_cooking_state"),
        schema="static",
    )
    op.create_index("ix_static_meal_ingredients_meal_id", "meal_ingredients", ["meal_id"], schema="static")
    op.create_index("ix_static_meal_ingredients_food_id", "meal_ingredients", ["food_id"], schema="static")

    op.create_table(
        "custom_meals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("meal_type", sa.String(20), nullable=True),
        sa.Column("total_calories", sa.Numeric(8, 2), nullable=True),
        sa.Column("total_protein_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_carbs_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_fat_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_fiber_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_sugar_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_sodium_mg", sa.Numeric(8, 2), nullable=True),
        sa.Column("total_omega3_g", sa.Numeric(6, 3), nullable=True),
        sa.Column("anti_inflammatory_score", sa.Numeric(4, 1), nullable=True),
        sa.Column("is_vegetarian", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_flare_friendly", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("meal_type IS NULL OR meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'flare_day')", name="ck_tracking_custom_meals_meal_type"),
        sa.CheckConstraint("anti_inflammatory_score IS NULL OR (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)", name="ck_tracking_custom_meals_score"),
        schema="tracking",
    )
    op.create_index("ix_tracking_custom_meals_user_id", "custom_meals", ["user_id"], schema="tracking")

    op.create_table(
        "custom_meal_ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("custom_meal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tracking.custom_meals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("static.foods.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("portion_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("cooking_state", sa.String(20), nullable=True),
        sa.Column("display_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("portion_g IS NULL OR portion_g > 0", name="ck_tracking_custom_meal_ingredients_portion_positive"),
        schema="tracking",
    )
    op.create_index("ix_tracking_custom_meal_ingredients_custom_meal_id", "custom_meal_ingredients", ["custom_meal_id"], schema="tracking")
    op.create_index("ix_tracking_custom_meal_ingredients_food_id", "custom_meal_ingredients", ["food_id"], schema="tracking")


def downgrade() -> None:
    op.drop_index("ix_tracking_custom_meal_ingredients_food_id", table_name="custom_meal_ingredients", schema="tracking")
    op.drop_index("ix_tracking_custom_meal_ingredients_custom_meal_id", table_name="custom_meal_ingredients", schema="tracking")
    op.drop_table("custom_meal_ingredients", schema="tracking")
    op.drop_index("ix_tracking_custom_meals_user_id", table_name="custom_meals", schema="tracking")
    op.drop_table("custom_meals", schema="tracking")
    op.drop_index("ix_static_meal_ingredients_food_id", table_name="meal_ingredients", schema="static")
    op.drop_index("ix_static_meal_ingredients_meal_id", table_name="meal_ingredients", schema="static")
    op.drop_table("meal_ingredients", schema="static")
    _remove_static_meal_columns()
    op.drop_constraint("ck_foods_conversion_factor_positive", "foods", schema="static", type_="check")
    op.drop_constraint("ck_foods_quality_flag", "foods", schema="static", type_="check")
    op.drop_constraint("ck_foods_cooking_state", "foods", schema="static", type_="check")
    op.drop_column("foods", "manual_override", schema="static")
    op.drop_column("foods", "quality_flag", schema="static")
    op.drop_column("foods", "display_note", schema="static")
    op.drop_column("foods", "conversion_factor", schema="static")
    op.drop_column("foods", "cooking_state", schema="static")


def _extend_static_meals() -> None:
    for column_sql in (
        "ADD COLUMN IF NOT EXISTS cuisine_type VARCHAR(50)",
        "ADD COLUMN IF NOT EXISTS effort_level VARCHAR(10) NOT NULL DEFAULT 'medium'",
        "ADD COLUMN IF NOT EXISTS serving_size_description TEXT",
        "ADD COLUMN IF NOT EXISTS total_calories NUMERIC(8,2)",
        "ADD COLUMN IF NOT EXISTS total_protein_g NUMERIC(6,2)",
        "ADD COLUMN IF NOT EXISTS total_carbs_g NUMERIC(6,2)",
        "ADD COLUMN IF NOT EXISTS total_fat_g NUMERIC(6,2)",
        "ADD COLUMN IF NOT EXISTS total_fiber_g NUMERIC(6,2)",
        "ADD COLUMN IF NOT EXISTS total_sugar_g NUMERIC(6,2)",
        "ADD COLUMN IF NOT EXISTS total_sodium_mg NUMERIC(8,2)",
        "ADD COLUMN IF NOT EXISTS total_omega3_g NUMERIC(6,3)",
        "ADD COLUMN IF NOT EXISTS is_vegetarian BOOLEAN NOT NULL DEFAULT FALSE",
        "ADD COLUMN IF NOT EXISTS is_flare_friendly BOOLEAN NOT NULL DEFAULT FALSE",
        "ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb",
        "ADD COLUMN IF NOT EXISTS instructions TEXT",
    ):
        op.execute(f"ALTER TABLE static.meals {column_sql}")

    op.execute("ALTER TABLE static.meals ALTER COLUMN prep_time_minutes DROP NOT NULL")
    op.execute("ALTER TABLE static.meals ALTER COLUMN meal_type TYPE VARCHAR(20)")
    op.execute("ALTER TABLE static.meals ALTER COLUMN anti_inflammatory_score TYPE NUMERIC(4,1)")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS meals_meal_type_check")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS valid_meal_type")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS meals_anti_inflammatory_score_check")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS score_between_0_100")
    op.execute(
        "ALTER TABLE static.meals ADD CONSTRAINT ck_static_meals_meal_type_v2 "
        "CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'flare_day'))"
    )
    op.execute(
        "ALTER TABLE static.meals ADD CONSTRAINT ck_static_meals_effort_level "
        "CHECK (effort_level IN ('low', 'medium', 'high'))"
    )
    op.execute(
        "ALTER TABLE static.meals ADD CONSTRAINT ck_static_meals_ai_score_v2 "
        "CHECK (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)"
    )


def _remove_static_meal_columns() -> None:
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS ck_static_meals_ai_score_v2")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS ck_static_meals_effort_level")
    op.execute("ALTER TABLE static.meals DROP CONSTRAINT IF EXISTS ck_static_meals_meal_type_v2")
    for column_name in (
        "instructions",
        "tags",
        "is_flare_friendly",
        "is_vegetarian",
        "total_omega3_g",
        "total_sodium_mg",
        "total_sugar_g",
        "total_fiber_g",
        "total_fat_g",
        "total_carbs_g",
        "total_protein_g",
        "total_calories",
        "serving_size_description",
        "effort_level",
        "cuisine_type",
    ):
        op.execute(f"ALTER TABLE static.meals DROP COLUMN IF EXISTS {column_name}")
