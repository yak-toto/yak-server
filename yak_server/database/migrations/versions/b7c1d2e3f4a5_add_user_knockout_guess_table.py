"""Add user_knockout_guess table and remove hardcoded knockout columns

Revision ID: b7c1d2e3f4a5
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "b7c1d2e3f4a5"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_knockout_guess",
        sa.Column("id", UUID(), nullable=False),
        sa.Column("user_id", UUID(), nullable=False),
        sa.Column("group_id", UUID(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count>=0", name="check_user_knockout_guess_count"),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "group_id", name="uq_user_knockout_guess"),
    )
    op.drop_column("user", "number_quarter_final_guess")
    op.drop_column("user", "number_semi_final_guess")
    op.drop_column("user", "number_final_guess")


def downgrade():
    op.add_column(
        "user",
        sa.Column(
            "number_final_guess",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "number_semi_final_guess",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "number_quarter_final_guess",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.drop_table("user_knockout_guess")
