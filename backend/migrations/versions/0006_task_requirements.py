"""Add persisted task requirements and worker tools."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0006_task_requirements"
down_revision = "0005_email_action_tokens"
branch_labels = None
depends_on = None


def _add_text_column_if_missing(table: str, name: str) -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns(table)}
    if name not in columns:
        op.add_column(
            table,
            sa.Column(name, sa.Text(), server_default=sa.text("'[]'"), nullable=False),
        )


def upgrade() -> None:
    _add_text_column_if_missing("users", "tools_json")
    _add_text_column_if_missing("tasks", "required_skills_json")
    _add_text_column_if_missing("tasks", "required_tools_json")


def downgrade() -> None:
    bind = op.get_bind()
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    task_columns = {column["name"] for column in inspect(bind).get_columns("tasks")}
    if "required_tools_json" in task_columns:
        op.drop_column("tasks", "required_tools_json")
    if "required_skills_json" in task_columns:
        op.drop_column("tasks", "required_skills_json")
    if "tools_json" in user_columns:
        op.drop_column("users", "tools_json")
