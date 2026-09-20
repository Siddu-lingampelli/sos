# SilentSOS — Intelligent Emergency Detection System

> AI-assisted, multimodal emergency detection: Camera + Microphone → AI Detection → Temporal Verification → Emergency Confidence Engine → FastAPI → PostgreSQL + WebSocket → React Dashboard → Human Verification

SilentSOS passively monitors a hostel/campus environment for possible falls, prolonged inactivity, and distress audio (keywords + scream), verifies over an observation window, calculates an emergency confidence score, and alerts a human security operator. It reports **"Possible emergency — human verification required"**, never a definitive diagnosis.

See `SOS_Documentation.md` (spec) and `SOS_PLAN.md` (10-level build plan).

## Status — Levels 1–5 complete

- `backend/` — FastAPI + JWT auth + cameras/locations/incidents APIs + live MJPEG `/api/stream/video`
- `frontend/` — React + TypeScript + Tailwind dashboard with laptop / mobile / manual-IP camera picker
- `ai/vision/` — OpenCV + YOLO11n-pose + ByteTrack IDs + fall state machine + inactivity observation window
- `ai/audio, ai/engine/` — placeholders for Level 6 (audio) and Level 7 (confidence engine)
- `database/` — Postgres dev init (`init.sql`); full schema via SQLAlchemy models + Alembic env
- `docker-compose.yml` — postgres + backend + frontend
- `.env.example` — DATABASE_URL, JWT_SECRET, BACKEND_URL, FRONTEND_URL, MODEL_PATHS, ALERT_SETTINGS

## Quickstart (local, no Docker)

Backend:
```powershell
python -m venv backend\venv
backend\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
uvicorn main:app --reload --port 8000
# → http://localhost:8000/health (run from inside backend/ — main.py uses app.* imports)
```

Frontend:
```powershell
Set-Location frontend
npm install
npm run dev
# → http://localhost:5173
```

Docker:
```powershell
docker compose up --build
# backend http://localhost:8000, frontend http://localhost:5173, postgres localhost:5432
```

## Docs

- `SOS_Documentation.md` — sections 1-43, architecture, confidence engine, stack rationale
- `SOS_PLAN.md` — Levels 1-10 + Definition of Done
- `docs/` — (Level 10) ARCHITECTURE, API, DATABASE, SETUP, TESTING, LIMITATIONS
