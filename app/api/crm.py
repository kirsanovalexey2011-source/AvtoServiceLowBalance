from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.models import Client, ConsentRecord, ServiceVisit, User, Vehicle

router = APIRouter(prefix="/api", tags=["workspace"])

class ClientIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    notes: str | None = None

class ConsentIn(BaseModel):
    channel: str = Field(min_length=2, max_length=30)
    purpose: str = Field(default="marketing", min_length=2, max_length=40)
    granted: bool
    evidence_reference: str | None = Field(default=None, max_length=500)

class VehicleIn(BaseModel):
    client_id: int
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    plate_number: str | None = None
    mileage_km: int | None = Field(default=None, ge=0)

class VisitIn(BaseModel):
    client_id: int
    vehicle_id: int | None = None
    service_name: str = Field(min_length=2, max_length=160)
    next_due_at: datetime | None = None
    amount_rub: int | None = Field(default=None, ge=0)
    notes: str | None = None

def owned_client(db: Session, user: User, client_id: int) -> Client:
    client = db.scalar(select(Client).where(Client.id == client_id, Client.organization_id == user.organization_id))
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    org = user.organization_id
    total = db.scalar(select(func.count(Client.id)).where(Client.organization_id == org)) or 0
    visits = db.scalar(select(func.count(ServiceVisit.id)).where(ServiceVisit.organization_id == org)) or 0
    due = db.scalar(select(func.count(ServiceVisit.id)).where(ServiceVisit.organization_id == org, ServiceVisit.next_due_at <= datetime.now(timezone.utc))) or 0
    revenue = db.scalar(select(func.coalesce(func.sum(ServiceVisit.amount_minor), 0)).where(ServiceVisit.organization_id == org)) or 0
    return {"clients": total, "visits": visits, "due": due, "revenue_rub": round(revenue / 100)}

@router.get("/clients")
def list_clients(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    clients = db.scalars(select(Client).where(Client.organization_id == user.organization_id).order_by(Client.created_at.desc())).all()
    return [{"id": c.id, "full_name": c.full_name, "phone": c.phone, "email": c.email, "notes": c.notes,
             "vehicles": [{"id": v.id, "make": v.make, "model": v.model, "year": v.year} for v in c.vehicles]} for c in clients]

@router.post("/clients", status_code=201)
def create_client(payload: ClientIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    client = Client(organization_id=user.organization_id, **payload.model_dump())
    db.add(client); db.commit(); db.refresh(client)
    return {"id": client.id, "full_name": client.full_name}

@router.post("/clients/{client_id}/consents", status_code=201)
def record_consent(client_id: int, payload: ConsentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    client = owned_client(db, user, client_id)
    if payload.purpose != "marketing":
        raise HTTPException(status_code=400, detail="Поддерживается только отдельная фиксация согласия на маркетинговые сообщения")
    record = ConsentRecord(organization_id=user.organization_id, client_id=client.id, **payload.model_dump())
    db.add(record); db.commit(); db.refresh(record)
    return {"id": record.id, "granted": record.granted, "purpose": record.purpose}

@router.post("/vehicles", status_code=201)
def create_vehicle(payload: VehicleIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_client(db, user, payload.client_id)
    data = payload.model_dump()
    vehicle = Vehicle(organization_id=user.organization_id, **data)
    db.add(vehicle); db.commit(); db.refresh(vehicle)
    return {"id": vehicle.id, "make": vehicle.make, "model": vehicle.model}

@router.get("/visits")
def list_visits(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(select(ServiceVisit, Client.full_name).join(Client, Client.id == ServiceVisit.client_id)
        .where(ServiceVisit.organization_id == user.organization_id).order_by(ServiceVisit.visited_at.desc()).limit(100)).all()
    return [{"id": v.id, "client": name, "service_name": v.service_name, "visited_at": v.visited_at.isoformat(),
             "next_due_at": v.next_due_at.isoformat() if v.next_due_at else None, "amount_rub": round(v.amount_minor / 100) if v.amount_minor else 0} for v,name in rows]

@router.post("/visits", status_code=201)
def create_visit(payload: VisitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_client(db, user, payload.client_id)
    if payload.vehicle_id:
        vehicle = db.scalar(select(Vehicle).where(Vehicle.id == payload.vehicle_id, Vehicle.organization_id == user.organization_id, Vehicle.client_id == payload.client_id))
        if not vehicle:
            raise HTTPException(status_code=404, detail="Автомобиль не найден у этого клиента")
    data = payload.model_dump()
    amount = data.pop("amount_rub")
    visit = ServiceVisit(organization_id=user.organization_id, amount_minor=amount * 100 if amount is not None else None, **data)
    db.add(visit); db.commit(); db.refresh(visit)
    return {"id": visit.id, "status": "created"}

@router.get("/smart-return")
def smart_return(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    org = user.organization_id
    now = datetime.now(timezone.utc)
    rows = db.execute(select(ServiceVisit, Client).join(Client, Client.id == ServiceVisit.client_id)
        .where(ServiceVisit.organization_id == user.organization_id, Client.is_blocked.is_(False),
               ServiceVisit.next_due_at.is_not(None), ServiceVisit.next_due_at <= now)
        .order_by(ServiceVisit.next_due_at.asc()).limit(100)).all()
    result = []
    seen = set()
    for visit, client in rows:
        if client.id in seen: continue
        seen.add(client.id)
        consent = db.scalar(select(ConsentRecord).where(
            ConsentRecord.organization_id == org, ConsentRecord.client_id == client.id,
            ConsentRecord.purpose == "marketing", ConsentRecord.granted.is_(True),
            ConsentRecord.revoked_at.is_(None)
        ).order_by(ConsentRecord.captured_at.desc()))
        draft = None
        if consent:
            draft = f"Здравствуйте, {client.full_name}! Напоминаем, что для вашего автомобиля актуально обслуживание: {visit.service_name}. Будем рады подобрать удобное время для визита."
        result.append({"client_id": client.id, "client": client.full_name, "phone": client.phone,
            "service": visit.service_name, "due_at": visit.next_due_at.isoformat(),
            "has_marketing_consent": bool(consent), "draft": draft})
    return result
