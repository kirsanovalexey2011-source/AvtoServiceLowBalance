from datetime import date, datetime, time, timedelta, timezone
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.api.auth import limiter
from app.core.config import settings
from app.models import Appointment, BookingLock, BusinessProfile, BusinessWorkingHours, Client, Organization, ServiceOffering, User

router = APIRouter(tags=["marketplace"])


def _lock_organization_bookings(db: Session, organization_id: int) -> None:
    """Serialize booking writes for one organization across SQLite and PostgreSQL."""
    dialect = db.get_bind().dialect.name
    values = {"organization_id": organization_id}
    if dialect == "sqlite":
        statement = sqlite_insert(BookingLock).values(**values).on_conflict_do_nothing(
            index_elements=[BookingLock.organization_id]
        )
    elif dialect == "postgresql":
        statement = postgresql_insert(BookingLock).values(**values).on_conflict_do_nothing(
            index_elements=[BookingLock.organization_id]
        )
    else:
        raise RuntimeError(f"Safe booking locks are not configured for database dialect: {dialect}")

    # The upsert creates the lock row on first use. Updating it obtains a write lock
    # that is held until the surrounding booking transaction commits or rolls back.
    db.execute(statement)
    db.execute(
        update(BookingLock)
        .where(BookingLock.organization_id == organization_id)
        .values(updated_at=datetime.now(timezone.utc))
    )

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


class WorkingDayIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    is_closed: bool = False
    opens_at: time | None = None
    closes_at: time | None = None

    @model_validator(mode="after")
    def validate_working_window(self):
        if self.is_closed:
            return self
        if self.opens_at is None or self.closes_at is None:
            raise ValueError("Для рабочего дня укажите время открытия и закрытия")
        for value in (self.opens_at, self.closes_at):
            if value.minute not in {0, 30} or value.second or value.microsecond:
                raise ValueError("Время должно быть кратно 30 минутам")
        if self.opens_at >= self.closes_at:
            raise ValueError("Время закрытия должно быть позже времени открытия")
        return self


class WorkingHoursIn(BaseModel):
    days: list[WorkingDayIn] = Field(min_length=7, max_length=7)

    @field_validator("days")
    @classmethod
    def require_each_weekday_once(cls, days: list[WorkingDayIn]) -> list[WorkingDayIn]:
        if {day.weekday for day in days} != set(range(7)):
            raise ValueError("Укажите каждый день недели ровно один раз")
        return days


MOSCOW_TZ = timezone(timedelta(hours=3))
DEFAULT_OPENING_TIME = time(hour=9)
DEFAULT_CLOSING_TIME = time(hour=18)


def _get_working_day(db: Session, organization_id: int, weekday: int) -> dict:
    record = db.scalar(select(BusinessWorkingHours).where(
        BusinessWorkingHours.organization_id == organization_id,
        BusinessWorkingHours.weekday == weekday,
    ))
    if record is None:
        return {
            "weekday": weekday,
            "is_closed": False,
            "opens_at": DEFAULT_OPENING_TIME,
            "closes_at": DEFAULT_CLOSING_TIME,
        }
    return {
        "weekday": weekday,
        "is_closed": record.is_closed,
        "opens_at": record.opens_at,
        "closes_at": record.closes_at,
    }


def _working_day_payload(db: Session, organization_id: int, weekday: int) -> dict:
    day = _get_working_day(db, organization_id, weekday)
    return {
        "weekday": weekday,
        "is_closed": day["is_closed"],
        "opens_at": day["opens_at"].isoformat(timespec="minutes") if day["opens_at"] else None,
        "closes_at": day["closes_at"].isoformat(timespec="minutes") if day["closes_at"] else None,
    }


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _booking_fits_working_day(start: datetime, end: datetime, working_day: dict) -> bool:
    if working_day["is_closed"]:
        return False
    local_start = _as_utc(start).astimezone(MOSCOW_TZ)
    local_end = _as_utc(end).astimezone(MOSCOW_TZ)
    if local_start.date() != local_end.date():
        return False
    opening = datetime.combine(local_start.date(), working_day["opens_at"], tzinfo=MOSCOW_TZ)
    closing = datetime.combine(local_start.date(), working_day["closes_at"], tzinfo=MOSCOW_TZ)
    return local_start >= opening and local_end <= closing


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

