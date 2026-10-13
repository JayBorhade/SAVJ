"""Add per-user in-app notifications."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0008_user_notifications"
down_revision = "0007_task_ratings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "user_notifications" not in tables:
        op.create_table(
            "user_notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("notification_type", sa.String(length=60), nullable=False),
            sa.Column("title", sa.String(length=140), nullable=False),
            sa.Column("body", sa.String(length=500), nullable=False, server_default=""),
            sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True),
            sa.Column("drive_id", sa.Integer(), sa.ForeignKey("community_drives.id", ondelete="SET NULL"), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = {index["name"] for index in inspect(bind).get_indexes("user_notifications")}
    for name, columns in [
        ("ix_user_notifications_id", ["id"]),
        ("ix_user_notifications_user_id", ["user_id"]),
        ("ix_user_notifications_task_id", ["task_id"]),
        ("ix_user_notifications_drive_id", ["drive_id"]),
    ]:
        if name not in indexes:
            op.create_index(name, "user_notifications", columns, unique=False)


def downgrade() -> None:
    if "user_notifications" in inspect(op.get_bind()).get_table_names():
        op.drop_table("user_notifications")
