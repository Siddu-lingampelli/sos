"""SilentSOS Backend — Level 1 foundation.

Run: uvicorn backend.main:app --reload --port 8000
Health: GET /health, GET /api/health
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {"status": "ok", "api": "v1-foundation", "db": "not-configured-yet-level2"}
