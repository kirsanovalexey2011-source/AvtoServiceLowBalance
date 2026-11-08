from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    business_type: Mapped[str] = mapped_column(String(40), default="auto_service")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    users: Mapped[list["User"]] = relationship(back_populates="organization")
    clients: Mapped[list["Client"]] = relationship(back_populates="organization")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(30), default="owner")
    organization: Mapped[Organization] = relationship(back_populates="users")

class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (Index("ix_clients_org_created", "organization_id", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    organization: Mapped[Organization] = relationship(back_populates="clients")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="client", cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (Index("ix_vehicles_org_client", "organization_id", "client_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    make: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(80))
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plate_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client: Mapped[Client] = relationship(back_populates="vehicles")

class ServiceVisit(Base):
    __tablename__ = "service_visits"
    __table_args__ = (
        Index("ix_visits_org_next_due", "organization_id", "next_due_at"),
        Index("ix_visits_org_client_visited", "organization_id", "client_id", "visited_at"),
        CheckConstraint("amount_minor IS NULL OR amount_minor >= 0", name="ck_visits_nonnegative_amount"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    service_name: Mapped[str] = mapped_column(String(160))
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    next_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class ReminderRule(Base):
    __tablename__ = "reminder_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    business_type: Mapped[str] = mapped_column(String(40), default="auto_service")
    service_name: Mapped[str] = mapped_column(String(160))
    days_after_visit: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class ConsentRecord(Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("ix_consents_org_client_purpose_time", "organization_id", "client_id", "purpose", "captured_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    channel: Mapped[str] = mapped_column(String(30))
    purpose: Mapped[str] = mapped_column(String(40))
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)

class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("reminder_rules.id"), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    channel: Mapped[str] = mapped_column(String(30), default="manual")
    message_text: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class DeferredService(Base):
    __tablename__ = "deferred_services"
    __table_args__ = (
        Index("ix_deferred_org_status_followup", "organization_id", "status", "follow_up_at"),
        CheckConstraint("estimated_amount_minor IS NULL OR estimated_amount_minor >= 0", name="ck_deferred_nonnegative_amount"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    service_name: Mapped[str] = mapped_column(String(160))
    estimated_amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open")
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
