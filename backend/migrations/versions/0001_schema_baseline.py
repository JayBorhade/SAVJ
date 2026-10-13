"""Bootstrap the SAVJ schema from the SQLAlchemy metadata.

This first migration is intentionally idempotent so existing development databases
created by the earlier create_all startup can be stamped with this revision without
dropping data. Subsequent schema changes should use explicit Alembic operations.
"""
from alembic import op
from app.database import Base
from app import models  # noqa: F401 - register model metadata

revision = "0001_schema_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
