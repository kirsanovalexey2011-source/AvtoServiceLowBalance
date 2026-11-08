from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.auth as auth_module
from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    # TestClient shares one IP across modules; reset counters to isolate tests.
    auth_module.limiter._storage.reset()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    auth_module.limiter._storage.reset()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_registration_requires_and_accepts_verified_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mailbox: dict[str, str] = {}
    monkeypatch.setattr(
        auth_module,
        "send_verification_email",
        lambda email, code, purpose: mailbox.__setitem__(email, code),
    )
    old_env = settings.app_env
    settings.app_env = "production"
    try:
        requested = client.post("/api/auth/email-code", json={
            "email": "new-owner@example.com",
            "purpose": "registration",
        })
        assert requested.status_code == 200
        assert requested.json()["expires_in_seconds"] == 600

        wrong = client.post("/api/auth/verify-email-code", json={
            "email": "new-owner@example.com",
            "code": "000000",
            "purpose": "registration",
        })
        assert wrong.status_code == 400

        verified = client.post("/api/auth/verify-email-code", json={
            "email": "new-owner@example.com",
            "code": mailbox["new-owner@example.com"],
            "purpose": "registration",
        })
        assert verified.status_code == 200
        token = verified.json()["verification_token"]

        payload = {
            "organization_name": "Новая СТО",
            "email": "new-owner@example.com",
            "password": "strong-pass-123",
        }
        assert client.post("/api/auth/register", json=payload).status_code == 400
        created = client.post("/api/auth/register", json={
            **payload,
            "email_verification_token": token,
        })
        assert created.status_code == 201
        assert created.json()["email_verified"] is True
    finally:
        settings.app_env = old_env


def test_profile_phone_and_existing_account_email_verification(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mailbox: dict[str, str] = {}
    monkeypatch.setattr(
        auth_module,
        "send_verification_email",
        lambda email, code, purpose: mailbox.__setitem__(email, code),
    )
    created = client.post("/api/auth/register", json={
        "organization_name": "Гараж",
        "email": "owner@example.com",
        "password": "strong-pass-123",
    })
    assert created.status_code == 201

    updated = client.patch("/api/auth/profile", json={
        "full_name": "Иван Петров",
        "phone": "+7 (999) 123-45-67",
    })
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Иван Петров"
    assert updated.json()["phone"] == "+79991234567"
    assert updated.json()["phone_verified"] is False
    assert client.patch("/api/auth/profile", json={"phone": "not-a-phone"}).status_code == 422

    requested = client.post("/api/auth/email-code", json={
        "email": "owner@example.com",
        "purpose": "account",
    })
    assert requested.status_code == 200
    verified = client.post("/api/auth/verify-email-code", json={
        "email": "owner@example.com",
        "code": mailbox["owner@example.com"],
        "purpose": "account",
    })
    assert verified.status_code == 200

    profile = client.get("/api/auth/profile").json()
    assert profile["email_verified"] is True
    assert profile["phone"] == "+79991234567"
