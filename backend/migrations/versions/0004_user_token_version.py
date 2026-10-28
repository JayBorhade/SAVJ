"""Add token version for immediate logout and session revocation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004_user_token_version"
down_revision = "0003_unique_task_completion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "token_version" not in columns:
        op.add_column(
            "users",
            sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "token_version" in columns:
        op.drop_column("users", "token_version")
