"""SilentSOS Backend — Level 1 foundation -> Level 2 API integration.

Run: uvicorn main:app --reload --port 8000
Health: GET /health, GET /api/health
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.api.api import api_router
from app.db.session import Base, engine
from app.models import User, Location, Camera, Incident, DetectionEvent, Alert
from app.core.audio_service import start_audio_service

app = FastAPI(title="SilentSOS API", version="0.2.0-level2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    start_audio_service()

# Initialize DB tables explicitly for dev (in prod we use alembic/migrations)
try:
    Base.metadata.create_all(bind=engine)
except OperationalError:
    print("WARNING: Cannot connect to PostgreSQL. Assuming offline mode or tests.")

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"service": "SilentSOS API", "level": 2, "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}

@app.get("/api/health")
def api_health():
    # Verify DB — reuse the shared engine (no per-request pool leak)
    db_status = "untested"
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            db_status = "connected"
    except OperationalError:
        db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok", 
        "api": "v2-db-foundation", 
        "db": db_status
    }
