"""SilentSOS Backend — Levels 1-9.

Run: uvicorn main:app --reload --port 8000
Health: GET /health, GET /api/health, GET /api/system/status
"""
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.health import health
from app.api.api import api_router
from app.db.session import Base, engine, SessionLocal
from app.models import User, Location, Camera, Incident, DetectionEvent, Alert, RoleEnum
from app.api.deps import require_auth
from app.core.security import get_password_hash
from app.core.audio_service import start_audio_service
from app.core.retention import purge_expired, start_retention_loop

app = FastAPI(title="SilentSOS API", version="0.9.0-level9")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
    max_age=3600,
)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Startup
    # NOTE: there is exactly one vision inference owner — the MJPEG singleton
    # in api/endpoints/stream.py, which starts a per-source thread on first
    # viewer. (An older vision_service.py ran a second, broken copy of the
    # same pipeline at boot with a hardcoded camera URL; it was removed.)

    # Initialize DB tables explicitly for dev
    try:
        # Alembic owns schema in production; create_all covers the dev
        # SQLite file that predates version stamping. It is a no-op when the
        # tables already exist.
        Base.metadata.create_all(bind=engine)

        # Seed an admin only when credentials are supplied through the env.
        # No default password ships with the repo (Level 9 security).
        # WARNING: SEED_ADMIN_* must be removed after first startup — while
        # set, anyone who can read the env can sign in as admin. The warning
        # below fires on every boot until you clear them.
        if settings.SEED_ADMIN_EMAIL and settings.SEED_ADMIN_PASSWORD:
            import warnings as _warnings
            _warnings.warn(
                "SEED_ADMIN_EMAIL is still set — remove SEED_ADMIN_* from .env "
                "now that the admin exists. Anyone who can read the environment "
                "can sign in as admin while it remains.",
                RuntimeWarning,
                stacklevel=1,
            )
            _harden_env_file()
            db = SessionLocal()
            try:
                admin = db.query(User).filter(User.email == settings.SEED_ADMIN_EMAIL).first()
                if not admin:
                    db.add(User(
                        email=settings.SEED_ADMIN_EMAIL,
                        name="System Admin",
                        password_hash=get_password_hash(settings.SEED_ADMIN_PASSWORD),
                        role=RoleEnum.ADMIN,
                    ))
                    db.commit()
                    print(f"Seeded admin {settings.SEED_ADMIN_EMAIL}")
            finally:
                db.close()

        # Run initial retention purge; start periodic background sweep
        try:
            purge_expired()
            start_retention_loop(interval_hours=24)
        except Exception as exc:  # noqa: BLE001 - retention must not block startup
            print(f"WARNING: retention purge failed: {exc}")
    except OperationalError as exc:
        print(f"WARNING: Cannot connect to database: {exc}")
    yield
    # Shutdown: nothing to join — audio/vision threads are daemons.


app.router.lifespan_context = _lifespan

app.include_router(api_router, prefix="/api")

def _harden_env_file() -> None:
    """Restrict .env to owner-only on POSIX so DB/JWT secrets are not
    world-readable. Best-effort: Windows ACLs need icacls, handled by docs."""
    import os
    for candidate in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        try:
            if os.path.isfile(candidate):
                os.chmod(candidate, 0o600)
        except OSError:
            pass

@app.get("/")
def read_root():
    return {"service": "SilentSOS API", "level": 9, "status": "running"}

@app.get("/health")
def health_check():
    # Public liveness only: orchestrators need "is it up", not the component
    # inventory. Anything detailed requires auth (/api/system/status).
    return {"status": "ok", "service": "backend"}

@app.get("/api/health")
def api_health(user: User = Depends(require_auth)):
    # Verify DB — reuse the shared engine (no per-request pool leak)
    db_status = "untested"
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
            db_status = "connected"
    except OperationalError:
        db_status = "disconnected"
    except Exception as e:
        db_status = "error"
        health.set("database", "down", type(e).__name__)

    if db_status == "connected":
        health.set("database", "ok", "connected")
    elif db_status == "disconnected":
        health.set("database", "down", "disconnected")

    return {
        "status": "ok",
        "api": "v9-hardening",
        "db": db_status,
        "components": health.snapshot(),
    }

@app.get("/api/system/status")
def system_status(user: User = Depends(require_auth)):
    return {"overall": health.overall(), "components": health.snapshot()}