@router.get("/api/marketplace/availability")
def public_availability(
    service_id: int,
    day: date,
    utc_offset_minutes: int = Query(default=180, ge=-720, le=840),
    db: Session = Depends(get_db),
):
    """Return 30-minute start slots within the partner's configured weekly hours."""
    service = db.scalar(select(ServiceOffering).where(
        ServiceOffering.id == service_id, ServiceOffering.is_active.is_(True)))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    profile = db.scalar(select(BusinessProfile).where(
        BusinessProfile.organization_id == service.organization_id,
        BusinessProfile.is_published.is_(True)))
    if not profile:
        raise HTTPException(status_code=404, detail="Автосервис пока не принимает онлайн-записи")

    if utc_offset_minutes != 180:
        raise HTTPException(status_code=422, detail="Для текущего региона используйте московское время UTC+3")
    local_tz = MOSCOW_TZ
    working_day = _get_working_day(db, service.organization_id, day.weekday())
    if working_day["is_closed"]:
        return {
            "service_id": service.id,
            "date": day.isoformat(),
            "timezone_offset_minutes": 180,
            "working_hours": {"from": None, "to": None, "is_closed": True},
            "slot_step_minutes": 30,
            "slots": [],
        }
    opening = datetime.combine(day, working_day["opens_at"], tzinfo=local_tz)
    closing = datetime.combine(day, working_day["closes_at"], tzinfo=local_tz)
    now = datetime.now(timezone.utc)
    duration = timedelta(minutes=service.duration_minutes)
    bookings = db.scalars(select(Appointment).where(
        Appointment.organization_id == service.organization_id,
        Appointment.status.in_(["pending", "confirmed"]),
        Appointment.starts_at < closing.astimezone(timezone.utc),
        Appointment.ends_at > opening.astimezone(timezone.utc),
    )).all()
    slots = []
    cursor = opening
    while cursor + duration <= closing:
        start_utc = cursor.astimezone(timezone.utc)
        end_utc = (cursor + duration).astimezone(timezone.utc)
        has_conflict = False
        for booking in bookings:
            booked_start = booking.starts_at
            booked_end = booking.ends_at
            if booked_start.tzinfo is None:
                booked_start = booked_start.replace(tzinfo=timezone.utc)
            if booked_end.tzinfo is None:
                booked_end = booked_end.replace(tzinfo=timezone.utc)
            if booked_start < end_utc and booked_end > start_utc:
                has_conflict = True
                break
        if start_utc >= now + timedelta(minutes=15) and not has_conflict:
            slots.append(cursor.isoformat())
        cursor += timedelta(minutes=30)
    return {
        "service_id": service.id,
        "date": day.isoformat(),
        "timezone_offset_minutes": utc_offset_minutes,
        "working_hours": {
            "from": working_day["opens_at"].isoformat(timespec="minutes"),
            "to": working_day["closes_at"].isoformat(timespec="minutes"),
            "is_closed": False,
        },
        "slot_step_minutes": 30,
        "slots": slots,
    }


