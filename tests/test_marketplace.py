from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
import app.main as main_module
from app.models import Appointment
from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_db
    old_admin = settings.platform_admin_email
    settings.platform_admin_email = "platform@example.com"
    with TestClient(app) as test_client:
        yield test_client
    settings.platform_admin_email = old_admin
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

def register(client: TestClient, email: str = "platform@example.com") -> None:
    response = client.post("/api/auth/register", json={
        "organization_name": "AutoFlow Partner", "email": email, "password": "strong-pass-123"
    })
    assert response.status_code == 201

def test_partner_profile_service_public_listing_and_booking(client: TestClient) -> None:
    register(client)
    profile = client.put("/api/partner/profile", json={
        "public_name": "Гараж Север", "city": "Санкт-Петербург", "district": "Приморский",
        "address": "Санкт-Петербург, улица Савушкина, 10", "phone": "+79990000000",
        "description": "Ремонт и обслуживание автомобилей"
    })
    assert profile.status_code == 200
    service = client.post("/api/partner/services", json={
        "title": "Замена масла", "category": "ТО", "price_from_rub": 3500, "duration_minutes": 60
    })
    assert service.status_code == 201
    assert client.get("/api/marketplace/services").json() == []
    published = client.patch("/api/platform/businesses/1/publish")
    assert published.status_code == 200
    results = client.get("/api/marketplace/services?city=Санкт-Петербург").json()
    assert len(results) == 1
    assert results[0]["business"] == "Гараж Север"
    booking_day = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    moscow_tz = timezone(timedelta(hours=3))
    start = datetime.combine(booking_day, time(hour=10), tzinfo=moscow_tz).astimezone(timezone.utc)
    payload = {"service_id": service.json()["id"], "customer_name": "Алексей",
               "customer_phone": "+79991112233", "starts_at": start.isoformat()}
    booking = client.post("/api/marketplace/bookings", json=payload)
    assert booking.status_code == 201
    assert booking.json()["status"] == "pending"
    conflict = client.post("/api/marketplace/bookings", json=payload)
    assert conflict.status_code == 409
    partner_bookings = client.get("/api/partner/bookings").json()
    assert len(partner_bookings) == 1
    assert partner_bookings[0]["customer_name"] == "Алексей"
    confirmed = client.patch(f"/api/partner/bookings/{booking.json()['id']}", json={"status": "confirmed"})
    assert confirmed.status_code == 200
    platform_bookings = client.get("/api/platform/bookings").json()
    assert len(platform_bookings) == 1
    assert client.get("/api/platform/clients").status_code == 200

def test_platform_endpoints_are_restricted(client: TestClient) -> None:
    register(client, "ordinary@example.com")
    assert client.get("/api/platform/overview").status_code == 403
    assert client.get("/api/platform/businesses").status_code == 403

def test_role_selection_and_workspace_pages(client: TestClient) -> None:
    home = client.get("/")
    assert home.status_code == 200
    assert "Разработчик" in home.text
    assert "Клиент" in home.text
    assert "Продавец услуг" in home.text
    assert client.get("/platform-login").status_code == 200
    assert client.get("/workspace").status_code == 200
    assert client.get("/marketplace").status_code == 200

def test_public_availability_returns_free_slots_and_hides_booked_time(client: TestClient) -> None:
    register(client)
    profile = client.put("/api/partner/profile", json={
        "public_name": "Сервис Север", "city": "Санкт-Петербург",
        "address": "Санкт-Петербург, Невский проспект, 10",
        "phone": "+79990000000",
    })
    assert profile.status_code == 200
    service = client.post("/api/partner/services", json={
        "title": "Диагностика", "category": "Диагностика",
        "duration_minutes": 60,
    })
    assert service.status_code == 201
    assert client.patch("/api/platform/businesses/1/publish").status_code == 200

    day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    query = {"service_id": service.json()["id"], "day": day.isoformat()}
    available = client.get("/api/marketplace/availability", params=query)
    assert available.status_code == 200
    data = available.json()
    assert data["working_hours"] == {"from": "09:00", "to": "18:00"}
    assert data["slot_step_minutes"] == 30

    outside_hours = client.post("/api/marketplace/bookings", json={
        "service_id": service.json()["id"],
        "customer_name": "Алексей",
        "customer_phone": "+79991112233",
        "starts_at": f"{day.isoformat()}T08:30:00+03:00",
    })
    assert outside_hours.status_code == 422

    first_slot = datetime.fromisoformat(data["slots"][0])
    booking = client.post("/api/marketplace/bookings", json={
        "service_id": service.json()["id"],
        "customer_name": "Алексей",
        "customer_phone": "+79991112233",
        "starts_at": first_slot.isoformat(),
    })
    assert booking.status_code == 201

    refreshed = client.get("/api/marketplace/availability", params=query)
    assert refreshed.status_code == 200
    assert first_slot.isoformat() not in refreshed.json()["slots"]


