"""Ensure a task can contribute at most one verified completion event."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_unique_task_completion"
down_revision = "0002_task_coordinates"
branch_labels = None
depends_on = None

INDEX_NAME = "uq_impact_task_completed_once"
PREDICATE = sa.text("event_type = 'task_completed' AND task_id IS NOT NULL")


def upgrade() -> None:
    bind = op.get_bind()
    # Repair duplicates from older versions before enforcing the invariant.
    # Preserve the earliest row for each task and event type.
    bind.execute(sa.text("""
        DELETE FROM impact_events
        WHERE event_type = 'task_completed'
          AND task_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM impact_events
              WHERE event_type = 'task_completed'
                AND task_id IS NOT NULL
              GROUP BY task_id
          )
    """))
    indexes = {index["name"] for index in inspect(bind).get_indexes("impact_events")}
    if INDEX_NAME not in indexes:
        op.create_index(
            INDEX_NAME,
            "impact_events",
            ["task_id"],
            unique=True,
            sqlite_where=PREDICATE,
            postgresql_where=PREDICATE,
        )


def downgrade() -> None:
    bind = op.get_bind()
    indexes = {index["name"] for index in inspect(bind).get_indexes("impact_events")}
    if INDEX_NAME in indexes:
        op.drop_index(INDEX_NAME, table_name="impact_events")
