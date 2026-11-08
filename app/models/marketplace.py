from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class BusinessProfile(Base):
    __tablename__ = "business_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), unique=True, index=True)
    public_name: Mapped[str] = mapped_column(String(160))
    city: Mapped[str] = mapped_column(String(100), default="Санкт-Петербург", index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    address: Mapped[str] = mapped_column(String(300))
    phone: Mapped[str] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ServiceOffering(Base):
    __tablename__ = "service_offerings"
    __table_args__ = (Index("ix_offerings_org_active", "organization_id", "is_active"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_from_rub: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_org_start", "organization_id", "starts_at"),
        Index("ix_appointments_customer_phone", "customer_phone"),
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled', 'completed')", name="ck_appointment_status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("service_offerings.id"), index=True)
    customer_name: Mapped[str] = mapped_column(String(160))
    customer_phone: Mapped[str] = mapped_column(String(32))
    customer_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
