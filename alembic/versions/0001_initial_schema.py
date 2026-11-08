"""Create the initial AutoFlow schema.

Revision ID: 0001_initial
Revises:
"""
import sqlalchemy as sa
from alembic import op
from app.db.base import Base
from app import models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create missing tables without dropping or replacing existing local data.
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    inspector = sa.inspect(bind)
    for table in Base.metadata.sorted_tables:
        if table.name not in inspector.get_table_names():
            continue
        existing = {item["name"] for item in inspector.get_indexes(table.name)}
        for index in table.indexes:
            if index.name not in existing:
                op.create_index(
                    index.name,
                    table.name,
                    [column.name for column in index.columns],
                    unique=index.unique,
                )

def downgrade() -> None:
    # Intentionally non-destructive: this baseline may be stamped onto an existing
    # database. Dropping all tables here could erase customer data.
    pass
