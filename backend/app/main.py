from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, admin, devices, scans
from app.core.config import settings
from app import models  # noqa: F401 - ensure model metadata is registered

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    # Schema changes are managed by Alembic. No implicit create_all in runtime.
    yield

app = FastAPI(title=settings.app_name, version="0.2.0", description="Rice Age departmental IoT quality portal API (P1/P2 foundation and P3 dashboard read APIs)", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(scans.router, prefix="/api/v1")

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": settings.app_name, "scope": "P1/P2/P3"}
