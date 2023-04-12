"""Remove locked column from score bet and binary bet.

Revision ID: c2ecfb568236
Revises: d75e76959af8
Create Date: 2023-03-12 06:30:53.548293

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "c2ecfb568236"
down_revision = "d75e76959af8"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("binary_bet", schema=None) as batch_op:
        batch_op.drop_column("locked")

    with op.batch_alter_table("score_bet", schema=None) as batch_op:
        batch_op.drop_column("locked")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("score_bet", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("locked", mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        )

    with op.batch_alter_table("binary_bet", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("locked", mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
        )

    # ### end Alembic commands ###
