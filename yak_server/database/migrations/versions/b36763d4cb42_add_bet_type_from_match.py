"""Add bet type from match.

Revision ID: b36763d4cb42
Revises: c2ecfb568236
Create Date: 2023-03-16 21:34:07.705206

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b36763d4cb42"
down_revision = "c2ecfb568236"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "bet_type_from_match",
                sa.Enum("SCORE_BET", "BINARY_BET", name="betmapping"),
                nullable=True,
            ),
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("match", schema=None) as batch_op:
        batch_op.drop_column("bet_type_from_match")

    # ### end Alembic commands ###
