"""add food nutrition scoring fields

Revision ID: 0002_food_score
Revises: 0001_initial_schema
Create Date: 2026-04-20 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_food_score"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "foods",
        sa.Column("saturated_fat_g", sa.Numeric(8, 2), nullable=False, server_default=sa.text("0")),
        schema="static",
    )
    op.add_column(
        "foods",
        sa.Column("calcium_mg", sa.Numeric(10, 2), nullable=False, server_default=sa.text("0")),
        schema="static",
    )
    op.add_column(
        "foods",
        sa.Column("vitamin_d_ug", sa.Numeric(8, 2), nullable=False, server_default=sa.text("0")),
        schema="static",
    )
    op.add_column(
        "foods",
        sa.Column("anti_inflammatory_score", sa.Numeric(4, 1), nullable=False, server_default=sa.text("0")),
        schema="static",
    )
    op.create_check_constraint(
        "ck_foods_saturated_fat_non_negative",
        "foods",
        "saturated_fat_g >= 0",
        schema="static",
    )
    op.create_check_constraint(
        "ck_foods_calcium_non_negative",
        "foods",
        "calcium_mg >= 0",
        schema="static",
    )
    op.create_check_constraint(
        "ck_foods_vitamin_d_non_negative",
        "foods",
        "vitamin_d_ug >= 0",
        schema="static",
    )
    op.create_check_constraint(
        "ck_foods_ai_score_between_0_10",
        "foods",
        "anti_inflammatory_score >= 0 AND anti_inflammatory_score <= 10",
        schema="static",
    )


def downgrade() -> None:
    op.drop_constraint("ck_foods_ai_score_between_0_10", "foods", schema="static", type_="check")
    op.drop_constraint("ck_foods_vitamin_d_non_negative", "foods", schema="static", type_="check")
    op.drop_constraint("ck_foods_calcium_non_negative", "foods", schema="static", type_="check")
    op.drop_constraint("ck_foods_saturated_fat_non_negative", "foods", schema="static", type_="check")
    op.drop_column("foods", "anti_inflammatory_score", schema="static")
    op.drop_column("foods", "vitamin_d_ug", schema="static")
    op.drop_column("foods", "calcium_mg", schema="static")
    op.drop_column("foods", "saturated_fat_g", schema="static")
