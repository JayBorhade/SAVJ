"""Add task ratings and worker rating summaries."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0007_task_ratings"
down_revision = "0006_task_requirements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "task_ratings" not in tables:
        op.create_table(
            "task_ratings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("worker_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False),
            sa.Column("comment", sa.String(length=1000), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("task_id", name="uq_task_rating_task"),
        )
    indexes = {index["name"] for index in inspect(bind).get_indexes("task_ratings")}
    for name, columns in [
        ("ix_task_ratings_id", ["id"]),
        ("ix_task_ratings_task_id", ["task_id"]),
        ("ix_task_ratings_requester_id", ["requester_id"]),
        ("ix_task_ratings_worker_id", ["worker_id"]),
    ]:
        if name not in indexes:
            op.create_index(name, "task_ratings", columns, unique=False)


def downgrade() -> None:
    if "task_ratings" in inspect(op.get_bind()).get_table_names():
        op.drop_table("task_ratings")
