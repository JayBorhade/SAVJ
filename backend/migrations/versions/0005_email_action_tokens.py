"""Add email verification state and single-use email action tokens."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0005_email_action_tokens"
down_revision = "0004_user_token_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_email_verified" not in user_columns:
        # Existing accounts are grandfathered as verified; new production
        # registrations explicitly set this flag to false until confirmed.
        op.add_column(
            "users",
            sa.Column("is_email_verified", sa.Boolean(), server_default=sa.true(), nullable=False),
        )

    tables = set(inspect(bind).get_table_names())
    if "email_action_tokens" not in tables:
        op.create_table(
            "email_action_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("purpose", sa.String(length=32), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in inspect(bind).get_indexes("email_action_tokens")}
    definitions = [
        ("ix_email_action_tokens_id", ["id"], False),
        ("ix_email_action_tokens_user_id", ["user_id"], False),
        ("ix_email_action_tokens_token_hash", ["token_hash"], True),
        ("ix_email_action_tokens_purpose", ["purpose"], False),
        ("ix_email_action_tokens_user_purpose", ["user_id", "purpose"], False),
    ]
    for name, columns, unique in definitions:
        if name not in indexes:
            op.create_index(name, "email_action_tokens", columns, unique=unique)


def downgrade() -> None:
    bind = op.get_bind()
    if "email_action_tokens" in inspect(bind).get_table_names():
        op.drop_table("email_action_tokens")
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "is_email_verified" in user_columns:
        op.drop_column("users", "is_email_verified")
