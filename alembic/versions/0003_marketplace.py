"""Add public marketplace profiles, services and appointment requests.

Revision ID: 0003_marketplace
Revises: 0002_deferred
"""
from alembic import op
from app.models.marketplace import BusinessProfile, ServiceOffering, Appointment

revision = "0003_marketplace"
down_revision = "0002_deferred"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    BusinessProfile.__table__.create(bind=bind, checkfirst=True)
    ServiceOffering.__table__.create(bind=bind, checkfirst=True)
    Appointment.__table__.create(bind=bind, checkfirst=True)

def downgrade() -> None:
    # Preserve customer booking data; use a forward migration for future schema changes.
    pass
