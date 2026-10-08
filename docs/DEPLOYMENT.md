# Deployment Guide (Level 9)

## Local development

```powershell
python -m venv backend\venv
backend\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install -r ai\requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

Local mode defaults to SQLite. Auth is **always enforced** — the dashboard
requires a login out of the box, so set `SEED_ADMIN_EMAIL` and
`SEED_ADMIN_PASSWORD` before the first startup to get an account, then remove
them (the server warns on every boot while they remain). `AUTH_REQUIRED` is
retained for old `.env` files but no longer disables anything (fail-closed).

## Production profile

1. Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Set environment values (do not commit them):

```
DATABASE_URL=postgresql://silentsos:<secret>@postgres:5432/silentsos
JWT_SECRET=<generated-token>
JWT_EXPIRE_MINUTES=120
ALLOW_PUBLIC_REGISTRATION=false
SEED_ADMIN_EMAIL=<operator-admin-email>
SEED_ADMIN_PASSWORD=<strong-password>
CORS_ORIGINS=https://<your-dashboard-host>
SESSION_COOKIE_SECURE=true
TRUST_PROXY=true
RETENTION_DAYS=30
SNAPSHOT_DIR=./snapshots
AUDIO_KEYWORDS=help,emergency,please help,someone help
STREAM_MAX_THREADS=4
STREAM_SOURCE_ALLOWLIST=rtsp://cam1,http://192.168.1.
MONITOR_THRESHOLD=40
ALERT_THRESHOLD=70
OBSERVATION_DURATION_SEC=10
INACTIVITY_THRESHOLD=0.02
AUDIO_WINDOW_SEC=10
```

Schema is owned by Alembic in production — run `alembic upgrade head` from
`backend/` against the production database before starting the API. The
dev SQLite file predates version stamping, so `main.py` also calls
`create_all` at startup (a no-op when the tables already exist).

A blank or placeholder `JWT_SECRET` is replaced with a random per-process key and
logs a warning: tokens then stop working on restart, and no other install can
replay them. Set a real secret for anything that must persist.

3. Remove `SEED_ADMIN_*` after the first successful startup.
4. Put the API behind TLS and a reverse proxy; do not expose PostgreSQL.
5. Keep the microphone in the same network namespace as the backend — the audio
   pipeline is local-only.

## Docker

```powershell
docker compose up --build
```

The compose file reads secrets from the environment (`.env`), keeps PostgreSQL
on the internal network, and adds healthchecks/restart policies. The backend
image installs both `backend/requirements.txt` and `ai/requirements.txt` and
copies the `ai/` tree so the vision/audio import paths resolve.

## Camera and microphone access

Containers need explicit device access. On Linux:

```yaml
devices:
  - /dev/video0:/dev/video0
  - /dev/snd:/dev/snd
```

## Health and failure handling

- `GET /health` — liveness plus overall component state.
- `GET /api/health` — database check plus per-component detail.
- `GET /api/system/status` — dashboard poll endpoint.
- System events are pushed over `/api/ws/alerts` as
  `{"type": "system", "component": "...", "status": "degraded|down", ...}`.

## Performance

Instrumentation lives in the vision loop (`latency`, `fps`) and the dashboard
header. Run the app against a recorded clip with `ai/vision/run_pipeline.py`
to record FPS/latency before changing `IMGSZ`, `DETECT_STRIDE`, or
`STREAM_WIDTH`.