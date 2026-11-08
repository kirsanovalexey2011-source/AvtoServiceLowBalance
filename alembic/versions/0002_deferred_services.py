"""Add declined-service recovery records.

Revision ID: 0002_deferred
Revises: 0001_initial
"""
from alembic import op
from app.models.entities import DeferredService

revision = "0002_deferred"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade() -> None:
    DeferredService.__table__.create(bind=op.get_bind(), checkfirst=True)

def downgrade() -> None:
    # Keep customer/business records safe; mark this migration as non-destructive.
    pass
