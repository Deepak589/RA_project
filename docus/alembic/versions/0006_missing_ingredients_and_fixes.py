"""missing ingredients and week 6 fixes

Revision ID: 0006_missing_ingredients
Revises: 0005_food_log_enhancements
Create Date: 2026-04-25 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_missing_ingredients"
down_revision = "0005_food_log_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "missing_ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingredient_name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="missing_completely"),
        sa.Column("submitted_calories", sa.Numeric(8, 2), nullable=True),
        sa.Column("submitted_protein_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("submitted_carbs_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("submitted_fat_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("submitted_fiber_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("submitted_sugar_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("submitted_sodium_mg", sa.Numeric(8, 2), nullable=True),
        sa.Column("submitted_source", sa.Text(), nullable=True),
        sa.Column("reported_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('missing_completely', 'user_entered', 'under_review', 'added', 'rejected')",
            name="ck_tracking_missing_ingredients_status",
        ),
        sa.CheckConstraint("char_length(trim(ingredient_name)) > 0", name="ck_tracking_missing_ingredients_name_not_blank"),
        sa.CheckConstraint("reported_count > 0", name="ck_tracking_missing_ingredients_reported_count_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["food_id"], ["static.foods.id"], ondelete="SET NULL"),
        schema="tracking",
    )
    op.create_index(
        "ux_tracking_missing_ingredients_name_lower",
        "missing_ingredients",
        [sa.text("LOWER(ingredient_name)")],
        unique=True,
        schema="tracking",
    )
    op.create_index("ix_tracking_missing_ingredients_status", "missing_ingredients", ["status"], schema="tracking")
    op.create_index(
        "ix_tracking_missing_ingredients_reported_count",
        "missing_ingredients",
        ["reported_count"],
        schema="tracking",
    )

    op.add_column(
        "foods",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        schema="static",
    )

    op.add_column(
        "recommendation_logs",
        sa.Column("recommendation_mode", sa.String(20), nullable=True),
        schema="intelligence",
    )
    op.create_check_constraint(
        "ck_intelligence_recommendation_logs_mode",
        "recommendation_logs",
        "recommendation_mode IS NULL OR recommendation_mode IN ('normal', 'mixed', 'flare_only')",
        schema="intelligence",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_intelligence_recommendation_logs_mode",
        "recommendation_logs",
        schema="intelligence",
        type_="check",
    )
    op.drop_column("recommendation_logs", "recommendation_mode", schema="intelligence")
    op.drop_column("foods", "needs_review", schema="static")
    op.drop_index("ix_tracking_missing_ingredients_reported_count", table_name="missing_ingredients", schema="tracking")
    op.drop_index("ix_tracking_missing_ingredients_status", table_name="missing_ingredients", schema="tracking")
    op.drop_index("ux_tracking_missing_ingredients_name_lower", table_name="missing_ingredients", schema="tracking")
    op.drop_table("missing_ingredients", schema="tracking")
