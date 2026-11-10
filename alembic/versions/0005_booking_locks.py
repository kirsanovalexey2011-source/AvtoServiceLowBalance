"""Add per-organization locks for concurrent appointment writes.

Revision ID: 0005_booking_locks
Revises: 0004_account_security
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_booking_locks"
down_revision = "0004_account_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "booking_locks" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "booking_locks",
            sa.Column(
                "organization_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id"),
                primary_key=True,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade() -> None:
    # Forward-only: booking coordination state is intentionally retained.
    pass
