from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.api.auth import limiter
from app.core.config import settings
from app.models import Appointment, BusinessProfile, Organization, ServiceOffering, User

router = APIRouter(tags=["marketplace"])

class ProfileIn(BaseModel):
    public_name: str = Field(min_length=2, max_length=160)
    city: str = Field(min_length=2, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    address: str = Field(min_length=5, max_length=300)
    phone: str = Field(min_length=6, max_length=32)
    description: str | None = Field(default=None, max_length=3000)
    website: str | None = Field(default=None, max_length=300)

class ServiceIn(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    category: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2000)
    price_from_rub: int | None = Field(default=None, ge=0, le=100000000)
    duration_minutes: int = Field(default=60, ge=15, le=1440)
    is_active: bool = True

class BookingIn(BaseModel):
    service_id: int
    customer_name: str = Field(min_length=2, max_length=160)
    customer_phone: str = Field(min_length=6, max_length=32)
    customer_email: EmailStr | None = None
    starts_at: datetime
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("customer_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Укажите имя")
        return value

class BookingStatusIn(BaseModel):
    status: str = Field(pattern="^(confirmed|cancelled|completed)$")

def profile_payload(profile: BusinessProfile, services_count: int = 0) -> dict:
    return {
        "id": profile.id, "organization_id": profile.organization_id,
        "name": profile.public_name, "city": profile.city, "district": profile.district,
        "address": profile.address, "phone": profile.phone, "description": profile.description,
        "website": profile.website, "is_published": profile.is_published,
        "services_count": services_count,
    }

@router.get("/api/marketplace/services")
def public_services(city: str | None = None, district: str | None = None, category: str | None = None,
                    q: str | None = None, db: Session = Depends(get_db)):
    stmt = (select(ServiceOffering, BusinessProfile)
            .join(BusinessProfile, BusinessProfile.organization_id == ServiceOffering.organization_id)
            .where(ServiceOffering.is_active.is_(True), BusinessProfile.is_published.is_(True)))
    if city:
        stmt = stmt.where(BusinessProfile.city == city)
    if district:
        stmt = stmt.where(BusinessProfile.district == district)
    if category:
        stmt = stmt.where(ServiceOffering.category == category)
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where((ServiceOffering.title.ilike(term)) | (BusinessProfile.public_name.ilike(term)))
    rows = db.execute(stmt.order_by(BusinessProfile.public_name, ServiceOffering.title).limit(200)).all()
    return [{
        "service_id": service.id, "organization_id": service.organization_id,
        "service": service.title, "category": service.category,
        "description": service.description, "price_from_rub": service.price_from_rub,
        "duration_minutes": service.duration_minutes,
        "business": profile.public_name, "city": profile.city, "district": profile.district,
        "address": profile.address, "phone": profile.phone,
    } for service, profile in rows]

@router.get("/api/marketplace/businesses/{organization_id}")
def public_business(organization_id: int, db: Session = Depends(get_db)):
    profile = db.scalar(select(BusinessProfile).where(
        BusinessProfile.organization_id == organization_id, BusinessProfile.is_published.is_(True)))
    if not profile:
        raise HTTPException(status_code=404, detail="Автосервис не найден")
    services = db.scalars(select(ServiceOffering).where(
        ServiceOffering.organization_id == organization_id, ServiceOffering.is_active.is_(True))).all()
    return {**profile_payload(profile, len(services)), "services": [{
        "id": s.id, "title": s.title, "category": s.category, "description": s.description,
        "price_from_rub": s.price_from_rub, "duration_minutes": s.duration_minutes,
    } for s in services]}

@router.post("/api/marketplace/bookings", status_code=201)
@limiter.limit("5/minute")
def create_public_booking(request: Request, payload: BookingIn, db: Session = Depends(get_db)):
    service = db.scalar(select(ServiceOffering).where(
        ServiceOffering.id == payload.service_id, ServiceOffering.is_active.is_(True)))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    profile = db.scalar(select(BusinessProfile).where(
        BusinessProfile.organization_id == service.organization_id, BusinessProfile.is_published.is_(True)))
    if not profile:
        raise HTTPException(status_code=404, detail="Автосервис пока не принимает онлайн-записи")
    start = payload.starts_at
    if start.tzinfo is None:
        raise HTTPException(status_code=422, detail="Укажите часовой пояс времени записи")
    start = start.astimezone(timezone.utc)
    if start < datetime.now(timezone.utc) + timedelta(minutes=15):
        raise HTTPException(status_code=422, detail="Выберите время не менее чем через 15 минут")
    end = start + timedelta(minutes=service.duration_minutes)
    conflict = db.scalar(select(Appointment.id).where(
        Appointment.organization_id == service.organization_id,
        Appointment.status.in_(["pending", "confirmed"]),
        Appointment.starts_at < end, Appointment.ends_at > start,
    ).limit(1))
    if conflict:
        raise HTTPException(status_code=409, detail="Это время уже занято. Выберите другое.")
    booking = Appointment(
        organization_id=service.organization_id, service_id=service.id,
        customer_name=payload.customer_name.strip(), customer_phone=payload.customer_phone.strip(),
        customer_email=str(payload.customer_email).lower() if payload.customer_email else None,
        starts_at=start, ends_at=end, comment=payload.comment, status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"id": booking.id, "status": booking.status, "message": "Заявка отправлена автосервису. Дождитесь подтверждения."}

@router.get("/api/partner/profile")
def partner_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.organization_id == user.organization_id))
    return profile_payload(profile) if profile else None

