from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.api.deps import get_db
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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

def test_register_login_and_duplicate_email(client: TestClient) -> None:
    payload = {"organization_name": "Тестовый автосервис", "email": "owner@example.com", "password": "strong-pass-123"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["organization"] == "Тестовый автосервис"
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 200
    assert client.post("/api/auth/register", json=payload).status_code == 409

def test_client_visit_and_smart_return(client: TestClient) -> None:
    client.post("/api/auth/register", json={"organization_name": "Garage", "email": "a@example.com", "password": "strong-pass-123"})
    created = client.post("/api/clients", json={"full_name": "Иван Петров", "phone": "+79990000000"})
    assert created.status_code == 201
    client_id = created.json()["id"]
    visit = client.post("/api/visits", json={
        "client_id": client_id, "service_name": "Замена масла",
        "next_due_at": "2020-01-01T12:00:00Z", "amount_rub": 6500
    })
    assert visit.status_code == 201
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["clients"] == 1
    assert dashboard["visits"] == 1
    assert dashboard["due"] == 1
    queue = client.get("/api/smart-return").json()
    assert len(queue) == 1
    assert queue[0]["has_marketing_consent"] is False
    assert queue[0]["draft"] is None
    consent = client.post("/api/clients/" + str(client_id) + "/consents", json={
        "channel": "sms", "purpose": "marketing", "granted": True,
        "evidence_reference": "Test consent"
    })
    assert consent.status_code == 201
    queue = client.get("/api/smart-return").json()
    assert queue[0]["has_marketing_consent"] is True
    assert "Иван Петров" in queue[0]["draft"]

def test_workspace_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/clients").status_code == 401
