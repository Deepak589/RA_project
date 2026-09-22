"""set food external source default to usda

Revision ID: 0003_food_source
Revises: 0002_food_score
Create Date: 2026-04-20 10:00:00
"""

from __future__ import annotations

from alembic import op


revision = "0003_food_source"
down_revision = "0002_food_score"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE static.foods ALTER COLUMN external_source SET DEFAULT 'usda'")


def downgrade() -> None:
    op.execute("ALTER TABLE static.foods ALTER COLUMN external_source SET DEFAULT 'usda_fdc'")
