"""Remove played column. Compute played property as won + drawn + lost.

Revision ID: d75e76959af8
Revises: 9f8e020eeced
Create Date: 2023-03-12 01:50:45.579007

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "d75e76959af8"
down_revision = "9f8e020eeced"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("group_position", schema=None) as batch_op:
        batch_op.drop_column("played")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("group_position", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("played", mysql.INTEGER(), autoincrement=False, nullable=False),
        )

    # ### end Alembic commands ###
