"""Add an append-only audit trail for appointment status changes.

Revision ID: 0007_appointment_status_history
Revises: 0006_business_working_hours
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_appointment_status_history"
down_revision = "0006_business_working_hours"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "appointment_status_history" not in inspector.get_table_names():
        op.create_table(
            "appointment_status_history",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "appointment_id",
                sa.Integer(),
                sa.ForeignKey("appointments.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column(
                "organization_id",
                sa.Integer(),
                sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("previous_status", sa.String(length=20), nullable=True),
            sa.Column("new_status", sa.String(length=20), nullable=False),
            sa.Column("actor_type", sa.String(length=20), nullable=False),
            sa.Column(
                "actor_user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "changed_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint(
                "previous_status IS NULL OR previous_status IN "
                "('pending', 'confirmed', 'cancelled', 'completed')",
                name="ck_appointment_status_history_previous_status",
            ),
            sa.CheckConstraint(
                "new_status IN ('pending', 'confirmed', 'cancelled', 'completed')",
                name="ck_appointment_status_history_new_status",
            ),
            sa.CheckConstraint(
                "actor_type IN ('customer', 'partner', 'system')",
                name="ck_appointment_status_history_actor_type",
            ),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {
        item["name"] for item in inspector.get_indexes("appointment_status_history")
    }
    if "ix_appointment_status_history_appointment_time" not in existing_indexes:
        op.create_index(
            "ix_appointment_status_history_appointment_time",
            "appointment_status_history",
            ["appointment_id", "changed_at", "id"],
        )
    if "ix_appointment_status_history_org_time" not in existing_indexes:
        op.create_index(
            "ix_appointment_status_history_org_time",
            "appointment_status_history",
            ["organization_id", "changed_at"],
        )

    # Existing appointments receive one baseline event. This records their
    # current known state without inventing transitions that were never stored.
    op.execute(sa.text(
        """
        INSERT INTO appointment_status_history (
            appointment_id,
            organization_id,
            previous_status,
            new_status,
            actor_type,
            actor_user_id,
            changed_at
        )
        SELECT
            appointment.id,
            appointment.organization_id,
            NULL,
            appointment.status,
            'system',
            NULL,
            appointment.created_at
        FROM appointments AS appointment
        WHERE NOT EXISTS (
            SELECT 1
            FROM appointment_status_history AS history
            WHERE history.appointment_id = appointment.id
        )
        """
    ))


def downgrade() -> None:
    # Forward-only: never remove appointment audit history automatically.
    pass
