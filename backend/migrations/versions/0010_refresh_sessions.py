"""Add opaque rotating refresh sessions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0010_refresh_sessions"
down_revision = "0009_private_task_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "refresh_sessions" not in tables:
        op.create_table(
            "refresh_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("family_id", sa.String(length=64), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("token_hash", name="uq_refresh_sessions_token_hash"),
        )
    indexes = {index["name"] for index in inspect(bind).get_indexes("refresh_sessions")}
    for name, columns, unique in [
        ("ix_refresh_sessions_id", ["id"], False),
        ("ix_refresh_sessions_user_id", ["user_id"], False),
        ("ix_refresh_sessions_family_id", ["family_id"], False),
        ("ix_refresh_sessions_token_hash", ["token_hash"], True),
        ("ix_refresh_sessions_expires_at", ["expires_at"], False),
    ]:
        if name not in indexes:
            op.create_index(name, "refresh_sessions", columns, unique=unique)


def downgrade() -> None:
    if "refresh_sessions" in inspect(op.get_bind()).get_table_names():
        op.drop_table("refresh_sessions")
