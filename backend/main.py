"""SilentSOS Backend — Level 1 foundation -> Level 2 API integration.

Run: uvicorn main:app --reload --port 8000
Health: GET /health, GET /api/health
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.api.api import api_router
from app.db.session import Base, engine
from app.models import User, Location, Camera, Incident, DetectionEvent, Alert

app = FastAPI(title="SilentSOS API", version="0.2.0-level2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Relaxed for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    # Verify DB
    db_status = "untested"
    try:
        engine_test = create_engine(settings.DATABASE_URL)
        with engine_test.connect() as conn:
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