@router.post("/api/marketplace/bookings", status_code=201)
@limiter.limit("5/minute")
def create_public_booking(request: Request, payload: BookingIn, db: Session = Depends(get_db)):
    service = db.scalar(select(ServiceOffering).where(
        ServiceOffering.id == payload.service_id, ServiceOffering.is_active.is_(True)))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    organization_id = service.organization_id

    start = payload.starts_at
    if start.tzinfo is None:
        raise HTTPException(status_code=422, detail="Укажите часовой пояс времени записи")
    start = start.astimezone(timezone.utc)
    local_start = start.astimezone(MOSCOW_TZ)
    if local_start.minute not in {0, 30} or local_start.second or local_start.microsecond:
        raise HTTPException(status_code=422, detail="Выберите время из доступных 30-минутных интервалов")

    # End the read transaction before taking the per-organization write lock.
    # This is important for SQLite, where a deferred read transaction cannot
    # always be upgraded safely after another writer has committed.
    db.commit()
    _lock_organization_bookings(db, organization_id)

    # Re-read mutable service/profile data after acquiring the lock.
    service = db.scalar(select(ServiceOffering).where(
        ServiceOffering.id == payload.service_id,
        ServiceOffering.organization_id == organization_id,
        ServiceOffering.is_active.is_(True),
    ))
    if not service:
        raise HTTPException(status_code=404, detail="Услуга недоступна")
    profile = db.scalar(select(BusinessProfile).where(
        BusinessProfile.organization_id == organization_id,
        BusinessProfile.is_published.is_(True),
    ))
    if not profile:
        raise HTTPException(status_code=404, detail="Автосервис пока не принимает онлайн-записи")

    if start < datetime.now(timezone.utc) + timedelta(minutes=15):
        raise HTTPException(status_code=422, detail="Выберите время не менее чем через 15 минут")
    end = start + timedelta(minutes=service.duration_minutes)
    working_day = _get_working_day(db, organization_id, local_start.weekday())
    if not _booking_fits_working_day(start, end, working_day):
        raise HTTPException(status_code=422, detail="Выбранное время не соответствует графику работы автосервиса")

    conflict = db.scalar(select(Appointment.id).where(
        Appointment.organization_id == organization_id,
        Appointment.status.in_(["pending", "confirmed"]),
        Appointment.starts_at < end, Appointment.ends_at > start,
    ).limit(1))
    if conflict:
        raise HTTPException(status_code=409, detail="Это время уже занято. Выберите другое.")

    booking = Appointment(
        organization_id=organization_id, service_id=service.id,
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

@router.get("/api/partner/working-hours")
def partner_working_hours(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"days": [_working_day_payload(db, user.organization_id, weekday) for weekday in range(7)]}


@router.put("/api/partner/working-hours")
def save_partner_working_hours(
    payload: WorkingHoursIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Serialize schedule changes with booking writes so a booking cannot be
    # created using a schedule that was changed concurrently.
    db.commit()
    _lock_organization_bookings(db, user.organization_id)

    proposed = {
        day.weekday: {
            "weekday": day.weekday,
            "is_closed": day.is_closed,
            "opens_at": None if day.is_closed else day.opens_at,
            "closes_at": None if day.is_closed else day.closes_at,
        }
        for day in payload.days
    }
    now = datetime.now(timezone.utc)
    active_bookings = db.scalars(select(Appointment).where(
        Appointment.organization_id == user.organization_id,
        Appointment.status.in_(["pending", "confirmed"]),
        Appointment.starts_at >= now,
    )).all()
    for booking in active_bookings:
        start = _as_utc(booking.starts_at)
        end = _as_utc(booking.ends_at)
        weekday = start.astimezone(MOSCOW_TZ).weekday()
        if not _booking_fits_working_day(start, end, proposed[weekday]):
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Нельзя изменить график: есть ожидающие или подтверждённые записи вне нового времени. Сначала перенесите или отмените их.",
            )

    existing = {
        item.weekday: item
        for item in db.scalars(select(BusinessWorkingHours).where(
            BusinessWorkingHours.organization_id == user.organization_id
        )).all()
    }
    for weekday, day in proposed.items():
        record = existing.get(weekday)
        if record is None:
            record = BusinessWorkingHours(
                organization_id=user.organization_id,
                weekday=weekday,
            )
            db.add(record)
        record.is_closed = day["is_closed"]
        record.opens_at = day["opens_at"]
        record.closes_at = day["closes_at"]

    db.commit()
    return {"days": [_working_day_payload(db, user.organization_id, weekday) for weekday in range(7)]}


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
    organization_id = booking.organization_id

    db.commit()
    _lock_organization_bookings(db, organization_id)
    booking = db.scalar(select(Appointment).where(
        Appointment.id == booking_id, Appointment.organization_id == organization_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    if payload.status == "confirmed":
        conflict = db.scalar(select(Appointment.id).where(
            Appointment.organization_id == organization_id,
            Appointment.id != booking.id,
            Appointment.status.in_(["pending", "confirmed"]),
            Appointment.starts_at < booking.ends_at,
            Appointment.ends_at > booking.starts_at,
        ).limit(1))
        if conflict:
            raise HTTPException(status_code=409, detail="На это время уже есть другая активная запись")
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

@router.get("/api/platform/clients")
def platform_clients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_platform_admin(user)
    rows = db.execute(select(Client, Organization.name).join(
        Organization, Organization.id == Client.organization_id
    ).order_by(Client.created_at.desc()).limit(1000)).all()
    return [{"id": client.id, "organization": organization, "name": client.full_name,
             "phone": client.phone, "email": client.email, "created_at": client.created_at.isoformat()}
            for client, organization in rows]

@router.get("/api/platform/overview")
def platform_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    admin_email = (settings.platform_admin_email or "").strip().lower()
    if not admin_email or user.email.lower() != admin_email:
        raise HTTPException(status_code=403, detail="Доступ только для администратора платформы")
    organizations = db.scalar(select(func.count(Organization.id))) or 0
    customers = db.scalar(select(func.count(Client.id))) or 0
    booking_requests = db.scalar(select(func.count(Appointment.id))) or 0
    pending = db.scalar(select(func.count(Appointment.id)).where(Appointment.status == "pending")) or 0
    published = db.scalar(select(func.count(BusinessProfile.id)).where(BusinessProfile.is_published.is_(True))) or 0
    return {"organizations": organizations, "published_businesses": published,
            "customers": customers, "booking_requests": booking_requests, "pending_bookings": pending}
