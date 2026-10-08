# Privacy Controls

SilentSOS is an AI-assisted alerting system. It reports **possible emergencies**
for human verification; it is not a medical or autonomous response system.

## Processing posture

- Vision (YOLO pose + tracking + fall/inactivity) and audio (VAD, keyword,
  distress classifier) run locally. No cloud AI API is called.
- Raw audio and raw video are **not** persisted by the backend. The live
  `/api/stream/video` endpoint returns annotated MJPEG frames in memory only.
- Incidents store structured evidence (event type, confidence, signal values),
  not raw media. `snapshot_path` exists but no backend path writes snapshots.

## Data lifecycle

- `RETENTION_DAYS` (default 30) controls how long resolved incidents are kept.
  `purge_expired()` removes VERIFIED/DISMISSED incidents, their detection
  events, and their alert rows at startup. Open incidents are never auto-deleted.
- Operators can erase a single incident and its history via
  `DELETE /api/incidents/{id}`. OPEN incidents are protected — erasing live
  response state needs `?force=true`. Snapshot files on disk are removed
  alongside the DB rows.
- Set `RETENTION_DAYS=0` to disable automatic purge.

## Access control

- Authentication is always enforced: every endpoint (except `/`, `/health`
  and the auth routes) and the WebSocket require a valid JWT or session, and
  incident deletion additionally requires the ADMIN role. Put a reverse proxy
  or gateway in front of the API for a second layer.
- No default admin credential ships in the repo. Seed an admin explicitly with
  `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD`, then remove those values (the
  server warns on every boot while they remain).
- Session tokens live in memory + an httpOnly cookie — never in
  `localStorage`. Camera URLs (which may contain credentials) are still stored
  in browser `localStorage` for convenience: prefer camera sources that do
  not embed credentials, and treat operator workstations as sensitive.
- Incident snapshot files live under `SNAPSHOT_DIR` and are deleted together
  with their incident rows by the retention purge.

## Camera placement and consent

- Place cameras to cover the monitored area only; avoid private spaces such as
  bathrooms, changing areas, and sleeping quarters.
- Post visible notice that AI-assisted monitoring is active and obtain consent
  where required by local policy or law.
- Prefer on-premises storage and restrict database/API reachability to the
  operator network.

## What is not stored

- No raw audio recordings, no raw video recordings, no face templates, and no
  continuous location history beyond incident camera association.