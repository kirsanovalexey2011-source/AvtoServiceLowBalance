"""Add configurable weekly business working hours.

Revision ID: 0006_business_working_hours
Revises: 0005_booking_locks
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_business_working_hours"
down_revision = "0005_booking_locks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "business_working_hours" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "business_working_hours",
            sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), primary_key=True),
            sa.Column("weekday", sa.Integer(), primary_key=True),
            sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("opens_at", sa.Time(), nullable=True),
            sa.Column("closes_at", sa.Time(), nullable=True),
            sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_business_working_hours_weekday"),
            sa.CheckConstraint(
                "(is_closed = true) OR (opens_at IS NOT NULL AND closes_at IS NOT NULL AND opens_at < closes_at)",
                name="ck_business_working_hours_window",
            ),
        )


def downgrade() -> None:
    # Forward-only: never remove partner schedule data automatically.
    pass