def test_concurrent_overlapping_bookings_only_reserve_once(tmp_path) -> None:
    database_path = tmp_path / "autoflow-booking-race.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    old_admin = settings.platform_admin_email
    old_engine = main_module.engine
    settings.platform_admin_email = "platform@example.com"
    main_module.engine = engine
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as setup_client, \
             TestClient(app, client=("127.0.0.1", 50001)) as first_client, \
             TestClient(app, client=("127.0.0.2", 50002)) as second_client:
            register(setup_client)
            profile = setup_client.put("/api/partner/profile", json={
                "public_name": "Сервис Север", "city": "Санкт-Петербург",
                "address": "Санкт-Петербург, Невский проспект, 10",
                "phone": "+79990000000",
            })
            assert profile.status_code == 200
            service = setup_client.post("/api/partner/services", json={
                "title": "Диагностика", "category": "Диагностика",
                "duration_minutes": 60,
            })
            assert service.status_code == 201
            assert setup_client.patch("/api/platform/businesses/1/publish").status_code == 200

            booking_day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
            moscow_tz = timezone(timedelta(hours=3))
            starts = [
                datetime.combine(booking_day, time(hour=10), tzinfo=moscow_tz),
                datetime.combine(booking_day, time(hour=10, minute=30), tzinfo=moscow_tz),
            ]
            payloads = [{
                "service_id": service.json()["id"],
                "customer_name": f"Клиент {index + 1}",
                "customer_phone": f"+7999000000{index + 1}",
                "starts_at": starts[index].isoformat(),
            } for index in range(2)]

            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(first_client.post, "/api/marketplace/bookings", json=payloads[0])
                second = executor.submit(second_client.post, "/api/marketplace/bookings", json=payloads[1])
                statuses = [first.result().status_code, second.result().status_code]

            assert sorted(statuses) == [201, 409]

        with TestingSession() as db:
            assert db.scalar(select(func.count()).select_from(Appointment)) == 1
    finally:
        settings.platform_admin_email = old_admin
        main_module.engine = old_engine
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_partner_working_hours_control_availability_and_preserve_existing_bookings(client: TestClient) -> None:
    register(client)
    profile = client.put("/api/partner/profile", json={
        "public_name": "Сервис Север", "city": "Санкт-Петербург",
        "address": "Санкт-Петербург, Невский проспект, 10",
        "phone": "+79990000000",
    })
    assert profile.status_code == 200
    service = client.post("/api/partner/services", json={
        "title": "Диагностика", "category": "Диагностика", "duration_minutes": 60,
    })
    assert service.status_code == 201
    assert client.patch("/api/platform/businesses/1/publish").status_code == 200

    defaults = client.get("/api/partner/working-hours")
    assert defaults.status_code == 200
    assert len(defaults.json()["days"]) == 7
    assert all(day["opens_at"] == "09:00" and day["closes_at"] == "18:00" for day in defaults.json()["days"])

    day = (datetime.now(timezone.utc) + timedelta(days=3)).date()
    working_weekday = day.weekday()
    invalid_schedule = {"days": [
        {"weekday": 0, "is_closed": False, "opens_at": "10:00", "closes_at": "10:00"}
        for _ in range(7)
    ]}
    assert client.put("/api/partner/working-hours", json=invalid_schedule).status_code == 422

    schedule = {"days": [
        {
            "weekday": weekday,
            "is_closed": weekday != working_weekday,
            "opens_at": "10:00" if weekday == working_weekday else None,
            "closes_at": "16:00" if weekday == working_weekday else None,
        }
        for weekday in range(7)
    ]}
    saved = client.put("/api/partner/working-hours", json=schedule)
    assert saved.status_code == 200

    query = {"service_id": service.json()["id"], "day": day.isoformat()}
    availability = client.get("/api/marketplace/availability", params=query)
    assert availability.status_code == 200
    data = availability.json()
    assert data["working_hours"] == {"from": "10:00", "to": "16:00", "is_closed": False}
    assert datetime.fromisoformat(data["slots"][0]).astimezone(timezone(timedelta(hours=3))).time() == time(hour=10)

    closed_day = day + timedelta(days=1)
    closed = client.get("/api/marketplace/availability", params={
        "service_id": service.json()["id"], "day": closed_day.isoformat(),
    })
    assert closed.status_code == 200
    assert closed.json()["working_hours"]["is_closed"] is True
    assert closed.json()["slots"] == []

    outside = client.post("/api/marketplace/bookings", json={
        "service_id": service.json()["id"],
        "customer_name": "Алексей",
        "customer_phone": "+79991112233",
        "starts_at": f"{day.isoformat()}T09:30:00+03:00",
    })
    assert outside.status_code == 422

    first_slot = datetime.fromisoformat(data["slots"][0])
    booking = client.post("/api/marketplace/bookings", json={
        "service_id": service.json()["id"],
        "customer_name": "Алексей",
        "customer_phone": "+79991112233",
        "starts_at": first_slot.isoformat(),
    })
    assert booking.status_code == 201

    closed_with_existing_booking = {"days": [
        {"weekday": weekday, "is_closed": True, "opens_at": None, "closes_at": None}
        for weekday in range(7)
    ]}
    rejected = client.put("/api/partner/working-hours", json=closed_with_existing_booking)
    assert rejected.status_code == 409
    current = client.get("/api/partner/working-hours").json()["days"]
    assert current[working_weekday]["is_closed"] is False
