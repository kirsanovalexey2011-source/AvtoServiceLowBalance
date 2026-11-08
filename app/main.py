from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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
    version="0.3.0",
    description="AutoFlow — customer retention workspace for automotive businesses.",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)

@app.middleware("http")
async def same_origin_for_unsafe_requests(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlsplit
            origin_host = urlsplit(origin).netloc.lower()
            request_host = request.headers.get("host", "").lower()
            if not origin_host or origin_host != request_host:
                return JSONResponse(status_code=403, content={"detail": "Cross-origin request rejected"})
    return await call_next(request)

app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(crm_router)
app.include_router(web_router)

@app.on_event("startup")
def initialize_local_database() -> None:
    # Local convenience only. Production schema changes must run through Alembic.
    if settings.app_env != "production":
        Base.metadata.create_all(bind=engine)

@app.get("/api")
def api_info() -> dict[str, str]:
    return {"name": settings.app_name, "status": "mvp"}
