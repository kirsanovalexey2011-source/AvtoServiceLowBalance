from fastapi import FastAPI
from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0", description="Customer retention for automotive businesses.")
app.include_router(health_router, tags=["health"])

@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "scaffold"}
