from collections.abc import Generator
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
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
    start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(second=0, microsecond=0)
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
