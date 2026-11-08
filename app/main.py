from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.crm import router as crm_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Client, ConsentRecord, Organization, Reminder, ReminderRule, ServiceVisit, User, Vehicle
from app.web import router as web_router

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="AutoFlow — customer retention workspace for automotive businesses.",
)
app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(crm_router)
app.include_router(web_router)

@app.on_event("startup")
def initialize_local_database() -> None:
    # Lightweight local MVP bootstrap. Use Alembic migrations before production deployment.
    if settings.app_env != "production":
        Base.metadata.create_all(bind=engine)

@app.get("/api")
def api_info() -> dict[str, str]:
    return {"name": settings.app_name, "status": "mvp"}
