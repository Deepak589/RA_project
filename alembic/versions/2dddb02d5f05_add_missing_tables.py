"""add_missing_tables

Revision ID: 2dddb02d5f05
Revises: 0007_add_user_role
Create Date: 2026-05-10 23:48:06.189037
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '2dddb02d5f05'
down_revision = '0007_add_user_role'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- New tables created ad-hoc outside Alembic; captured here for fresh deploys ---

    op.create_table(
        'meal_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column('meal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('static.meals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('static.foods.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('portion_g', sa.Numeric(8, 2), nullable=False),
        sa.Column('cooking_state', sa.String(20), nullable=False, server_default=text("'cooked'")),
        sa.Column('display_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.CheckConstraint("portion_g > 0", name="ck_static_meal_ingredients_portion_positive"),
        sa.CheckConstraint("cooking_state IN ('raw', 'cooked', 'ready_to_eat', 'unspecified')", name="ck_static_meal_ingredients_cooking_state"),
        schema='static',
        if_not_exists=True,
    )
    op.create_index('ix_static_meal_ingredients_meal_id', 'meal_ingredients', ['meal_id'], schema='static', if_not_exists=True)
    op.create_index('ix_static_meal_ingredients_food_id', 'meal_ingredients', ['food_id'], schema='static', if_not_exists=True)

    op.create_table(
        'custom_meals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('meal_type', sa.String(20), nullable=True),
        sa.Column('total_calories', sa.Numeric(8, 2), nullable=True),
        sa.Column('total_protein_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_carbs_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_fat_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_fiber_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_sugar_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('total_sodium_mg', sa.Numeric(8, 2), nullable=True),
        sa.Column('total_omega3_g', sa.Numeric(6, 3), nullable=True),
        sa.Column('anti_inflammatory_score', sa.Numeric(4, 1), nullable=True),
        sa.Column('is_vegetarian', sa.Boolean(), nullable=False, server_default=text("FALSE")),
        sa.Column('is_flare_friendly', sa.Boolean(), nullable=False, server_default=text("FALSE")),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=text("'[]'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.CheckConstraint(
            "meal_type IS NULL OR meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'flare_day')",
            name="ck_tracking_custom_meals_meal_type",
        ),
        sa.CheckConstraint(
            "anti_inflammatory_score IS NULL OR (anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10)",
            name="ck_tracking_custom_meals_score",
        ),
        schema='tracking',
        if_not_exists=True,
    )
    op.create_index('ix_tracking_custom_meals_user_id', 'custom_meals', ['user_id'], schema='tracking', if_not_exists=True)

    op.create_table(
        'custom_meal_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column('custom_meal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracking.custom_meals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('static.foods.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('portion_g', sa.Numeric(8, 2), nullable=True),
        sa.Column('cooking_state', sa.String(20), nullable=True),
        sa.Column('display_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.CheckConstraint("portion_g IS NULL OR portion_g > 0", name="ck_tracking_custom_meal_ingredients_portion_positive"),
        schema='tracking',
        if_not_exists=True,
    )
    op.create_index('ix_tracking_custom_meal_ingredients_custom_meal_id', 'custom_meal_ingredients', ['custom_meal_id'], schema='tracking', if_not_exists=True)
    op.create_index('ix_tracking_custom_meal_ingredients_food_id', 'custom_meal_ingredients', ['food_id'], schema='tracking', if_not_exists=True)

    op.create_table(
        'missing_ingredients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ingredient_name', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=text("'missing_completely'")),
        sa.Column('submitted_calories', sa.Numeric(8, 2), nullable=True),
        sa.Column('submitted_protein_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('submitted_carbs_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('submitted_fat_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('submitted_fiber_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('submitted_sugar_g', sa.Numeric(6, 2), nullable=True),
        sa.Column('submitted_sodium_mg', sa.Numeric(8, 2), nullable=True),
        sa.Column('submitted_source', sa.Text(), nullable=True),
        sa.Column('reported_count', sa.Integer(), nullable=False, server_default=text("1")),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('reviewed_by', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('food_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('static.foods.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")),
        sa.CheckConstraint(
            "status IN ('missing_completely', 'user_entered', 'under_review', 'added', 'rejected')",
            name="ck_tracking_missing_ingredients_status",
        ),
        sa.CheckConstraint("char_length(trim(ingredient_name)) > 0", name="ck_tracking_missing_ingredients_name_not_blank"),
        sa.CheckConstraint("reported_count > 0", name="ck_tracking_missing_ingredients_reported_count_positive"),
        schema='tracking',
        if_not_exists=True,
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_tracking_missing_ingredients_name_lower ON tracking.missing_ingredients (LOWER(ingredient_name))")
    op.create_index('ix_tracking_missing_ingredients_status', 'missing_ingredients', ['status'], schema='tracking', if_not_exists=True)
    op.create_index('ix_tracking_missing_ingredients_reported_count', 'missing_ingredients', ['reported_count'], schema='tracking', if_not_exists=True)

    # --- Real schema drift: foods columns changed from VARCHAR to Text in models ---
    op.alter_column('foods', 'cooking_state',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.Text(),
               existing_nullable=False,
               existing_server_default=sa.text("'unspecified'::character varying"),
               schema='static')
    op.alter_column('foods', 'quality_flag',
               existing_type=sa.VARCHAR(length=30),
               type_=sa.Text(),
               existing_nullable=False,
               existing_server_default=sa.text("'usda_verified'::character varying"),
               schema='static')

    # --- Constraint renames ---
    op.drop_constraint('user_preferences_user_id_key', 'user_preferences', schema='core', type_='unique')
    op.drop_index('ix_core_user_preferences_user_id', table_name='user_preferences', schema='core')
    op.create_index('ix_core_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True, schema='core')

    op.drop_constraint('lifestyle_logs_user_id_log_date_key', 'lifestyle_logs', schema='tracking', type_='unique')
    op.create_unique_constraint('uq_tracking_lifestyle_logs_user_log_date', 'lifestyle_logs', ['user_id', 'log_date'], schema='tracking')


def downgrade() -> None:
    # Constraint renames — reverse
    op.drop_constraint('uq_tracking_lifestyle_logs_user_log_date', 'lifestyle_logs', schema='tracking', type_='unique')
    op.create_unique_constraint('lifestyle_logs_user_id_log_date_key', 'lifestyle_logs', ['user_id', 'log_date'], schema='tracking')

    op.drop_index('ix_core_user_preferences_user_id', table_name='user_preferences', schema='core')
    op.create_index('ix_core_user_preferences_user_id', 'user_preferences', ['user_id'], unique=False, schema='core')
    op.create_unique_constraint('user_preferences_user_id_key', 'user_preferences', ['user_id'], schema='core')

    # foods type revert
    op.alter_column('foods', 'quality_flag',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=30),
               existing_nullable=False,
               existing_server_default=sa.text("'usda_verified'::character varying"),
               schema='static')
    op.alter_column('foods', 'cooking_state',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False,
               existing_server_default=sa.text("'unspecified'::character varying"),
               schema='static')

    # Drop new tables
    op.drop_table('missing_ingredients', schema='tracking')
    op.drop_table('custom_meal_ingredients', schema='tracking')
    op.drop_table('custom_meals', schema='tracking')
    op.drop_table('meal_ingredients', schema='static')
