"""Add group rank need_recomputation column.

Revision ID: e0f551c7766c
Revises: b36763d4cb42
Create Date: 2023-03-18 22:04:41.764896

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e0f551c7766c"
down_revision = "b36763d4cb42"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("group_position", schema=None) as batch_op:
        batch_op.add_column(sa.Column("need_recomputation", sa.Boolean(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("group_position", schema=None) as batch_op:
        batch_op.drop_column("need_recomputation")

    # ### end Alembic commands ###
