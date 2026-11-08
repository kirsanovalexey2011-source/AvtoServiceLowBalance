from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.health import router as health_router
from app.api.auth import limiter, router as auth_router
from app.api.crm import router as crm_router
from app.api.marketplace import router as marketplace_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Client, ConsentRecord, DeferredService, Organization, Reminder, ReminderRule, ServiceVisit, User, Vehicle
from app.web import router as web_router
from app.marketplace_web import router as marketplace_web_router

@asynccontextmanager
async def lifespan(application: FastAPI):
    # Local convenience only. Production schema changes must run through Alembic.
    if settings.app_env != "production":
        Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="AutoFlow — customer retention workspace for automotive businesses.",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
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
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(health_router, tags=["health"])
app.include_router(auth_router)
app.include_router(crm_router)
app.include_router(marketplace_router)
app.include_router(web_router)
app.include_router(marketplace_web_router)

@app.get("/api")
def api_info() -> dict[str, str]:
    return {"name": settings.app_name, "status": "mvp"}
