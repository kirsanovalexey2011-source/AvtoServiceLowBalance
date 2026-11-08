"""Add email verification and account contact fields.

Revision ID: 0004_account_security
Revises: 0003_marketplace
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_account_security"
down_revision = "0003_marketplace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    additions = (
        ("full_name", sa.String(length=160)),
        ("phone", sa.String(length=32)),
        ("email_verified_at", sa.DateTime(timezone=True)),
        ("phone_verified_at", sa.DateTime(timezone=True)),
    )
    for name, column_type in additions:
        if name not in existing_columns:
            op.add_column("users", sa.Column(name, column_type, nullable=True))

    inspector = sa.inspect(bind)
    if "email_verifications" not in inspector.get_table_names():
        op.create_table(
            "email_verifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=254), nullable=False),
            sa.Column("purpose", sa.String(length=30), nullable=False),
            sa.Column("code_hash", sa.String(length=64), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("attempts >= 0 AND attempts <= 5", name="ck_email_verification_attempts"),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("email_verifications")}
    if "ix_email_verifications_email" not in existing_indexes:
        op.create_index("ix_email_verifications_email", "email_verifications", ["email"])
    if "ix_email_verifications_lookup" not in existing_indexes:
        op.create_index(
            "ix_email_verifications_lookup",
            "email_verifications",
            ["email", "purpose", "created_at"],
        )


def downgrade() -> None:
    # Forward-only by policy: don't risk removing account data from an existing database.
    pass
