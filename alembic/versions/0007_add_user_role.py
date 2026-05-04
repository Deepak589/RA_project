"""add user role

Revision ID: 0007_add_user_role
Revises: 0006_missing_ingredients
Create Date: 2026-04-26 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_add_user_role"
down_revision = "0006_missing_ingredients"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        schema="core",
    )
    op.create_check_constraint(
        "ck_core_users_role",
        "users",
        "role IN ('user', 'admin')",
        schema="core",
    )


def downgrade() -> None:
    op.drop_constraint("ck_core_users_role", "users", schema="core", type_="check")
    op.drop_column("users", "role", schema="core")
