"""Add optional latitude/longitude coordinates to tasks."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_task_coordinates"
down_revision = "0001_schema_baseline"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tasks")}
    if "latitude" not in columns:
        op.add_column("tasks", sa.Column("latitude", sa.Float(), nullable=True))
    if "longitude" not in columns:
        op.add_column("tasks", sa.Column("longitude", sa.Float(), nullable=True))
    indexes = {index["name"] for index in inspect(bind).get_indexes("tasks")}
    if "ix_tasks_latitude" not in indexes:
        op.create_index("ix_tasks_latitude", "tasks", ["latitude"], unique=False)
    if "ix_tasks_longitude" not in indexes:
        op.create_index("ix_tasks_longitude", "tasks", ["longitude"], unique=False)

def downgrade() -> None:
    bind = op.get_bind()
    indexes = {index["name"] for index in inspect(bind).get_indexes("tasks")}
    if "ix_tasks_longitude" in indexes:
        op.drop_index("ix_tasks_longitude", table_name="tasks")
    if "ix_tasks_latitude" in indexes:
        op.drop_index("ix_tasks_latitude", table_name="tasks")
    columns = {column["name"] for column in inspect(bind).get_columns("tasks")}
    if "longitude" in columns:
        op.drop_column("tasks", "longitude")
    if "latitude" in columns:
        op.drop_column("tasks", "latitude")
