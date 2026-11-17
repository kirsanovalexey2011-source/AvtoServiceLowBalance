from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import settings


def test_appointment_status_history_migration_backfills_existing_bookings(
    tmp_path, monkeypatch
) -> None:
    database_path = tmp_path / "autoflow-migration.sqlite3"
    monkeypatch.setattr(
        settings,
        "database_url",
        f"sqlite:///{database_path.as_posix()}",
    )
    config = Config("alembic.ini")

    # Stop before the new revision, then insert a legacy booking that has no
    # audit events. The database is isolated under pytest's temporary path.
    command.upgrade(config, "0006_business_working_hours")
    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    created_at = "2026-11-01 09:00:00"

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO organizations (id, name, business_type, created_at)
                    VALUES (1, 'Legacy workshop', 'auto_service', :created_at)
                    """
                ),
                {"created_at": created_at},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO service_offerings (
                        id, organization_id, title, category, duration_minutes, is_active
                    )
                    VALUES (1, 1, 'Diagnostics', 'Diagnostics', 60, 1)
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO appointments (
                        id, organization_id, service_id, customer_name, customer_phone,
                        customer_email, starts_at, ends_at, status, comment, created_at
                    )
                    VALUES (
                        1, 1, 1, 'Legacy customer', '+79990000000', NULL,
                        '2026-11-05 10:00:00', '2026-11-05 11:00:00',
                        'confirmed', NULL, :created_at
                    )
                    """
                ),
                {"created_at": created_at},
            )

        command.upgrade(config, "head")

        with engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT appointment_id, organization_id, previous_status,
                           new_status, actor_type, actor_user_id, changed_at
                    FROM appointment_status_history
                    WHERE appointment_id = 1
                    """
                )
            ).mappings().all()

        assert len(rows) == 1
        assert rows[0]["organization_id"] == 1
        assert rows[0]["previous_status"] is None
        assert rows[0]["new_status"] == "confirmed"
        assert rows[0]["actor_type"] == "system"
        assert rows[0]["actor_user_id"] is None
        assert str(rows[0]["changed_at"]).startswith(created_at)
    finally:
        engine.dispose()
