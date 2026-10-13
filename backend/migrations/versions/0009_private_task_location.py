"""Add a separate private address field to tasks."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0009_private_task_location"
down_revision = "0008_user_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("tasks")}
    if "private_location_text" not in columns:
        op.add_column("tasks", sa.Column("private_location_text", sa.String(length=300), nullable=True))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("tasks")}
    if "private_location_text" in columns:
        op.drop_column("tasks", "private_location_text")
