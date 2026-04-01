"""rename_internal_flag_url_to_internal_flag_path_in_team

Revision ID: 12740baeb469
Revises: 488d33a92340
Create Date: 2026-04-01 12:41:14.610528

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "12740baeb469"
down_revision = "488d33a92340"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("team", "internal_flag_url", new_column_name="internal_flag_path")


def downgrade():
    op.alter_column("team", "internal_flag_path", new_column_name="internal_flag_url")
