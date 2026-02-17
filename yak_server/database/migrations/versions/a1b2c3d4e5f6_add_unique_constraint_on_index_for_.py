"""Add unique constraint on index for phase and group

Revision ID: a1b2c3d4e5f6
Revises: c2f508437a7e
Create Date: 2026-02-17 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "c2f508437a7e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_phase_index", "phase", ["index"])
    op.create_unique_constraint("uq_group_index", "group", ["index"])


def downgrade():
    op.drop_constraint("uq_group_index", "group", type_="unique")
    op.drop_constraint("uq_phase_index", "phase", type_="unique")