@router.put("/api/partner/profile")
def save_partner_profile(payload: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.organization_id == user.organization_id))
    if profile is None:
        profile = BusinessProfile(organization_id=user.organization_id, **payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile_payload(profile)

@router.post("/api/partner/services", status_code=201)
def create_partner_service(payload: ServiceIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = ServiceOffering(organization_id=user.organization_id, **payload.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return {"id": service.id, "title": service.title}

@router.get("/api/partner/services")
def list_partner_services(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(ServiceOffering).where(
        ServiceOffering.organization_id == user.organization_id).order_by(ServiceOffering.id.desc())).all()
    return [{"id": s.id, "title": s.title, "category": s.category, "price_from_rub": s.price_from_rub,
             "duration_minutes": s.duration_minutes, "is_active": s.is_active} for s in rows]

@router.get("/api/partner/bookings")
def list_partner_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(Appointment, ServiceOffering.title).join(
        ServiceOffering, ServiceOffering.id == Appointment.service_id).where(
        Appointment.organization_id == user.organization_id).order_by(Appointment.starts_at.desc()).limit(300)).all()
    return [{"id": a.id, "service": title, "customer_name": a.customer_name,
             "customer_phone": a.customer_phone, "customer_email": a.customer_email,
             "starts_at": a.starts_at.isoformat(), "status": a.status, "comment": a.comment}
            for a, title in rows]

@router.patch("/api/partner/bookings/{booking_id}")
def update_partner_booking(booking_id: int, payload: BookingStatusIn,
                           db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    booking = db.scalar(select(Appointment).where(
        Appointment.id == booking_id, Appointment.organization_id == user.organization_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if payload.status == "confirmed":
        conflict = db.scalar(select(Appointment.id).where(
            Appointment.organization_id == user.organization_id, Appointment.id != booking.id,
            Appointment.status == "confirmed", Appointment.starts_at < booking.ends_at,
            Appointment.ends_at > booking.starts_at).limit(1))
        if conflict:
            raise HTTPException(status_code=409, detail="На это время уже подтверждена другая запись")
    booking.status = payload.status
    db.commit()
    return {"id": booking.id, "status": booking.status}

def require_platform_admin(user: User) -> None:
    admin_email = (settings.platform_admin_email or "").strip().lower()
    if not admin_email or user.email.lower() != admin_email:
        raise HTTPException(status_code=403, detail="Доступ только для администратора платформы")

@router.get("/api/platform/businesses")
def platform_businesses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_platform_admin(user)
    rows = db.execute(select(BusinessProfile, Organization.name).join(
        Organization, Organization.id == BusinessProfile.organization_id
    ).order_by(BusinessProfile.created_at.desc()).limit(500)).all()
    result = []
    for profile, organization_name in rows:
        services = db.scalars(select(ServiceOffering).where(
            ServiceOffering.organization_id == profile.organization_id).order_by(ServiceOffering.id)).all()
        result.append({**profile_payload(profile, len(services)), "organization": organization_name,
                       "services": [{"id": s.id, "title": s.title, "category": s.category,
                                     "price_from_rub": s.price_from_rub, "active": s.is_active} for s in services]})
    return result

@router.patch("/api/platform/businesses/{organization_id}/publish")
def platform_publish_business(organization_id: int, db: Session = Depends(get_db),
                              user: User = Depends(get_current_user)):
    require_platform_admin(user)
    profile = db.scalar(select(BusinessProfile).where(BusinessProfile.organization_id == organization_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Профиль автосервиса не найден")
    profile.is_published = not profile.is_published
    db.commit()
    return {"organization_id": organization_id, "is_published": profile.is_published}

@router.get("/api/platform/bookings")
def platform_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_platform_admin(user)
    rows = db.execute(select(Appointment, BusinessProfile.public_name, ServiceOffering.title).join(
        BusinessProfile, BusinessProfile.organization_id == Appointment.organization_id
    ).join(ServiceOffering, ServiceOffering.id == Appointment.service_id)
     .order_by(Appointment.created_at.desc()).limit(1000)).all()
    return [{"id": a.id, "business": business, "service": service, "customer_name": a.customer_name,
             "customer_phone": a.customer_phone, "customer_email": a.customer_email,
             "starts_at": a.starts_at.isoformat(), "status": a.status} for a, business, service in rows]

@router.get("/api/platform/overview")
def platform_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    admin_email = (settings.platform_admin_email or "").strip().lower()
    if not admin_email or user.email.lower() != admin_email:
        raise HTTPException(status_code=403, detail="Доступ только для администратора платформы")
    organizations = db.scalar(select(func.count(Organization.id))) or 0
    customers = db.scalar(select(func.count(Appointment.id))) or 0
    pending = db.scalar(select(func.count(Appointment.id)).where(Appointment.status == "pending")) or 0
    published = db.scalar(select(func.count(BusinessProfile.id)).where(BusinessProfile.is_published.is_(True))) or 0
    return {"organizations": organizations, "published_businesses": published,
            "booking_requests": customers, "pending_bookings": pending}
