"""SilentSOS Backend — Level 1 foundation.

Run: uvicorn backend.main:app --reload --port 8000
Health: GET /health, GET /api/health
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from .app.core.config import settings

app = FastAPI(title="SilentSOS API", version="0.1.0-level1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"service": "SilentSOS API", "level": 1, "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}


@app.get("/api/health")
def api_health():
    # Level 1 Deliverable: "PostgreSQL connects."
    db_status = "untested"
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            db_status = "connected"
    except OperationalError:
        db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    return {
        "status": "ok", 
        "api": "v1-foundation", 
        "db": db_status
    }
